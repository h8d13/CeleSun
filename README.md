# CeleSun -  ΦLO-TIME

CeleSun is a 24h clock based on a simple compass (an idea of my dad actually).

We break it down into 15° equal parts (Also 22.5 to be fancy) and work from there.

Built with GTK4 and libadwaita for a modern, native Linux experience. 

> Clocks are kinda stupid by design, using some neat Python libs we can maybe make a good one? 

---

Uses latitude, longitude and timezone to create GUI. (Defaults to Europe/Paris)

<img width="608" height="615" alt="Screenshot_20251119_142049" src="https://github.com/user-attachments/assets/8cc8e6e2-d53a-4457-a27e-6467cadaa2e2" />


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

35.5, 139.5 ; Asia/Tokyo

### Or Buenos Aires where you can see it's just past peak noon 🔆 

-34.3, -58.1 ; America/Argentina/Buenos_Aires

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
