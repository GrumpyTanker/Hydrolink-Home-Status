# HydroLinkStatus AppDaemon Plugin

A simple AppDaemon 4 script to integrate your EcoWater HydroLink water softener with Home Assistant.

---

## 📂 Repository Contents

- **hydrolink.py** – Main AppDaemon Python app  
- **appdaemon.yaml** – Example AppDaemon apps-enabled configuration  
- **README.md** – This documentation  

---

## 🖥️ Requirements

- Home Assistant OS 15.2+ with AppDaemon 4 add-on (v4.5.8+)  
- Python 3.12 (bundled with the AppDaemon add-on)  
- Internet access from the Home Assistant host to `api.hydrolinkhome.com`  

---

## 🚀 Installation

1. **Clone or download** this repo into your Home Assistant `config/apps/` folder:

   ```bash
   cd /config/apps
   git clone https://github.com/YourUser/YourRepo.git hydrolink_app
