# CeleSun -  ΦLO-TIME

Get it running
---

`sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0`

If you get a path error you need to specify your PyQt5 install path `export QT_QPA_PLATFORM_PLUGIN_PATH=/path/to/qt` 

Create venv inside the cloned git `python -m venv venv`.

Activate your venv `source venv/bin/activate`

Install requirements: `pip install -r requirements`

Then `python3 celesun.py` 

----
CeleSun is a 24h clock based on a simple compass (an idea of my dad actually). 

We break it down into 15° equal parts (Also 22.5 to be fancy) and work from there.

---
![image](https://github.com/user-attachments/assets/b757cdfc-4c70-45fa-a0b6-55a876528ede)

Uses latitude, longitude and timezone to create GUI. (Defaults to Europe/Paris)

---
![image](https://github.com/user-attachments/assets/4503be89-a3cc-49b1-970a-52c19f5955a0)

New Settings!

### You can then visit tokyo while they are sleeping 😴

35.5, 139.5

---
![image](https://github.com/user-attachments/assets/4f36317f-d66c-4f7b-8559-e47be52fe1c8)

### Or Buenos Aires where you can see it's just past peak noon 🔆 

-34.3, -58.1

---
![image](https://github.com/user-attachments/assets/c272505e-f03f-4879-9267-b248116a9068)

### Darkmode & Color config:

![image](https://github.com/user-attachments/assets/74314214-fc6d-4f27-9a8f-ec4d061e8a08)


