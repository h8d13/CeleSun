# CeleSun -  ΦLO-TIME

CeleSun is a 24h clock based on a simple compass (an idea of my dad actually).

We break it down into 15° equal parts (Also 22.5 to be fancy) and work from there.

Built with GTK4 and libadwaita for a modern, native Linux experience.

---
![image](https://github.com/user-attachments/assets/b757cdfc-4c70-45fa-a0b6-55a876528ede)

Uses latitude, longitude and timezone to create GUI. (Defaults to Europe/Paris)

---
![image](https://github.com/user-attachments/assets/4503be89-a3cc-49b1-970a-52c19f5955a0)

## Features

- **24-hour clock display** with compass-style visualization
- **Solar tracking**: Shows sunrise, sunset, solar noon, and daylight arc
- **Customizable location**: Set any latitude/longitude/timezone
- **Dark mode support** with proper libadwaita integration
- **Color themes**: Choose different gradient colors for daylight visualization
- **Clock offset**: Rotate the compass to your preference
- **Responsive design**: Dynamically scales to any window size (minimum 300x350)
- **Customizable font**: Choose your preferred font family
- **Config persistence**: All settings and window size automatically saved

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

---

## Installation

### Arch Linux

```bash
# Install system dependencies
sudo pacman -S gtk4 libadwaita python-gobject python-cairo

# Create virtual environment with system packages
python3 -m venv venv --system-site-packages

# Install Python dependencies
./venv/bin/pip install suntime pytz

# Run the application
./venv/bin/python celesun_gtk.py
```

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-venv

# Create virtual environment with system packages
python3 -m venv venv --system-site-packages

# Install Python dependencies
./venv/bin/pip install suntime pytz

# Run the application
./venv/bin/python celesun_gtk.py
```

### Fedora

```bash
# Install system dependencies
sudo dnf install gtk4 libadwaita python3-gobject python3-cairo

# Create virtual environment with system packages
python3 -m venv venv --system-site-packages

# Install Python dependencies
./venv/bin/pip install suntime pytz

# Run the application
./venv/bin/python celesun_gtk.py
```

---

## Configuration

Settings are automatically saved to `~/.config/celesun/config.json` and include:
- Location (latitude, longitude, timezone)
- Appearance (dark mode, gradient color, clock offset, font family)
- Window size (minimum 300x350, scales dynamically)

---
