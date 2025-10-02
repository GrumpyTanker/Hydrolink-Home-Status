# ⚠️ This AppDaemon Plugin is Deprecated ⚠️

**This project is no longer actively maintained. Please use the new and improved HACS integration instead.**

The new integration offers better performance, easier configuration through the Home Assistant UI, and more robust features.

➡️ **[Go to the new Ecowater-Hydrolink-HACS repository](https://github.com/GrumpyTanker/Ecowater-Hydrolink-HACS)**

---

# HydroLinkStatus AppDaemon Plugin

A simple AppDaemon 4 script to integrate your EcoWater HydroLink water softener with Home Assistant.

---

## 📂 Repository Contents

- **hydrolink.py** – Main AppDaemon Python app  
- **apps.yaml** – Example AppDaemon apps-enabled configuration  
- **README.md** – This documentation  

---

## 🖥️ Requirements

- Home Assistant OS 15.2+ with AppDaemon 4 add-on (v4.5.8+)  
  - MUST add "websocket-client" to AppDaemon Configuration's "Python Packages"
- Python 3.12 (bundled with the AppDaemon add-on)  
- Internet access from the Home Assistant host to `api.hydrolinkhome.com`  

---

## 🚀 Installation

1. **Clone or download** this repo into your Home Assistant `config/apps/` folder:

   ```bash
   cd /config/apps
   git clone https://github.com/YourUser/YourRepo.git hydrolink_app
   
1. Ensure "websocket-client" is an available python package in AppDaemon Add-On Configuration.
   - Settings -> Add-Ons -> AppDaemon -> Configuration

1. Update your AppDaemon apps.yaml to include the sample apps.yaml from this repo, and ensure you update email and password.
