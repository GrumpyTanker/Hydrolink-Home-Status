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

        self.unit_map = {
            "avg_daily_use_gals": "gallons",
            "avg_salt_per_regen_lbs": "lbs",
            "capacity_remaining_percent": "%",
            "current_water_flow_gpm": "gpm",
            "daily_avg_rock_removed_lbs": "lbs",
            "gallons_used_today": "gallons",
            "peak_water_flow_gpm": "gpm",
            # Add more units as needed
        }

        self.run_every(self.poll, self.datetime() + datetime.timedelta(seconds=5), self.args.get("poll_interval", 300))

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
        if not self.auth_cookie:
            if not self.login():
                self.log("Login failed, will retry on next poll")
                return

        try:
            r = requests.get(
                "https://api.hydrolinkhome.com/v1/devices?all=false&per_page=200",
                cookies={"hhfoffoezyzzoeibwv": self.auth_cookie},
                timeout=10
            )
            r.raise_for_status()
        except requests.RequestException as e:
            self.log(f"HTTP request failed: {e}")
            self.auth_cookie = None  # force re-login next poll
            return

        data = r.json().get("data", [])
        for dev in data:
            props = dev.get("properties") or {}
            if not isinstance(props, dict):
                self.error(f"`properties` is not dict! Got: {repr(props)}")
                continue

            prop_map = {
                name: info["value"]
                for name, info in props.items()
                if isinstance(info, dict) and "value" in info and name in self.whitelist
            }

            for key, val in prop_map.items():
                # Adjust 'capacity_remaining_percent' for tenths
                if key == "capacity_remaining_percent" and isinstance(val, (int, float)):
                    val = val / 10

                entity_id = f"sensor.hydrolink_{key}"
                friendly = self.friendly_name(key)
                attributes = {"friendly_name": f"{self.device_name} {friendly}"}
                if key in self.unit_map:
                    attributes["unit_of_measurement"] = self.unit_map[key]

                self.set_state(
                    entity_id,
                    state=val,
                    attributes=attributes,
                )

    def friendly_name(self, key):
        return key.replace("_", " ").title()
