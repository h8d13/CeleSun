import sys
import math
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QVBoxLayout, QCompleter, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QCheckBox, QComboBox
from PyQt5.QtGui import QPainter, QPen, QFont, QFontMetrics, QBrush, QColor, QRadialGradient, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QPoint, QTimer, QEvent, QObject
from suntime import Sun
import pytz

## Todo:
# Dump settings somewhere so it uses the same

## Annoying settings stuff 
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setFixedSize(300, 300)  

        self.layout = QVBoxLayout()

        # Latitude input
        self.latitude_label = QLabel('Latitude:')
        self.latitude_input = QLineEdit()
        self.layout.addWidget(self.latitude_label)
        self.layout.addWidget(self.latitude_input)

        # Longitude input
        self.longitude_label = QLabel('Longitude:')
        self.longitude_input = QLineEdit()
        self.layout.addWidget(self.longitude_label)
        self.layout.addWidget(self.longitude_input)

        # Timezone input with autocomplete
        self.timezone_label = QLabel('Timezone:')
        self.timezone_input = QLineEdit()
        self.layout.addWidget(self.timezone_label)
        self.layout.addWidget(self.timezone_input)
        
        # Add separator
        self.layout.addSpacing(10)
        self.separator = QLabel("Appearance:")
        self.layout.addWidget(self.separator)
        
        # Dark mode checkbox
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.layout.addWidget(self.dark_mode_checkbox)
        
        # Gradient color selector
        self.gradient_label = QLabel("Daylight Gradient:")
        self.layout.addWidget(self.gradient_label)
        
        self.gradient_selector = QComboBox()
        self.gradient_selector.addItem("Yellow (Default)", QColor(255, 255, 0))
        self.gradient_selector.addItem("Orange", QColor(255, 165, 0))
        self.gradient_selector.addItem("Blue", QColor(135, 206, 235))
        self.gradient_selector.addItem("Green", QColor(144, 238, 144))
        self.gradient_selector.addItem("Pink", QColor(255, 182, 193))
        self.layout.addWidget(self.gradient_selector)

        # Load timezones from file and set up autocompletion
        self.load_timezones()

        # Buttons row (OK, Cancel, and Reset)
        self.button_row = QHBoxLayout()
        
        # Add Reset button
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.button_row.addWidget(self.reset_button)
        
        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.button_row.addWidget(self.buttons)
        
        self.layout.addLayout(self.button_row)

        self.setLayout(self.layout)
        
    def reset_to_defaults(self):
        """Reset to default values (Paris)"""
        self.latitude_input.setText("48.8575")
        self.longitude_input.setText("2.3514")
        self.timezone_input.setText("Europe/Paris")
        self.dark_mode_checkbox.setChecked(False)
        self.gradient_selector.setCurrentIndex(0)  # Yellow

    def load_timezones(self):
        """Loads the list of timezones from a file and sets up autocompletion."""
        try:
            with open("timezones.txt", "r") as file:
                timezone_list = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            timezone_list = []

        # Set up autocompletion with custom behavior
        completer = QCompleter(timezone_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # Case insensitive matching
        completer.setCompletionMode(QCompleter.PopupCompletion)  # Shows dropdown suggestions
        completer.setFilterMode(Qt.MatchContains)  # Allows searching anywhere in the string

        # Assign completer to timezone input field
        self.timezone_input.setCompleter(completer)

    def get_values(self):
        try:
            latitude = float(self.latitude_input.text())
            longitude = float(self.longitude_input.text())
            timezone = self.timezone_input.text().strip()
            dark_mode = self.dark_mode_checkbox.isChecked()
            gradient_color = self.gradient_selector.currentData()
            return (latitude, longitude, timezone, dark_mode, gradient_color)
        except ValueError as e:
            print(f"Invalid input: {e}")
            raise

## Actual stuff
class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 500)
        self.setWindowTitle('Celesun')

        # Default location (Paris)
        self.latitude = 48.8575
        self.longitude = 2.3514
        self.timezone = "Europe/Paris"
        
        # Default appearance settings
        self.dark_mode = False
        self.gradient_color = QColor(255, 255, 0)  # Yellow

        # Initialize Sun object
        self.sun = Sun(self.latitude, self.longitude)
        
        # Initialize times
        self.sunrise = None
        self.sunset = None
        self.solar_noon = None
        self.now = None
        self.event = ""
        self.time_left = datetime.timedelta(0)
        self.sun_position = 0
        self.sun_direction = "N"

        # Timer for updating the UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Update every second

        # Initial update
        self.update_data()

        # Settings button
        self.settings_button = QPushButton('⚙', self)
        self.settings_button.setGeometry(360, 10, 30, 30)
        self.settings_button.clicked.connect(self.open_settings)
        # Add clock button next to settings
        self.clock_button = QPushButton('🕒', self)
        self.clock_button.setGeometry(320, 10, 30, 30)
        self.clock_button.clicked.connect(self.open_clock_window)
        self.clock_button.setToolTip("Open High Precision Clock")

    def open_clock_window(self):
        import time
        import threading
        
        # Create a class for the clock window
        class FastClockWindow(QWidget):
            def __init__(self, parent_timezone, dark_mode):
                super().__init__()
                self.parent_timezone = parent_timezone
                self.dark_mode = dark_mode
                self.setup_ui()
                self.running = True
                self.clock_thread = threading.Thread(target=self.clock_worker, daemon=True)
                self.clock_thread.start()
                
            def setup_ui(self):
                self.setWindowTitle("High Precision Clock")
                self.setFixedSize(400, 100)
            
                layout = QVBoxLayout()
                self.clock_label = QLabel("--:--:--.---.---")
                self.clock_label.setAlignment(Qt.AlignCenter)
            
                # Set font to be large and monospace
                font = self.clock_label.font()
                font.setFamily("monospace")
                font.setPointSize(20)
                self.clock_label.setFont(font)
            
                layout.addWidget(self.clock_label)
                self.setLayout(layout)
                
                # Apply dark mode if enabled
                self.update_stylesheet()
                
            def update_stylesheet(self):
                """Update the widget stylesheet based on dark mode setting"""
                if self.dark_mode:
                    self.setStyleSheet("""
                        QWidget {
                            background-color: #2D2D2D;
                            color: #FFFFFF;
                        }
                        QLabel {
                            color: #FFFFFF;
                        }
                    """)
                else:
                    self.setStyleSheet("")  # Reset to default styling
            
            def clock_worker(self):
                """Worker function that runs in a separate thread"""
                while self.running:
                    # Get time with highest precision available
                    ns_time = time.time_ns()
                    
                    # Get current UTC time
                    utc_now = datetime.datetime.utcfromtimestamp(ns_time / 1_000_000_000)
                    
                    # Convert to the parent timezone
                    try:
                        local_tz = pytz.timezone(self.parent_timezone)
                        local_now = pytz.utc.localize(utc_now).astimezone(local_tz)
                    except:
                        # Fallback to system time if timezone is invalid
                        local_now = utc_now
                    
                    # Extract time components
                    hours = local_now.hour
                    minutes = local_now.minute
                    seconds = local_now.second
                    
                    # Microseconds from datetime
                    ms = local_now.microsecond // 1000
                    us = local_now.microsecond % 1000
                    
                    # Nanoseconds (estimated)
                    ns = (ns_time % 1_000_000) // 1_000
                    
                    clock_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}.{us:03d}.{ns:03d}"
                    
                    # Update the UI from the main thread
                    QApplication.instance().postEvent(self, _ClockUpdateEvent(clock_text))
                    
                    # Sleep a tiny amount to prevent excessive CPU usage
                    # Still allows for sub-millisecond updates
                    time.sleep(0.0005)
                    
            def closeEvent(self, event):
                """Handle window close event to stop the thread"""
                self.running = False
                if self.clock_thread.is_alive():
                    self.clock_thread.join(1.0)  # Wait up to 1 second for thread to finish
                super().closeEvent(event)
        
        # Custom event for thread-safe UI updates
        class _ClockUpdateEvent(QEvent):
            EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
            
            def __init__(self, clock_text):
                super().__init__(_ClockUpdateEvent.EVENT_TYPE)
                self.clock_text = clock_text
        
        # Event filter to handle custom events
        class ClockEventFilter(QObject):
            def __init__(self, clock_window):
                super().__init__()
                self.clock_window = clock_window
                
            def eventFilter(self, obj, event):
                if event.type() == _ClockUpdateEvent.EVENT_TYPE:
                    self.clock_window.clock_label.setText(event.clock_text)
                    return True
                return super().eventFilter(obj, event)
        
        # Create and store the window instance as an attribute
        self.clock_window = FastClockWindow(self.timezone, self.dark_mode)
        
        # Install event filter for thread-safe UI updates
        self.clock_event_filter = ClockEventFilter(self.clock_window)
        self.clock_window.installEventFilter(self.clock_event_filter)
        
        self.clock_window.show()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.latitude_input.setText(str(self.latitude))
        dialog.longitude_input.setText(str(self.longitude))
        dialog.timezone_input.setText(self.timezone)
        dialog.dark_mode_checkbox.setChecked(self.dark_mode)
        
        # Find and select the current gradient color
        for i in range(dialog.gradient_selector.count()):
            if dialog.gradient_selector.itemData(i).name() == self.gradient_color.name():
                dialog.gradient_selector.setCurrentIndex(i)
                break

        if dialog.exec_():
            try:
                # Get new values
                self.latitude, self.longitude, self.timezone, self.dark_mode, self.gradient_color = dialog.get_values()
                
                # Update sun calculator
                self.sun = Sun(self.latitude, self.longitude)
                
                # Reset times to force recalculation
                self.sunrise = None
                self.sunset = None
                self.solar_noon = None
                self.now = None
                self.event = ""
                self.time_left = datetime.timedelta(0)
                
                # Force a complete update
                self.update_data()
                
                # Force a repaint
                self.update()
                
                # Update background color based on dark mode
                self.update_stylesheet()
            except Exception as e:
                print(f"Error updating settings: {e}")
    
    def update_stylesheet(self):
        """Update the widget stylesheet based on dark mode setting"""
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #3D3D3D;
                    color: #FFFFFF;
                    border: 1px solid #5D5D5D;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;
                }
            """)
        else:
            self.setStyleSheet("")  # Reset to default styling

    def update_data(self):
        try:
            # Get timezone
            try:
                local_tz = pytz.timezone(self.timezone)
            except pytz.UnknownTimeZoneError:
                local_tz = pytz.utc
                
            # Get current time
            utc_now = datetime.datetime.now(pytz.utc)
            self.now = utc_now.astimezone(local_tz)
            
            # Current date in local timezone
            today = self.now.date()
            
            # Create datetime for TODAY at midnight in local timezone
            local_midnight = datetime.datetime.combine(today, datetime.time(0, 0))
            local_midnight = local_tz.localize(local_midnight)
            utc_midnight = local_midnight.astimezone(pytz.utc)
            
            # Calculate sunrise, sunset for TODAY
            try:
                sunrise_utc = self.sun.get_sunrise_time(utc_midnight)
                sunset_utc = self.sun.get_sunset_time(utc_midnight)
                
                # Convert to local timezone
                self.sunrise = sunrise_utc.astimezone(local_tz)
                self.sunset = sunset_utc.astimezone(local_tz)
                
                # FORCE the date to be today
                self.sunrise = local_tz.localize(datetime.datetime.combine(today, self.sunrise.time()))
                self.sunset = local_tz.localize(datetime.datetime.combine(today, self.sunset.time()))
                
                # Calculate solar noon (exactly halfway between sunrise and sunset)
                self.solar_noon = local_tz.localize(datetime.datetime.combine(
                    today, 
                    datetime.time(
                        (self.sunrise.hour + self.sunset.hour) // 2,
                        (self.sunrise.minute + self.sunset.minute) // 2
                    )
                ))
            except Exception as e:
                print(f"Error calculating sun times: {e}")
                # Fallback values for TODAY
                self.sunrise = local_tz.localize(datetime.datetime.combine(today, datetime.time(6, 0)))
                self.sunset = local_tz.localize(datetime.datetime.combine(today, datetime.time(18, 0)))
                self.solar_noon = local_tz.localize(datetime.datetime.combine(today, datetime.time(12, 0)))
            
            # Calculate next event and time remaining
            self.calculate_next_event(local_tz)
            
            # Calculate current sun position
            self.calculate_sun_position()
            
            # Trigger a repaint to show the updated clock
            self.update()
            
        except Exception as e:
            print(f"Error in update_data: {e}")
    
    def calculate_next_event(self, local_tz):
        """Calculate the next sun event (sunrise/sunset) and time remaining."""
        # Get the current time
        now = self.now
        
        # If it's before sunrise, next event is sunrise
        if now < self.sunrise:
            self.event = "Sunrise"
            self.time_left = self.sunrise - now
        # If it's before sunset, next event is sunset
        elif now < self.sunset:
            self.event = "Sunset"
            self.time_left = self.sunset - now
        # After sunset, next event is tomorrow's sunrise
        else:
            # Create tomorrow's date
            tomorrow = now.date() + datetime.timedelta(days=1)
            
            # Use today's sunrise time but with tomorrow's date
            tomorrow_sunrise = local_tz.localize(datetime.datetime.combine(
                tomorrow, 
                self.sunrise.time()
            ))
            
            self.event = "Sunrise (tomorrow)"
            self.time_left = tomorrow_sunrise - now

    def calculate_sun_position(self):
        """Calculate the sun's position and direction based on the time of day."""
        # Calculate sun position in degrees (0-360)
        # Mapping: 0 = midnight, 90 = 6am, 180 = noon, 270 = 6pm
        current_hour = self.now.hour + self.now.minute / 60 + self.now.second / 3600
        self.sun_position = (current_hour * 15) % 360  # 15 degrees per hour
        
        # Get direction based on position
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
                
        # Default to North if no match (shouldn't happen with proper ranges)
        self.sun_direction = "N"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set colors based on dark mode
        if self.dark_mode:
            background_color = QColor(45, 45, 45)
            text_color = QColor(255, 255, 255)
            line_color = QColor(200, 200, 200)
            compass_bg_color = QColor(60, 60, 60)
        else:
            background_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)
            line_color = QColor(0, 0, 0)
            compass_bg_color = QColor(240, 240, 240)
        
        # Fill background
        painter.fillRect(self.rect(), background_color)
        
        # Draw the compass circle
        painter.setPen(QPen(line_color, 2, Qt.SolidLine))
        painter.setBrush(compass_bg_color)
        painter.drawEllipse(50, 50, 300, 300)

        # Draw dashes at major and midpoints
        angles = [i * 22.5 for i in range(16)]  # Generate 0, 22.5, 45, ..., 337.5
        for angle in angles:
            angle_rad = math.radians(angle - 90)  # Convert to radians, adjust North to top

            # Determine dash length (longer for main cardinals, shorter for midpoints)
            if angle % 45 == 0:
                dash_length = 10  # Longer dashes for main cardinals
                pen = QPen(line_color, 2)  # Thicker
            else:
                dash_length = 5  # Shorter dashes for midpoints
                pen = QPen(line_color, 1)  # Thinner

            painter.setPen(pen)

            # Outer point (just outside the compass circle)
            outer_x = 200 + 155 * math.cos(angle_rad)
            outer_y = 200 + 155 * math.sin(angle_rad)

            # Inner point (a bit inside the compass circle)
            inner_x = 200 + (155 - dash_length) * math.cos(angle_rad)
            inner_y = 200 + (155 - dash_length) * math.sin(angle_rad)

            # Draw the dash
            painter.drawLine(QPointF(outer_x, outer_y), QPointF(inner_x, inner_y))

        # Draw the 15° line increments
        for i in range(0, 360, 15):
            angle = (i - 90) % 360  # Adjust angle to ensure north is at the top
            if i % 45 == 0:
                pen = QPen(line_color, 1, Qt.SolidLine)
                font = QFont('Arial', 12, QFont.Bold)
            else:
                pen = QPen(line_color.lighter(150) if self.dark_mode else line_color.darker(150), 0.5, Qt.SolidLine)
                font = QFont('Arial', 8, QFont.Normal)

            painter.setPen(pen)
            painter.setFont(font)

            # Calculate the end point of the line
            end_point = QPointF(200 + 140 * math.cos(math.radians(angle)),
                                200 + 140 * math.sin(math.radians(angle)))

            # Convert QPointF to QPoint
            start_point = QPoint(200, 200)
            end_point_int = QPoint(int(end_point.x()), int(end_point.y()))

            # Draw the line
            painter.drawLine(start_point, end_point_int)

            # Draw the text for directions
            if i % 45 == 0:
                text = self.get_direction(i)
                text_radius = 180  # Larger radius for text labels
                text_point = QPointF(200 + text_radius * math.cos(math.radians(angle)),
                                    200 + text_radius * math.sin(math.radians(angle)))
                text_point_int = QPoint(int(text_point.x()), int(text_point.y()))

                # Center the text around the text_point
                font_metrics = QFontMetrics(font)
                text_rect = font_metrics.boundingRect(text)
                text_x = text_point_int.x() - text_rect.width() / 2
                text_y = text_point_int.y() - text_rect.height() / 2

                # Adjust the vertical position to ensure the text is aligned correctly
                text_y += text_rect.height() / 2

                # Convert to integers
                text_x_int = int(text_x)
                text_y_int = int(text_y)

                # Draw the text with a consistent margin
                painter.setPen(text_color)
                painter.drawText(QPoint(text_x_int, text_y_int), text)

        # Move the text display below the compass circle
        offset_y = 360  # Adjust the starting Y position to make space below the compass

        # Draw the sunrise, sunset, and other information below the compass
        painter.setPen(QPen(text_color, 1))
        painter.setFont(QFont('Arial', 10))

        # Display sunrise and sunset times in 24h format
        painter.drawText(10, offset_y, f"Rise: {self.sunrise.strftime('%H:%M:%S')}")
        offset_y += 20
        painter.drawText(10, offset_y, f"Set: {self.sunset.strftime('%H:%M:%S')}")
        offset_y += 20

        # Display time left for the next event - ALWAYS POSITIVE
        hours, remainder = divmod(abs(self.time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        painter.drawText(10, offset_y, f"Next event: {self.event}")
        offset_y += 20
        painter.drawText(10, offset_y, f"Time Left: {time_str}")
        offset_y += 20

        # Display solar noon time
        painter.drawText(10, offset_y, f"Solar Noon: {self.solar_noon.strftime('%H:%M:%S')}")
        offset_y += 20

        # Display current sun position and direction
        painter.drawText(10, offset_y, f"Sun Position: {self.sun_position:.2f}°")
        offset_y += 20
        painter.drawText(10, offset_y, f"Sun Direction: {self.sun_direction}")

        # Calculate positions for sunrise, sunset and solar noon on the 24h clock
        
        # Convert clock times to angles (24-hour clock)
        # 0h = top (0°), 6h = right (90°), 12h = bottom (180°), 18h = left (270°)
        def time_to_angle(time):
            hour = time.hour + time.minute / 60 + time.second / 3600
            return (hour / 24 * 360) - 90  # -90 to make 0h at top
        
        sunrise_angle = time_to_angle(self.sunrise)
        sunset_angle = time_to_angle(self.sunset)
        noon_angle = time_to_angle(self.solar_noon)
        
        # Draw sunrise marker (yellow)
        sunrise_x = 200 + 140 * math.cos(math.radians(sunrise_angle))
        sunrise_y = 200 + 140 * math.sin(math.radians(sunrise_angle))
        painter.setPen(QPen(line_color, 3, Qt.SolidLine))
        painter.setBrush(Qt.yellow)
        painter.drawEllipse(QPointF(sunrise_x, sunrise_y), 6, 6)
        
        # Draw sunset marker (dark red)
        sunset_x = 200 + 140 * math.cos(math.radians(sunset_angle))
        sunset_y = 200 + 140 * math.sin(math.radians(sunset_angle))
        painter.setPen(QPen(line_color, 3, Qt.SolidLine))
        painter.setBrush(Qt.darkRed)
        painter.drawEllipse(QPointF(sunset_x, sunset_y), 6, 6)
        
        # Draw solar noon marker (red)
        noon_x = 200 + 140 * math.cos(math.radians(noon_angle))
        noon_y = 200 + 140 * math.sin(math.radians(noon_angle))
        painter.setPen(QPen(line_color, 3, Qt.SolidLine))
        painter.setBrush(Qt.red)
        painter.drawEllipse(QPointF(noon_x, noon_y), 6, 6)

        # Create a radial gradient for daytime arc with the selected color
        gradient = QRadialGradient(200, 200, 150)
        gradient.setColorAt(0.0, QColor(self.gradient_color.red(), self.gradient_color.green(), self.gradient_color.blue(), 255))  # Brightest at center
        gradient.setColorAt(0.5, QColor(self.gradient_color.red(), self.gradient_color.green(), self.gradient_color.blue(), 128))  # Midway fade
        gradient.setColorAt(1.0, QColor(self.gradient_color.red(), self.gradient_color.green(), self.gradient_color.blue(), 0))    # Fully transparent at edge
        
        # Apply gradient
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        
        # Draw the daylight arc
        highlight_path = QPainterPath()
        highlight_path.moveTo(200, 200)  # Center
        
        # Handle case where sunset is earlier than sunrise (crossing midnight)
        steps = 50
        if sunset_angle < sunrise_angle:
            # First part: sunrise to end of day
            for i in range(steps // 2 + 1):
                fraction = i / (steps // 2)
                angle = sunrise_angle + fraction * (360 - sunrise_angle)
                x = 200 + 150 * math.cos(math.radians(angle))
                y = 200 + 150 * math.sin(math.radians(angle))
                highlight_path.lineTo(x, y)
                
            # Second part: start of day to sunset
            for i in range(steps // 2 + 1):
                fraction = i / (steps // 2)
                angle = fraction * sunset_angle
                x = 200 + 150 * math.cos(math.radians(angle))
                y = 200 + 150 * math.sin(math.radians(angle))
                highlight_path.lineTo(x, y)
        else:
            # Normal case: sunrise to sunset within same day
            for i in range(steps + 1):
                fraction = i / steps
                angle = sunrise_angle + fraction * (sunset_angle - sunrise_angle)
                x = 200 + 150 * math.cos(math.radians(angle))
                y = 200 + 150 * math.sin(math.radians(angle))
                highlight_path.lineTo(x, y)
        
        highlight_path.closeSubpath()
        painter.drawPath(highlight_path)

        # Draw the clock hands
        self.draw_clock_hands(painter, line_color, text_color)
        
        # Draw current sun position marker if daytime
        sun_angle = time_to_angle(self.now)  # Current time angle
        sun_x = 200 + 140 * math.cos(math.radians(sun_angle))
        sun_y = 200 + 140 * math.sin(math.radians(sun_angle))
        
        if self.sunrise <= self.now <= self.sunset:
            painter.setPen(QPen(Qt.red, 3))
            painter.setBrush(Qt.red)
            painter.drawEllipse(QPointF(sun_x, sun_y), 10, 10)

    def draw_clock_hands(self, painter, line_color, text_color):
        # 24-hour clock: Hour hand shows time of day
        hour_decimal = self.now.hour + self.now.minute / 60 + self.now.second / 3600
        hour_angle = (hour_decimal / 24) * 360 - 90  # -90 to make 0h at top
        
        # 60-minute/second clock: Minute and second hands show traditional time
        minute_angle = (self.now.minute / 60) * 360 - 90
        second_angle = (self.now.second / 60) * 360 - 90
        
        # Draw the hands
        self.draw_hand(painter, hour_angle, 80, 4, line_color)        # Hour (shorter)
        self.draw_hand(painter, minute_angle, 110, 3, line_color)     # Minute (medium)
        self.draw_hand(painter, second_angle, 140, 1, Qt.red)  # Second (longest, red)

    def draw_hand(self, painter, angle, length, width, color=Qt.black):
        # Calculate end point
        end_x = 200 + length * math.cos(math.radians(angle))
        end_y = 200 + length * math.sin(math.radians(angle))
        
        # Draw the hand
        painter.setPen(QPen(color, width, Qt.SolidLine))
        painter.drawLine(QPoint(200, 200), QPoint(int(end_x), int(end_y)))

    def get_direction(self, angle):
        directions = {
            0: 'N', 45: 'NE', 90: 'E', 135: 'SE',
            180: 'S', 225: 'SW', 270: 'W', 315: 'NW'
        }
        return directions.get(angle, '')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    compass = CompassWidget()
    compass.show()
    sys.exit(app.exec_())
