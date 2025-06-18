import requests
import datetime
import appdaemon.plugins.hass.hassapi as hass

class HydroLinkStatus(hass.Hass):

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

        # schedule polling (start 5 sec after init)
        start = self.datetime() + datetime.timedelta(seconds=5)
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
            self.log(f"Login request failed: {e}")
        return False

    def poll(self, kwargs):
        # ensure we have a valid cookie
        if not self.auth_cookie:
            if not self.login():
                self.log("Login failed, will retry on next poll")
                return

        # fetch device list
        try:
            r = requests.get(
                "https://api.hydrolinkhome.com/v1/devices?all=false&per_page=200",
                cookies={"hhfoffoezyzzoeibwv": self.auth_cookie},
                timeout=10
            )
            r.raise_for_status()
        except requests.RequestException as e:
            self.log(f"HTTP request failed: {e}")
            self.auth_cookie = None  # force re-login next time
            return

        devices = r.json().get("data", [])
        for dev in devices:
            props = dev.get("properties") or {}
            if not isinstance(props, dict):
                self.error(f"`properties` is not dict! Got: {repr(props)}")
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
