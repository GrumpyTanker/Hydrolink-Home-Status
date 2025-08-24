import requests
import datetime
import appdaemon.plugins.hass.hassapi as hass
import websocket
import threading
import time



class HydroLinkStatus(hass.Hass):

    #this is used to track how many web socket messages we have received so we can close after a certain amount.
    ws_message_count = 0

    #this is used to track if we are waiting for the WebSocket thread to exit.
    waiting_for_ws_thread_to_end = 1

    #the websocket uri
    ws_uri = ""

    #used to enable debug messages
    debug = 0

    # Allows switching between different type of debugging.
    def log_debug(self, msg):
#You could use something like this as well:        self.log(msg, level="DEBUG")
        if self.debug:
            self.log(f"DEBUG: {msg}")

    # This is a thread function that opens a websocket to refresh the data
    def start_ws(self):
        def on_message(ws, message):
            #self.log_debug(f"WebSocket on_message: Received- Count: {self.ws_message_count}, Msg: {message}:")
            self.ws_message_count += 1
            # This is what the web app is doing... it seems to get 17 messages, and then closes connection.
            if self.ws_message_count >= 17:  # magic number!!!  Not sure why, this is what web app does.
                ws.close()

        def on_open(ws):
            self.log_debug("WebSocket: on_open")

        def on_close(ws, close_status_code, close_msg):
            self.log_debug(f"WebSocket: on_close: got {self.ws_message_count} messages")

        def on_error(ws, error):
            self.log_debug(f"WebSocket: on_error: {error}")

        self.log_debug(f"WebSocket: Opening a web socket at uri: {self.ws_uri}...")
        self.ws_message_count = 0
        ws = websocket.WebSocketApp(
            self.ws_uri,
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            on_error=on_error
        )
        # Note, on_message() above will auto-close the connection after a certain number of messages are received.
        ws.run_forever()
        self.waiting_for_ws_thread_to_end = 0


    def initialize(self):
        self.email = self.args["email"]
        self.password = self.args["password"]
        self.whitelist = set(self.args.get("whitelist", []))
        self.device_name = self.args.get("device_name", "HydroLink Water Softener")
        self.auth_cookie = None

        # Map some known keys to units
        self.unit_map = {
            "avg_daily_use_gals": "gallons",
            "avg_salt_per_regen_lbs": "lbs",
            "capacity_remaining_percent": "%",
            "current_water_flow_gpm": "gpm",
            "daily_avg_rock_removed_lbs": "lbs",
            "gallons_used_today": "gallons",
            "peak_water_flow_gpm": "gpm",
        }

        # schedule polling
        seconds_until_first_poll=5
        self.log_debug(f"Initialization starting in {seconds_until_first_poll} seconds...")
        start = self.datetime() + datetime.timedelta(seconds=seconds_until_first_poll)
        interval = self.args.get("poll_interval", 300)
        self.run_every(self.poll, start, interval)

    def login(self):
        try:
            r = requests.post(
                "https://api.hydrolinkhome.com/v1/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=10
            )
            if r.status_code == 200:
                self.auth_cookie = r.cookies.get("hhfoffoezyzzoeibwv")
                self.log("Login successful, cookie stored")
                return True
            else:
                self.log(f"Login failed: {r.status_code}")
        except requests.RequestException as e:
            self.log(f"Login request failed: {e}.  Tried login: {self.email}")
        return False

    def poll(self, kwargs):
        self.log_debug(f"---------starting poll---------------")
        # ensure we have a valid cookie
        if not self.auth_cookie:
            if not self.login():
                self.log("Login failed, will retry on next poll")
                return

        try:
            # Note, this gets the list of devices, and returns data, but note that the data is stale and shouldn't be used (except for the list of devices, and their IDs).
            self.log_debug("Requesting devices...")
            r = requests.get(
                "https://api.hydrolinkhome.com/v1/devices?all=false&per_page=200",
                cookies={"hhfoffoezyzzoeibwv": self.auth_cookie},
                timeout=10
            )
            r.raise_for_status()

            devices = r.json().get("data", [])
            for dev in devices:
                # The following sequence of actions were copied from using the web hydrolink page,
                # and mimicing what is done when a refresh on the page is done.  I think the
                # key is that you have to open a WebSocket connection and get data.
                dev_id = dev.get("id")
                self.log_debug(f"Asking for web link for device: {dev_id}...")
                # This makes a request for a live Web Socket connection.
                r = requests.get(
                    f"https://api.hydrolinkhome.com/v1/devices/{dev_id}/live",
                    cookies={"hhfoffoezyzzoeibwv": self.auth_cookie},
                    timeout=10
                )
                r.raise_for_status()

                # Parse out, and open a WebSocket.
                self.ws_uri = r.json().get("websocket_uri") or {}
                self.ws_uri = f"wss://api.hydrolinkhome.com{self.ws_uri}"
                self.waiting_for_ws_thread_to_end = 1
                num_of_waits = 0
                threading.Thread(target=self.start_ws, daemon=True).start()
                # This loop just makes sure we don't wait forever for the WebSocket to finish.
                while self.waiting_for_ws_thread_to_end:
                    time.sleep(1)
                    num_of_waits = num_of_waits + 1
                    if num_of_waits > 15:
                        self.log(f"!!!!!! Stop waiting for ws thread, took too long.")
                        break

                # Now, when we request data, it should be fresh data.
                self.log_debug(f"Getting the data again - should be fresh data now...")
                r = requests.get(
                    "https://api.hydrolinkhome.com/v1/devices?all=false&per_page=200",
                    cookies={"hhfoffoezyzzoeibwv": self.auth_cookie},
                    timeout=10
                )
                r.raise_for_status()

        except requests.RequestException as e:
            self.log(f"Polling failed: {e}")
            self.auth_cookie = None  # force re-login next time
            return

        self.log_debug(f"Parsing devices...")
        devices = r.json().get("data", [])
        for dev in devices:
            props = dev.get("properties") or {}
            if not isinstance(props, dict):
                self.error(f"`properties` is not in dict! Got: {repr(props)}")
                continue

            # filter & extract only whitelisted keys
            prop_map = {
                name: info["value"]
                for name, info in props.items()
                if isinstance(info, dict) and "value" in info and name in self.whitelist
            }

            for key, val in prop_map.items():
                # apply any special conversions
                if key == "capacity_remaining_percent":
                    # Hydrolink returns tenths of percent (e.g. 777 → 77.7%)
                    val = round(val / 10.0, 1)

                # If the current_time_sec updates, that seems to be a good metric
                # that we got fresh data (without having to run faucets to see if
                # if gallons per minute changing, etc.)
                if key == "current_time_secs":
                    self.log_debug(f"current_time_secs: {val}")

                entity_id = f"sensor.hydrolink_{key}"
                friendly = self.friendly_name(key)
                attributes = {"friendly_name": f"{self.device_name} {friendly}"}
                if key in self.unit_map:
                    attributes["unit_of_measurement"] = self.unit_map[key]

                # update HA state
                self.set_state(entity_id, state=val, attributes=attributes)


    def friendly_name(self, key):
        # snake_case → Title Case
        return key.replace("_", " ").title()
