import sys
import json
from datetime import timedelta
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QDialog, QPushButton
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFontMetrics
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

config = load_config()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config['client_id'],
    client_secret=config['client_secret'],
    redirect_uri=config['redirect_uri'],
    scope="user-read-playback-state",
    cache_path='login.json'))

def ms_to_minutes_seconds(ms):
    return str(timedelta(milliseconds=ms)).split(".")[0][2:]

def get_current_track():
    current_track = sp.current_playback()

    if current_track is not None and current_track['is_playing']:
        track = current_track['item']
        artist = track['artists'][0]['name']
        track_name = track['name']
        progress_ms = current_track['progress_ms']
        duration_ms = track['duration_ms']

        progress_time = ms_to_minutes_seconds(progress_ms)
        total_time = ms_to_minutes_seconds(duration_ms)

        return {
            "track_name": track_name,
            "artist": artist,
            "progress_ms": progress_ms,
            "duration_ms": duration_ms,
            "progress_time": progress_time,
            "total_time": total_time
        }
    else:
        return None

class PositionSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select Position")
        self.setGeometry(100, 100, 200, 150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("Select the position for the overlay:", self)
        layout.addWidget(self.label)

        self.buttons = {
            "Top Left": (0, 0),
            "Top Right": (1, 0),
            "Top Center": (0.5, 0),
            "Center": (0.5, 0.5),
            "Bottom Left": (0, 1),
            "Bottom Right": (1, 1),
            "Bottom Center": (0.5, 1)
        }

        for text, pos in self.buttons.items():
            button = QPushButton(text, self)
            button.clicked.connect(lambda checked, pos=pos: self.accept_position(pos))
            layout.addWidget(button)

    def accept_position(self, pos):
        self.selected_position = pos
        self.accept()

    def get_position(self):
        return getattr(self, 'selected_position', (0, 0))

class NowPlayingOverlay(QMainWindow):
    def __init__(self, position):
        super().__init__()

        self.setWindowTitle("Now Playing")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)  # Fully transparent

        # Create the layout and widgets
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.track_label = QLabel("", self)
        self.track_label.setStyleSheet("font-size: 20px; color: white;")
        self.layout.addWidget(self.track_label)

        self.progress_label = QLabel("", self)
        self.progress_label.setStyleSheet("font-size: 16px; color: white;")
        self.layout.addWidget(self.progress_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_track_info)
        self.timer.start(500)  # Update every 500 ms

        self.current_position = position 
        self.update_track_info()  # Initial update
        self.set_position(self.current_position)

    def update_track_info(self):
        current_track = get_current_track()

        if current_track is not None:
            track_name = f"{current_track['track_name']}"
            progress = f"{current_track['progress_time']} / {current_track['total_time']}"

            self.track_label.setText(track_name)
            self.progress_label.setText(progress)
        else:
            self.track_label.setText("No track currently playing")
            self.progress_label.setText("")

        # Adjust the window size based on the content
        self.adjust_size()

    def adjust_size(self):
        font_metrics = QFontMetrics(self.track_label.font())
        track_name_width = font_metrics.boundingRect(self.track_label.text()).width()
        progress_width = font_metrics.boundingRect(self.progress_label.text()).width()

        # Add some padding to avoid cutting off text
        padding = 20
        width = max(track_name_width, progress_width) + padding
        height = 100

        # Avoid resizing if the new size is the same as the current size
        if self.width() != width or self.height() != height:
            self.setFixedSize(width, height)
            # Ensure the window is repositioned after resizing
            self.set_position(self.current_position)

    def set_position(self, position):
        self.current_position = position  # Update current_position
        screen_geometry = QApplication.primaryScreen().geometry()
        width, height = self.width(), self.height()
        x, y = position

        if x == 0:  # Left
            x_pos = 0
        elif x == 1:  # Right
            x_pos = screen_geometry.width() - width
        else:  # Center
            x_pos = (screen_geometry.width() - width) // 2

        if y == 0:  # Top
            y_pos = 0
        elif y == 1:  # Bottom
            y_pos = screen_geometry.height() - height
        else:  # Center
            y_pos = (screen_geometry.height() - height) // 2

        self.move(x_pos, y_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = PositionSelector()
    if dialog.exec_() == QDialog.Accepted:
        position = dialog.get_position()
        overlay = NowPlayingOverlay(position)
        overlay.show()
        sys.exit(app.exec_())
