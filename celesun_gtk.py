#!/usr/bin/env python3
import sys
import math
import datetime
import gi
import json
import os
import signal

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk, GObject, Pango, PangoCairo
import cairo
from suntime import Sun
import pytz
import subprocess


# Font management
def get_available_fonts():
    """Get list of available system fonts using fc-list"""
    try:
        # Use fc-list to get system fonts
        result = subprocess.run(['fc-list', ':', 'family'],
                              capture_output=True, text=True, check=True)

        # Parse output and get unique font families
        fonts = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                # fc-list returns "family" or "family,style"
                family = line.split(',')[0].strip()
                if family:
                    fonts.add(family)

        return sorted(list(fonts))
    except Exception as e:
        print(f"Error getting fonts: {e}")
        # Fallback to common fonts
        return ['Arial', 'Sans', 'Serif', 'Monospace', 'DejaVu Sans', 'Ubuntu', 'Cantarell']


# Config file management
def get_config_path():
    """Get the path to the config file"""
    config_dir = os.path.join(os.path.expanduser('~'), '.config', 'celesun')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')


def load_config():
    """Load config from file, return default values if not found"""
    config_path = get_config_path()
    default_config = {
        'latitude': 48.8575,
        'longitude': 2.3514,
        'timezone': 'Europe/Paris',
        'offset': 0,
        'dark_mode': False,
        'gradient_color': (255, 255, 0),
        'window_width': 400,
        'window_height': 500,
        'font_family': 'Arial'
    }

    if not os.path.exists(config_path):
        return default_config

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Ensure all keys exist
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            # Convert gradient_color from list to tuple if needed
            if isinstance(config['gradient_color'], list):
                config['gradient_color'] = tuple(config['gradient_color'])
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config


def save_config(latitude, longitude, timezone, offset, dark_mode, gradient_color, window_width=400, window_height=500, font_family='Arial'):
    """Save config to file"""
    config_path = get_config_path()
    config = {
        'latitude': latitude,
        'longitude': longitude,
        'timezone': timezone,
        'offset': offset,
        'dark_mode': dark_mode,
        'gradient_color': list(gradient_color) if isinstance(gradient_color, tuple) else gradient_color,
        'window_width': window_width,
        'window_height': window_height,
        'font_family': font_family
    }

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


