# HydroLink Water Softener AppDaemon Integration

This AppDaemon app retrieves and publishes HydroLink water softener status sensors into Home Assistant.

---

## Features

- Logs into HydroLink API using your account
- Retrieves device status and properties
- Creates Home Assistant sensors for whitelisted properties
- Automatically refreshes data on a configurable interval

---

## Installation

1. Place `hydrolink.py` into your `apps` directory (e.g., `/config/appdaemon/apps/hydrolink.py`).

2. Add the following to your `apps.yaml` file:

```yaml
hydrolink_status:
  module: hydrolink
  class: HydroLinkStatus
  email: your_email@example.com
  password: your_password
  device_name: "EcoWater Softener"
  whitelist:
    - avg_daily_use_gals
    - capacity_remaining_percent
    - peak_water_flow_gpm
    # Add or remove keys as needed
  poll_interval: 300
```

3. Restart AppDaemon.

---

## Notes

- `capacity_remaining_percent` is divided by 10 in code to correct API scaling.
- Units are set automatically for known keys.
- Adjust `whitelist` to include only sensors you want created.

---

## Credits

This app and documentation were generated and refined with the help of ChatGPT.

---

## License

MIT License
