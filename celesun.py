import sys
import math
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QVBoxLayout, QCompleter, QLabel, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QPainter, QPen, QFont, QFontMetrics, QBrush, QColor, QRadialGradient, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QPoint, QTimer
from suntime import Sun
import pytz

##### CONFIG
# color: black/white + bg
# offset: 90° default

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setFixedSize(300, 200)

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

        # Load timezones from file and set up autocompletion
        self.load_timezones()

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

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
        return (
            float(self.latitude_input.text()),
            float(self.longitude_input.text()),
            self.timezone_input.text().strip()
        )
    
class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 500)
        self.setWindowTitle('Celesun')

        # Default location (Paris)
        self.latitude = 48.8575
        self.longitude = 2.3514
        self.timezone = "Europe/Paris"

        self.sun = Sun(self.latitude, self.longitude)

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

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.latitude_input.setText(str(self.latitude))
        dialog.longitude_input.setText(str(self.longitude))
        dialog.timezone_input.setText(self.timezone)

        if dialog.exec_():
            self.latitude, self.longitude, self.timezone = dialog.get_values()
            self.sun = Sun(self.latitude, self.longitude)
            self.update_data()

    def update_data(self):
        # Get current time in UTC
        utc_now = datetime.datetime.now(pytz.utc)

        # Use manually entered timezone
        try:
            local_tz = pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError:
            local_tz = pytz.utc  # Default to UTC if invalid timezone

        self.now = utc_now.astimezone(local_tz)

        # Get sunrise and sunset in the local timezone
        self.sunrise = self.sun.get_local_sunrise_time(self.now).replace(tzinfo=local_tz)
        self.sunset = self.sun.get_local_sunset_time(self.now).replace(tzinfo=local_tz)

        # Determine next event (sunrise or sunset)
        self.event, self.time_left = self.calculate_time_left()

        # Solar noon calculation
        self.solar_noon = self.sunrise + (self.sunset - self.sunrise) / 2

        # Sun position and direction
        self.sun_position, self.sun_direction = self.calculate_sun_position()

        # Refresh UI
        self.update()

    def calculate_time_left(self):
        if self.now < self.sunrise:
            return "Sunrise", self.sunrise - self.now
        elif self.now < self.sunset:
            return "Sunset", self.sunset - self.now
        else:
            next_sunrise = self.sun.get_local_sunrise_time(self.now + datetime.timedelta(days=1)).replace(tzinfo=self.now.tzinfo)
            return "Sunrise (next day)", next_sunrise - self.now

    def calculate_sun_position(self):
        current_hour = self.now.hour + self.now.minute / 60
        sun_position = (current_hour * 15) % 360

        directions = {
            (337.5, 22.5): "N", (22.5, 67.5): "NE", (67.5, 112.5): "E",
            (112.5, 157.5): "SE", (157.5, 202.5): "S", (202.5, 247.5): "SW",
            (247.5, 292.5): "W", (292.5, 337.5): "NW"
        }

        for (start, end), direction in directions.items():
            if start <= sun_position < end or (start > end and (sun_position >= start or sun_position < end)):
                return sun_position, direction

        return sun_position, "Unknown"


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the compass circle
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.drawEllipse(50, 50, 300, 300)

        # Draw dashes at major and midpoints
        angles = [i * 22.5 for i in range(16)]  # Generate 0, 22.5, 45, ..., 337.5
        for angle in angles:
            angle_rad = math.radians(angle - 90)  # Convert to radians, adjust North to top

            # Determine dash length (longer for main cardinals, shorter for midpoints)
            if angle % 45 == 0:
                dash_length = 10  # Longer dashes for main cardinals
                pen = QPen(Qt.black, 2)  # Thicker
            else:
                dash_length = 5  # Shorter dashes for midpoints
                pen = QPen(Qt.black, 1)  # Thinner

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
                pen = QPen(Qt.black, 1, Qt.SolidLine)
                font = QFont('Arial', 12, QFont.Bold)
            else:
                pen = QPen(Qt.black, 0.5, Qt.SolidLine)
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
                painter.drawText(QPoint(text_x_int, text_y_int), text)

        # Move the text display below the compass circle
        offset_y = 360  # Adjust the starting Y position to make space below the compass

        # Draw the sunrise, sunset, and other information below the compass
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont('Arial', 10))

        # Display sunrise and sunset times in 24h format
        painter.drawText(10, offset_y, f"Rise: {self.sunrise.strftime('%H:%M:%S')}")
        offset_y += 20
        painter.drawText(10, offset_y, f"Set: {self.sunset.strftime('%H:%M:%S')}")
        offset_y += 20

        # Display time left for the next event
        hours, remainder = divmod(self.time_left.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        painter.drawText(10, offset_y, f"Next event: {self.event}")
        offset_y += 20
        painter.drawText(10, offset_y, f"Time Left: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        offset_y += 20

        # Display solar noon time
        painter.drawText(10, offset_y, f"Solar Noon: {self.solar_noon.strftime('%H:%M:%S')}")
        offset_y += 20

        # Display current sun position and direction
        painter.drawText(10, offset_y, f"Sun Position: {self.sun_position:.2f}°")
        offset_y += 20
        painter.drawText(10, offset_y, f"Sun Direction: {self.sun_direction}")

        # Calculate positions for sunrise, sunset and solar noon for the 24h clock
        # These are based on time of day mapped to the 24h clock circle
        day_seconds = 24 * 3600

        # Sunrise marker
        sunrise_seconds = self.sunrise.hour * 3600 + self.sunrise.minute * 60 + self.sunrise.second
        sunrise_angle = (sunrise_seconds / day_seconds) * 360 - 90  # -90 to adjust for 0° at top
        sunrise_x = 200 + 140 * math.cos(math.radians(sunrise_angle))
        sunrise_y = 200 + 140 * math.sin(math.radians(sunrise_angle))
        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        painter.setBrush(Qt.yellow)  # Use yellow for sunrise
        painter.drawEllipse(QPointF(sunrise_x, sunrise_y), 6, 6)

        # Sunset marker
        sunset_seconds = self.sunset.hour * 3600 + self.sunset.minute * 60 + self.sunset.second
        sunset_angle = (sunset_seconds / day_seconds) * 360 - 90
        sunset_x = 200 + 140 * math.cos(math.radians(sunset_angle))
        sunset_y = 200 + 140 * math.sin(math.radians(sunset_angle))
        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        painter.setBrush(Qt.darkRed)  # Use dark red for sunset
        painter.drawEllipse(QPointF(sunset_x, sunset_y), 6, 6)

        # Solar Noon marker
        solar_noon_seconds = self.solar_noon.hour * 3600 + self.solar_noon.minute * 60 + self.solar_noon.second
        solar_noon_angle = (solar_noon_seconds / day_seconds) * 360 - 90
        solar_noon_x = 200 + 140 * math.cos(math.radians(solar_noon_angle))
        solar_noon_y = 200 + 140 * math.sin(math.radians(solar_noon_angle))
        painter.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        painter.setBrush(Qt.red)
        painter.drawEllipse(QPointF(solar_noon_x, solar_noon_y), 6, 6)

        # Create a radial gradient centered at the compass
        gradient = QRadialGradient(200, 200, 150)  # Center at compass, 150px radius

        # Set color stops for smooth transition
        gradient.setColorAt(0.0, QColor(255, 255, 0, 255))  # Brightest at solar noon
        gradient.setColorAt(0.5, QColor(255, 255, 0, 128))   # Midway fade
        gradient.setColorAt(1.0, QColor(255, 255, 0, 0))    # Fully transparent at sunrise/sunset

        # Apply gradient brush
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)

        # Draw only within the daytime arc
        highlight_path = QPainterPath()
        highlight_path.moveTo(200, 200)  # Center

        # Divide arc into small steps for smooth shading
        steps = 50
        for i in range(steps + 1):
            fraction = i / steps
            angle = sunrise_angle + fraction * (sunset_angle - sunrise_angle)
            x = 200 + 150 * math.cos(math.radians(angle))
            y = 200 + 150 * math.sin(math.radians(angle))
            highlight_path.lineTo(x, y)

        highlight_path.closeSubpath()

        # Draw the path with the radial gradient
        painter.drawPath(highlight_path)

        # Draw the clock hands (Hour, Minute, Second)
        self.draw_clock_hands(painter)

        sun_angle = self.sun_position - 90  # Adjust to match compass angle (0° should be at top)
        sun_x = 200 + 140 * math.cos(math.radians(sun_angle))
        sun_y = 200 + 140 * math.sin(math.radians(sun_angle))

        if self.sunrise <= self.now <= self.sunset:
            painter.setPen(QPen(Qt.red, 3))
            painter.setBrush(Qt.red)
            painter.drawEllipse(QPointF(sun_x, sun_y), 10, 10)

    def draw_clock_hands(self, painter):
        # Convert current time to angle on 24-hour clock (0° at top/north)
        # 24 hours maps to 360°, so each hour represents 15°
        total_seconds = self.now.hour * 3600 + self.now.minute * 60 + self.now.second
        day_seconds = 24 * 3600

        # Hour hand (shorter)
        hour_angle = (total_seconds / day_seconds) * 360 - 90  # -90 to make 0° at top
        self.draw_hand(painter, hour_angle, 80, 4)

        # Minute hand (longer)
        minute_angle = (self.now.minute / 60) * 360 - 90
        self.draw_hand(painter, minute_angle, 110, 3)

        # Second hand (longest, red)
        second_angle = (self.now.second / 60) * 360 - 90
        self.draw_hand(painter, second_angle, 140, 1, Qt.red)

    def draw_hand(self, painter, angle, length, width, color=Qt.black):
        # Calculate the end point for the hand
        end_point = QPointF(200 + length * math.cos(math.radians(angle)),
                            200 + length * math.sin(math.radians(angle)))

        # Draw the hand
        painter.setPen(QPen(color, width, Qt.SolidLine))
        painter.drawLine(QPoint(200, 200), QPoint(int(end_point.x()), int(end_point.y())))

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