class SettingsDialog(Gtk.Window):
    def __init__(self, parent, latitude, longitude, timezone, offset, dark_mode, gradient_color, font_family):
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title('Settings')
        self.set_default_size(300, 500)

        self.result = None

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)

        # Latitude
        lat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lat_label = Gtk.Label(label='Latitude:')
        lat_label.set_halign(Gtk.Align.START)
        self.latitude_entry = Gtk.Entry()
        self.latitude_entry.set_text(str(latitude))
        lat_box.append(lat_label)
        lat_box.append(self.latitude_entry)
        main_box.append(lat_box)

        # Longitude
        lon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lon_label = Gtk.Label(label='Longitude:')
        lon_label.set_halign(Gtk.Align.START)
        self.longitude_entry = Gtk.Entry()
        self.longitude_entry.set_text(str(longitude))
        lon_box.append(lon_label)
        lon_box.append(self.longitude_entry)
        main_box.append(lon_box)

        # Timezone
        tz_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        tz_label = Gtk.Label(label='Timezone:')
        tz_label.set_halign(Gtk.Align.START)
        self.timezone_entry = Gtk.Entry()
        self.timezone_entry.set_text(timezone)
        tz_box.append(tz_label)
        tz_box.append(self.timezone_entry)
        main_box.append(tz_box)

        # Offset
        offset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        offset_label = Gtk.Label(label='Clock Offset (degrees):')
        offset_label.set_halign(Gtk.Align.START)
        self.offset_entry = Gtk.Entry()
        self.offset_entry.set_text(str(offset))
        self.offset_entry.set_placeholder_text('0-359')
        offset_box.append(offset_label)
        offset_box.append(self.offset_entry)
        main_box.append(offset_box)

        # Separator
        main_box.append(Gtk.Separator())
        appearance_label = Gtk.Label(label='Appearance:')
        appearance_label.set_halign(Gtk.Align.START)
        main_box.append(appearance_label)

        # Dark mode
        self.dark_mode_check = Gtk.CheckButton(label='Dark Mode')
        self.dark_mode_check.set_active(dark_mode)
        main_box.append(self.dark_mode_check)

        # Gradient color
        gradient_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        gradient_label = Gtk.Label(label='Daylight Gradient:')
        gradient_label.set_halign(Gtk.Align.START)

        # Use StringList for GTK4
        self.gradient_options = ["Yellow (Default)", "Orange", "Blue", "Green", "Pink"]
        self.gradient_colors = [
            (255, 255, 0),
            (255, 165, 0),
            (135, 206, 235),
            (144, 238, 144),
            (255, 182, 193)
        ]

        string_list = Gtk.StringList.new(self.gradient_options)
        self.gradient_combo = Gtk.DropDown.new(string_list, None)

        # Set active based on current color
        try:
            index = self.gradient_colors.index(gradient_color)
            self.gradient_combo.set_selected(index)
        except ValueError:
            self.gradient_combo.set_selected(0)

        gradient_box.append(gradient_label)
        gradient_box.append(self.gradient_combo)
        main_box.append(gradient_box)

        # Font selector
        font_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        font_label = Gtk.Label(label='Font Family:')
        font_label.set_halign(Gtk.Align.START)

        # Get available fonts
        available_fonts = get_available_fonts()

        # Create string list with fonts
        font_string_list = Gtk.StringList.new(available_fonts)
        self.font_combo = Gtk.DropDown.new(font_string_list, None)

        # Enable search in the dropdown
        self.font_combo.set_enable_search(True)

        # Set active font based on current selection
        try:
            font_index = available_fonts.index(font_family)
            self.font_combo.set_selected(font_index)
        except ValueError:
            # Default to Arial or first font if not found
            try:
                font_index = available_fonts.index('Arial')
                self.font_combo.set_selected(font_index)
            except ValueError:
                self.font_combo.set_selected(0)

        font_box.append(font_label)
        font_box.append(self.font_combo)
        main_box.append(font_box)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)

        reset_btn = Gtk.Button(label='Reset')
        reset_btn.connect('clicked', self.on_reset)

        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.connect('clicked', self.on_cancel)

        ok_btn = Gtk.Button(label='OK')
        ok_btn.add_css_class('suggested-action')
        ok_btn.connect('clicked', self.on_ok)

        button_box.append(reset_btn)
        button_box.append(cancel_btn)
        button_box.append(ok_btn)
        main_box.append(button_box)

        self.set_child(main_box)

    def on_reset(self, button):
        self.latitude_entry.set_text("48.8575")
        self.longitude_entry.set_text("2.3514")
        self.timezone_entry.set_text("Europe/Paris")
        self.offset_entry.set_text("0")
        self.dark_mode_check.set_active(False)
        self.gradient_combo.set_selected(0)

        # Reset font to Arial
        available_fonts = get_available_fonts()
        try:
            arial_index = available_fonts.index('Arial')
            self.font_combo.set_selected(arial_index)
        except ValueError:
            self.font_combo.set_selected(0)

    def on_cancel(self, button):
        self.result = None
        self.close()

    def on_ok(self, button):
        try:
            latitude = float(self.latitude_entry.get_text())
            longitude = float(self.longitude_entry.get_text())
            timezone = self.timezone_entry.get_text().strip()
            offset = float(self.offset_entry.get_text() or "0") % 360
            dark_mode = self.dark_mode_check.get_active()

            # Get gradient color based on selected index
            selected_index = self.gradient_combo.get_selected()
            gradient_color = self.gradient_colors[selected_index]

            # Get selected font
            available_fonts = get_available_fonts()
            font_index = self.font_combo.get_selected()
            font_family = available_fonts[font_index] if font_index < len(available_fonts) else 'Arial'

            self.result = (latitude, longitude, timezone, offset, dark_mode, gradient_color, font_family)
            self.close()
        except ValueError as e:
            print(f"Invalid input: {e}")


class CompassWidget(Gtk.DrawingArea):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_draw_func(self.draw_func)

        # Default location (Paris)
        self.latitude = 48.8575
        self.longitude = 2.3514
        self.timezone = "Europe/Paris"
        self.offset = 0

        # Appearance
        self.dark_mode = False
        self.gradient_color = (255, 255, 0)
        self.font_family = 'Arial'

        # Sun data
        self.sun = Sun(self.latitude, self.longitude)
        self.sunrise = None
        self.sunset = None
        self.solar_noon = None
        self.now = None
        self.event = ""
        self.time_left = datetime.timedelta(0)
        self.sun_position = 0
        self.sun_direction = "N"

        # Update timer
        GLib.timeout_add(1000, self.update_data)
        self.update_data()

    def update_data(self):
        try:
            try:
                local_tz = pytz.timezone(self.timezone)
            except pytz.UnknownTimeZoneError:
                local_tz = pytz.utc

            utc_now = datetime.datetime.now(pytz.utc)
            self.now = utc_now.astimezone(local_tz)

            today = self.now.date()
            local_midnight = datetime.datetime.combine(today, datetime.time(0, 0))
            local_midnight = local_tz.localize(local_midnight)
            utc_midnight = local_midnight.astimezone(pytz.utc)

            try:
                sunrise_utc = self.sun.get_sunrise_time(utc_midnight)
                sunset_utc = self.sun.get_sunset_time(utc_midnight)

                self.sunrise = sunrise_utc.astimezone(local_tz)
                self.sunset = sunset_utc.astimezone(local_tz)

                self.sunrise = local_tz.localize(datetime.datetime.combine(today, self.sunrise.time()))
                self.sunset = local_tz.localize(datetime.datetime.combine(today, self.sunset.time()))

                self.solar_noon = local_tz.localize(datetime.datetime.combine(
                    today,
                    datetime.time(
                        (self.sunrise.hour + self.sunset.hour) // 2,
                        (self.sunrise.minute + self.sunset.minute) // 2
                    )
                ))
            except Exception as e:
                print(f"Error calculating sun times: {e}")
                self.sunrise = local_tz.localize(datetime.datetime.combine(today, datetime.time(6, 0)))
                self.sunset = local_tz.localize(datetime.datetime.combine(today, datetime.time(18, 0)))
                self.solar_noon = local_tz.localize(datetime.datetime.combine(today, datetime.time(12, 0)))

            self.calculate_next_event(local_tz)
            self.calculate_sun_position()

            self.queue_draw()
        except Exception as e:
            print(f"Error in update_data: {e}")

        return True

    def calculate_next_event(self, local_tz):
        now = self.now

        if now < self.sunrise:
            self.event = "Sunrise"
            self.time_left = self.sunrise - now
        elif now < self.sunset:
            self.event = "Sunset"
            self.time_left = self.sunset - now
        else:
            tomorrow = now.date() + datetime.timedelta(days=1)
            tomorrow_sunrise = local_tz.localize(datetime.datetime.combine(
                tomorrow,
                self.sunrise.time()
            ))
            self.event = "Sunrise (tomorrow)"
            self.time_left = tomorrow_sunrise - now

    def calculate_sun_position(self):
        current_hour = self.now.hour + self.now.minute / 60 + self.now.second / 3600
        self.sun_position = (current_hour * 15) % 360

        directions = [
            (348.75, 11.25, "N"), (11.25, 33.75, "NNE"), (33.75, 56.25, "NE"),
            (56.25, 78.75, "ENE"), (78.75, 101.25, "E"), (101.25, 123.75, "ESE"),
            (123.75, 146.25, "SE"), (146.25, 168.75, "SSE"), (168.75, 191.25, "S"),
            (191.25, 213.75, "SSW"), (213.75, 236.25, "SW"), (236.25, 258.75, "WSW"),
            (258.75, 281.25, "W"), (281.25, 303.75, "WNW"), (303.75, 326.25, "NW"),
            (326.25, 348.75, "NNW")
        ]

        for start, end, direction in directions:
            if start <= self.sun_position < end:
                self.sun_direction = direction
                return

        self.sun_direction = "N"

    def draw_func(self, area, cr, width, height):
        # Calculate scaling based on window size
        # Reserve space for bottom text (about 30px)
        available_height = height - 30
        # Use the smaller dimension to fit the compass
        size = min(width, available_height)
        # Compass radius is 37.5% of available size
        radius = size * 0.375
        # Center the compass
        center_x = width / 2
        center_y = (available_height) / 2

        # Set colors based on dark mode
        if self.dark_mode:
            bg_color = (45/255, 45/255, 45/255)
            text_color = (1, 1, 1)
            line_color = (200/255, 200/255, 200/255)
            compass_bg = (60/255, 60/255, 60/255)
        else:
            bg_color = (1, 1, 1)
            text_color = (0, 0, 0)
            line_color = (0, 0, 0)
            compass_bg = (240/255, 240/255, 240/255)

        # Background
        cr.set_source_rgb(*bg_color)
        cr.paint()

        # Draw compass circle
        cr.set_source_rgb(*compass_bg)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgb(*line_color)
        cr.set_line_width(2)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()

        # Draw dashes
        angles = [i * 22.5 for i in range(16)]
        for angle in angles:
            angle_rad = math.radians(angle - 90 - self.offset)

            if angle % 45 == 0:
                dash_length = radius * 0.067  # ~10 at radius 150
                cr.set_line_width(2)
            else:
                dash_length = radius * 0.033  # ~5 at radius 150
                cr.set_line_width(1)

            outer_radius = radius * 1.033  # ~155 at radius 150
            outer_x = center_x + outer_radius * math.cos(angle_rad)
            outer_y = center_y + outer_radius * math.sin(angle_rad)
            inner_x = center_x + (outer_radius - dash_length) * math.cos(angle_rad)
            inner_y = center_y + (outer_radius - dash_length) * math.sin(angle_rad)

            cr.move_to(outer_x, outer_y)
            cr.line_to(inner_x, inner_y)
            cr.stroke()

        # Draw 15° lines and direction labels
        for i in range(0, 360, 15):
            angle = (i - 90 - self.offset) % 360

            if i % 45 == 0:
                cr.set_line_width(1)
                cr.set_source_rgb(*line_color)
            else:
                if self.dark_mode:
                    cr.set_source_rgb(line_color[0] * 1.5, line_color[1] * 1.5, line_color[2] * 1.5)
                else:
                    cr.set_source_rgb(line_color[0] * 0.7, line_color[1] * 0.7, line_color[2] * 0.7)
                cr.set_line_width(0.5)

            line_radius = radius * 0.933  # ~140 at radius 150
            end_x = center_x + line_radius * math.cos(math.radians(angle))
            end_y = center_y + line_radius * math.sin(math.radians(angle))

            cr.move_to(center_x, center_y)
            cr.line_to(end_x, end_y)
            cr.stroke()

            # Draw direction text
            if i % 45 == 0:
                text = self.get_direction(i)
                text_radius = radius * 1.2  # ~180 at radius 150
                text_x = center_x + text_radius * math.cos(math.radians(angle))
                text_y = center_y + text_radius * math.sin(math.radians(angle))

                cr.set_source_rgb(*text_color)
                cr.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(radius * 0.08)  # ~12 at radius 150

                extents = cr.text_extents(text)
                cr.move_to(text_x - extents.width / 2, text_y + extents.height / 2)
                cr.show_text(text)

        # Draw bottom text (centered, 3 items)
        offset_y = height - 15
        cr.set_source_rgb(*text_color)
        cr.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(max(11, radius * 0.08))  # ~12 at radius 150, min 11

        hours, remainder = divmod(abs(self.time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        # Center the 3 text items horizontally
        spacing = width / 3
        cr.move_to(10, offset_y)
        cr.show_text(f"{self.event} in {time_str}")

        cr.move_to(spacing + 10, offset_y)
        cr.show_text(f"Pos: {self.sun_position:.1f}°")

        cr.move_to(spacing * 2 + 10, offset_y)
        cr.show_text(f"Dir: {self.sun_direction}")

        # Time to angle function
        def time_to_angle(t):
            hour = t.hour + t.minute / 60 + t.second / 3600
            return (hour / 24 * 360) - 90 - self.offset

        sunrise_angle = time_to_angle(self.sunrise)
        sunset_angle = time_to_angle(self.sunset)
        noon_angle = time_to_angle(self.solar_noon)

        # Draw sunrise marker with label
        marker_radius = radius * 0.933  # ~140 at radius 150
        sunrise_x = center_x + marker_radius * math.cos(math.radians(sunrise_angle))
        sunrise_y = center_y + marker_radius * math.sin(math.radians(sunrise_angle))
        cr.set_source_rgb(1, 1, 0)
        cr.arc(sunrise_x, sunrise_y, radius * 0.04, 0, 2 * math.pi)  # ~6 at radius 150
        cr.fill()

        label_radius = radius * 1.12  # ~168 at radius 150
        label_x = center_x + label_radius * math.cos(math.radians(sunrise_angle))
        label_y = center_y + label_radius * math.sin(math.radians(sunrise_angle))
        cr.set_source_rgb(*text_color)
        cr.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(max(9, radius * 0.067))  # ~10 at radius 150, min 9
        rise_text = self.sunrise.strftime('%H:%M')
        extents = cr.text_extents(rise_text)
        cr.move_to(label_x - extents.width / 2, label_y + extents.height / 4)
        cr.show_text(rise_text)

        # Draw sunset marker with label
        sunset_x = center_x + marker_radius * math.cos(math.radians(sunset_angle))
        sunset_y = center_y + marker_radius * math.sin(math.radians(sunset_angle))
        cr.set_source_rgb(139/255, 0, 0)
        cr.arc(sunset_x, sunset_y, radius * 0.04, 0, 2 * math.pi)  # ~6 at radius 150
        cr.fill()

        label_x = center_x + label_radius * math.cos(math.radians(sunset_angle))
        label_y = center_y + label_radius * math.sin(math.radians(sunset_angle))
        cr.set_source_rgb(*text_color)
        cr.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(max(9, radius * 0.067))  # ~10 at radius 150, min 9
        set_text = self.sunset.strftime('%H:%M')
        extents = cr.text_extents(set_text)
        cr.move_to(label_x - extents.width / 2, label_y + extents.height / 4)
        cr.show_text(set_text)

        # Draw solar noon marker with label
        noon_x = center_x + marker_radius * math.cos(math.radians(noon_angle))
        noon_y = center_y + marker_radius * math.sin(math.radians(noon_angle))
        cr.set_source_rgb(1, 0, 0)
        cr.arc(noon_x, noon_y, radius * 0.04, 0, 2 * math.pi)  # ~6 at radius 150
        cr.fill()

        label_x = center_x + label_radius * math.cos(math.radians(noon_angle))
        label_y = center_y + label_radius * math.sin(math.radians(noon_angle))
        cr.set_source_rgb(*text_color)
        cr.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(max(10, radius * 0.08))  # ~12 at radius 150, min 10
        noon_text = self.solar_noon.strftime('%H:%M')
        extents = cr.text_extents(noon_text)
        cr.move_to(label_x - extents.width / 2, label_y + extents.height / 4)
        cr.show_text(noon_text)

        # Draw daylight gradient
        gradient = cairo.RadialGradient(center_x, center_y, 0, center_x, center_y, radius)
        r, g, b = self.gradient_color[0]/255, self.gradient_color[1]/255, self.gradient_color[2]/255
        gradient.add_color_stop_rgba(0.0, r, g, b, 0.77)
        gradient.add_color_stop_rgba(0.5, r, g, b, 0.5)
        gradient.add_color_stop_rgba(1.0, r, g, b, 0.0)

        cr.set_source(gradient)
        cr.move_to(center_x, center_y)

        steps = 50
        if sunset_angle < sunrise_angle:
            for i in range(steps // 2 + 1):
                fraction = i / (steps // 2)
                angle = sunrise_angle + fraction * (360 - sunrise_angle)
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                cr.line_to(x, y)

            for i in range(steps // 2 + 1):
                fraction = i / (steps // 2)
                angle = fraction * sunset_angle
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                cr.line_to(x, y)
        else:
            for i in range(steps + 1):
                fraction = i / steps
                angle = sunrise_angle + fraction * (sunset_angle - sunrise_angle)
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                cr.line_to(x, y)

        cr.close_path()
        cr.fill()

        # Draw clock hands
        self.draw_clock_hands(cr, line_color, text_color, center_x, center_y, radius)

        # Draw current sun position if daytime
        sun_angle = time_to_angle(self.now)
        sun_x = center_x + marker_radius * math.cos(math.radians(sun_angle))
        sun_y = center_y + marker_radius * math.sin(math.radians(sun_angle))

        if self.sunrise <= self.now <= self.sunset:
            cr.set_source_rgb(1, 0.647, 0)  # Orange
            cr.arc(sun_x, sun_y, radius * 0.067, 0, 2 * math.pi)  # ~10 at radius 150
            cr.fill()

    def draw_clock_hands(self, cr, line_color, text_color, center_x, center_y, radius):
        hour_decimal = self.now.hour + self.now.minute / 60 + self.now.second / 3600
        hour_angle = (hour_decimal / 24) * 360 - 90 - self.offset

        minute_angle = (self.now.minute / 60) * 360 - 90 - self.offset
        second_angle = (self.now.second / 60) * 360 - 90 - self.offset

        # Scale hand lengths based on radius (~80, ~110, ~140 at radius 150)
        self.draw_hand(cr, hour_angle, radius * 0.533, 4, line_color, center_x, center_y)
        self.draw_hand(cr, minute_angle, radius * 0.733, 3, line_color, center_x, center_y)
        self.draw_hand(cr, second_angle, radius * 0.933, 1, (1, 0, 0), center_x, center_y)

    def draw_hand(self, cr, angle, length, width, color, center_x, center_y):
        end_x = center_x + length * math.cos(math.radians(angle))
        end_y = center_y + length * math.sin(math.radians(angle))

        cr.set_source_rgb(*color)
        cr.set_line_width(width)
        cr.move_to(center_x, center_y)
        cr.line_to(end_x, end_y)
        cr.stroke()

    def get_direction(self, angle):
        directions = {
            0: 'N', 45: 'NE', 90: 'E', 135: 'SE',
            180: 'S', 225: 'SW', 270: 'W', 315: 'NW'
        }
        return directions.get(angle, '')


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title('Celesun')

        # Set clock icon
        self.set_icon_name('preferences-system-time')

        # Load config
        self.config = load_config()

        # Set window size from config with minimum size of 300x350
        width = max(300, self.config['window_width'])
        height = max(350, self.config['window_height'])
        self.set_default_size(width, height)

        # Header bar
        header = Adw.HeaderBar()

        # Settings button
        settings_btn = Gtk.Button(icon_name='emblem-system-symbolic')
        settings_btn.connect('clicked', self.open_settings)
        header.pack_end(settings_btn)

        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header)

        self.compass = CompassWidget(self)
        main_box.append(self.compass)

        # Apply loaded config to compass
        self.compass.latitude = self.config['latitude']
        self.compass.longitude = self.config['longitude']
        self.compass.timezone = self.config['timezone']
        self.compass.offset = self.config['offset']
        self.compass.dark_mode = self.config['dark_mode']
        self.compass.gradient_color = tuple(self.config['gradient_color'])
        self.compass.font_family = self.config['font_family']
        self.compass.sun = Sun(self.compass.latitude, self.compass.longitude)
        self.compass.update_data()

        # Apply dark mode using AdwStyleManager
        self.apply_dark_mode(self.compass.dark_mode)

        self.set_content(main_box)

        # Connect close request to save config
        self.connect('close-request', self.on_close_request)

    def open_settings(self, button):
        dialog = SettingsDialog(
            self,
            self.compass.latitude,
            self.compass.longitude,
            self.compass.timezone,
            self.compass.offset,
            self.compass.dark_mode,
            self.compass.gradient_color,
            self.compass.font_family
        )
        dialog.connect('close-request', lambda d: self.on_settings_closed(d))
        dialog.present()

    def on_settings_closed(self, dialog):
        if dialog.result:
            latitude, longitude, timezone, offset, dark_mode, gradient_color, font_family = dialog.result

            self.compass.latitude = latitude
            self.compass.longitude = longitude
            self.compass.timezone = timezone
            self.compass.offset = offset
            self.compass.dark_mode = dark_mode
            self.compass.gradient_color = gradient_color
            self.compass.font_family = font_family

            self.compass.sun = Sun(latitude, longitude)
            self.compass.sunrise = None
            self.compass.sunset = None
            self.compass.solar_noon = None
            self.compass.now = None
            self.compass.event = ""
            self.compass.time_left = datetime.timedelta(0)

            self.compass.update_data()
            self.compass.queue_draw()

            # Apply dark mode
            self.apply_dark_mode(dark_mode)

            # Save config to file
            width = self.get_width()
            height = self.get_height()
            save_config(
                latitude, longitude, timezone, offset, dark_mode, gradient_color,
                width, height, self.compass.font_family
            )

    def apply_dark_mode(self, dark_mode):
        """Apply dark mode using AdwStyleManager"""
        style_manager = Adw.StyleManager.get_default()
        if dark_mode:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

    def on_close_request(self, window):
        """Save config when window is closed"""
        # Get current window size
        width = self.get_width()
        height = self.get_height()

        # Save config with current window size
        save_config(
            self.compass.latitude,
            self.compass.longitude,
            self.compass.timezone,
            self.compass.offset,
            self.compass.dark_mode,
            self.compass.gradient_color,
            width,
            height,
            self.compass.font_family
        )
        return False  # Allow the window to close


class CelesunApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.celesun.app')

    def do_activate(self):
        win = MainWindow(self)
        win.present()


if __name__ == '__main__':
    app = CelesunApp()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nReceived keyboard interrupt, closing...")
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)

    # Allow SIGINT to interrupt the GTK main loop
    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, lambda: app.quit())

    app.run(sys.argv)
