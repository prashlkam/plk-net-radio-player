import sys
import os
import datetime
import platform
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QListWidget, QListWidgetItem, QComboBox,
    QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont, QFontDatabase

# Try to import the VLC module
try:
    import vlc
except ImportError:
    print("VLC library not found.")
    print("Please install it using: pip install python-vlc")
    # You might also need to install the VLC media player application itself
    # on your system for the library to work.
    # For Windows/macOS, download from videolan.org.
    # For Linux, use your package manager (e.g., sudo apt-get install vlc).
    sys.exit(1)


class RadioApp(QMainWindow):
    """
    A Winamp-style internet radio player using PyQt6 and python-vlc.
    Supports streaming from Icecast/Shoutcast, genre-based playlists,
    and recording audio to MP3.
    """
    def __init__(self):
        super().__init__()

        # --- Station Data ---
        # A curated list of stream URLs categorized by genre.
        self.stations = {
            "Classic Rock": [
                ("Classic Rock Florida", "http://stream.abacast.net/playlist/classic-rock-florida-hd-48k.m3u"),
                ("Absolute Classic Rock", "http://icecast.timlradio.co.uk/ac-high.mp3"),
                ("Rock Antenne", "http://mp3.webradio.antenne.de:80/rockantenne/stream"),
            ],
            "80s Hits": [
                ("Absolute 80s", "http://icecast.timlradio.co.uk/a8-high.mp3"),
                ("80s80s", "http://80s80s.hoerradar.de/80s80s-mp3-128"),
                ("Awesome 80s", "https://streams.abidingradio.org/awesome80s"),
            ],
            "Jazz": [
                ("Jazz24", "https://jazz24.org/streams/high.m3u"),
                ("TSF Jazz", "http://tsfjazz.ice.infomaniak.ch/tsfjazz-high.mp3"),
                ("Swiss Jazz", "http://stream.srg-ssr.ch/m/rsj/mp3_128"),
            ],
            "Electronic / Chill": [
                ("SomaFM: Groove Salad", "http://ice.somafm.com/groovesalad-128-mp3"),
                ("SomaFM: Drone Zone", "http://ice.somafm.com/dronezone-128-mp3"),
                ("Radio Paradise (Mellow)", "http://stream.radioparadise.com/mellow-flac"),
            ],
            "Classical": [
                ("Linn Classical", "http://radio.linn.co.uk:8004/autodj"),
                ("Venice Classic Radio", "http://174.36.1.135:8006/stream"),
                ("Radio Swiss Classic", "http://stream.srg-ssr.ch/m/rsc_de/mp3_128"),
            ]
        }
        
        # --- VLC Setup ---
        self.instance = vlc.Instance("--no-xlib")
        self.player = self.instance.media_player_new()
        self.is_recording = False
        self.current_url = None
        self.current_station_name = None

        # --- UI Initialization ---
        self.setWindowTitle("PyRadio")
        self.setWindowIcon(self._get_app_icon())
        self.setGeometry(100, 100, 380, 520)
        self.setMinimumSize(380, 520)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_ui(main_layout)
        self._apply_stylesheet()

        # Timer to update UI elements like track info
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        self.load_genres()

    def _create_ui(self, main_layout):
        """Creates and arranges all UI widgets."""
        # --- Display Panel ---
        display_frame = QFrame()
        display_frame.setObjectName("displayFrame")
        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(10, 10, 10, 10)

        self.station_label = QLabel("Welcome to PyRadio")
        self.station_label.setObjectName("stationLabel")
        self.station_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.station_label.setWordWrap(True)

        self.track_label = QLabel("Select a station to begin")
        self.track_label.setObjectName("trackLabel")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label.setWordWrap(True)
        
        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        display_layout.addWidget(self.station_label)
        display_layout.addWidget(self.track_label)
        display_layout.addWidget(self.status_label)
        main_layout.addWidget(display_frame)

        # --- Controls Panel ---
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 10)

        # Playback buttons
        playback_layout = QHBoxLayout()
        self.play_pause_button = self._create_control_button("▶", self.toggle_play_pause, "Play/Pause")
        self.stop_button = self._create_control_button("■", self.stop_playback, "Stop")
        playback_layout.addWidget(self.play_pause_button)
        playback_layout.addWidget(self.stop_button)

        # Record button
        self.record_button = self._create_control_button("●", self.toggle_record, "Record")
        self.record_button.setObjectName("recordButton")
        playback_layout.addWidget(self.record_button)
        
        controls_layout.addLayout(playback_layout)

        # Volume slider
        volume_layout = QHBoxLayout()
        volume_icon = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.player.audio_set_volume(80)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_layout)
        main_layout.addWidget(controls_frame)

        # --- Playlist Panel ---
        playlist_frame = QFrame()
        playlist_frame.setObjectName("playlistFrame")
        playlist_layout = QVBoxLayout(playlist_frame)
        
        self.genre_combo = QComboBox()
        self.genre_combo.currentTextChanged.connect(self.populate_playlist)
        
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemClicked.connect(self.play_selected_station)
        
        playlist_layout.addWidget(self.genre_combo)
        playlist_layout.addWidget(self.playlist_widget)
        main_layout.addWidget(playlist_frame, 1) # Give playlist more stretch factor

    def _create_control_button(self, text, slot, tooltip):
        """Helper to create a styled QPushButton."""
        button = QPushButton(text)
        button.clicked.connect(slot)
        button.setToolTip(tooltip)
        button.setFixedSize(40, 40)
        button.setObjectName("controlButton")
        return button

    def load_genres(self):
        """Populates the genre dropdown."""
        self.genre_combo.addItems(sorted(self.stations.keys()))

    def populate_playlist(self, genre):
        """Fills the playlist widget with stations for the selected genre."""
        self.playlist_widget.clear()
        for name, url in self.stations.get(genre, []):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, url) # Store URL in the item
            self.playlist_widget.addItem(item)
            
    def play_selected_station(self, item):
        """Plays the station associated with the double-clicked item."""
        self.current_station_name = item.text()
        self.current_url = item.data(Qt.ItemDataRole.UserRole)
        
        if self.is_recording:
            self.stop_record()
            self.start_playback()
        else:
            self.start_playback()

    def start_playback(self, is_for_recording=False):
        """Starts media playback, optionally setting up for recording."""
        if not self.current_url:
            self.status_label.setText("No station selected")
            return

        media = self.instance.media_new(self.current_url)
        
        if is_for_recording:
            music_dir = self._get_music_folder()
            if not os.path.exists(music_dir):
                os.makedirs(music_dir)
            
            sanitized_name = "".join(x for x in self.current_station_name if x.isalnum())
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.record_path = os.path.join(music_dir, f"rec_{sanitized_name}_{timestamp}.mp3")

            # VLC sout string for transcoding to MP3
            sout = (f'#transcode{{acodec=mp3,ab=128,channels=2,samplerate=44100}}:'
                    f'standard{{access=file,mux=raw,dst="{self.record_path}"}}')
            media.add_option(f'sout={sout}')
        
        self.player.set_media(media)
        self.player.play()
        
        self.play_pause_button.setText("❚❚")
        self.station_label.setText(self.current_station_name)
        self.status_label.setText("Buffering...")
        
    def toggle_play_pause(self):
        """Toggles between play and pause states."""
        if self.player.is_playing():
            self.player.pause()
            self.play_pause_button.setText("▶")
        else:
            # If not playing, try to play the selected station
            selected_items = self.playlist_widget.selectedItems()
            if selected_items:
                self.play_selected_station(selected_items[0])
            elif self.current_url:
                # If no station is selected but there was a previous one, resume it
                self.player.play()
                self.play_pause_button.setText("❚❚")

    def stop_playback(self):
        """Stops the playback entirely."""
        if self.is_recording:
            self.stop_record()
        self.player.stop()
        self.play_pause_button.setText("▶")
        self.station_label.setText("Welcome to PyRadio")
        self.track_label.setText("Select a station to begin")
        self.status_label.setText("Stopped")

    def set_volume(self, value):
        """Sets the player volume."""
        self.player.audio_set_volume(value)

    def toggle_record(self):
        """Starts or stops recording the current stream."""
        if not self.player.is_playing() and not self.is_recording:
            self.status_label.setText("Cannot record: not playing.")
            return

        if self.is_recording:
            self.stop_record()
        else:
            self.start_record()

    def start_record(self):
        """Logic to begin the recording process."""
        self.is_recording = True
        self.record_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.record_button.setToolTip("Stop Recording")
        
        # Restart playback with recording options
        self.player.stop()
        self.start_playback(is_for_recording=True)
        self.status_label.setText("RECORDING...")

    def stop_record(self):
        """Logic to stop the recording process."""
        self.is_recording = False
        self.record_button.setStyleSheet("") # Revert to default style
        self.record_button.setToolTip("Record")

        # Restart playback without recording
        self.player.stop()
        self.start_playback() # Restart normally
        self.status_label.setText(f"Recording saved to Music folder")

    def update_ui(self):
        """Periodically updates the UI, especially track metadata."""
        if self.player.get_state() == vlc.State.Playing:
             if not self.is_recording:
                self.status_label.setText("Playing")
        
        media = self.player.get_media()
        if media:
            metadata = media.get_meta(vlc.Meta.NowPlaying)
            if metadata:
                self.track_label.setText(metadata)
            else:
                self.track_label.setText("...")

    def closeEvent(self, event):
        """Ensures the player is stopped on application exit."""
        self.stop_playback()
        self.player.release()
        self.instance.release()
        event.accept()

    def _get_music_folder(self):
        """Returns the default Music folder path for the current OS."""
        return os.path.join(os.path.expanduser('~'), 'Music')

    def _get_app_icon(self):
        """Creates a simple QIcon for the application."""
        # Using a unicode character as a fallback icon
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        font = QFont()
        font.setPointSize(24)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📻")
        painter.end()
        return QIcon(pixmap)

    def _apply_stylesheet(self):
        """Applies a Winamp-inspired stylesheet to the application."""
        # A custom font for the "digital" display
        font_id = QFontDatabase.addApplicationFontFromData(self._get_font_data())
        if font_id == -1:
            print("Failed to load custom font.")
            font_family = "Courier New"
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_family = font_families[0]
            else:
                print("Failed to get font family from loaded font.")
                font_family = "Courier New"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #333333;
            }}
            QFrame#displayFrame {{
                background-color: #111;
                border: 2px solid #555;
                border-radius: 5px;
                margin: 10px;
            }}
            QLabel#stationLabel, QLabel#trackLabel, QLabel#statusLabel {{
                color: #00FF00; /* Bright green */
                font-family: "{font_family}", "Courier New", monospace;
                font-size: 14px;
                font-weight: bold;
            }}
             QLabel#trackLabel {{
                font-size: 16px;
                min-height: 40px; /* Allow for two lines */
            }}
            QLabel#statusLabel {{
                color: #FFFF00; /* Yellow */
                font-size: 12px;
            }}
            QFrame#controlsFrame, QFrame#playlistFrame {{
                background-color: #444;
                border-top: 1px solid #666;
            }}
            QFrame#playlistFrame {{
                padding: 10px;
            }}
            QPushButton#controlButton {{
                background-color: #666;
                color: #EEE;
                border: 1px solid #888;
                border-radius: 20px; /* Circular buttons */
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton#controlButton:hover {{
                background-color: #777;
            }}
            QPushButton#controlButton:pressed {{
                background-color: #555;
            }}
            QPushButton#recordButton {{
                color: #e74c3c;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #555;
                height: 8px;
                background: #333;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #999;
                border: 1px solid #777;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QComboBox, QListWidget {{
                background-color: #222;
                color: #DDD;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QListWidget::item:hover {{
                background-color: #3e5a30; /* Dark green selection */
            }}
            QListWidget::item:selected {{
                background-color: #5c8a48; /* Lighter green selection */
            }}
        """)
        
    def _get_font_data(self):
        """Returns the raw data for a retro digital font (base64 encoded)."""
        # This avoids needing a separate font file.
        # Digital-7 (Mono) by Sizenko Alexander
        # http://www.styleseven.com
        import base64
        return base64.b64decode(b'AAEAAAALAIAAAwAwT1MvMggi/dUAAAC8AAAAYGNtYXABDQDNAAACNAAAAGxnYXNwAAAAEAAAAugAAAAIZ2x5ZgscV9gAAALwAAABHGhlYWQG41YJAAABMAAAADZoaGVhA+IB6QAAAVQAAAAkaG10eAoAAEAAAAABZAAAACRsb2NhAKgDNQAAAnQAAAAMbWF4cAAUANQAAAFoAAAAIG5hbWU9wjpWAAAC7AAAAlBwb3N0/5QA3gAAAXgAAAAgAAEAAAABAAAAAAAAAAMAAAADAAAAHAABAAAAAABMAAQAAQAAAAAAAgAAAAAAAQAAAAMAAwAAAAsAAABMAQUAAQAAABoABAAQAAAAEABIAAIAAAAEACIAAQAAAAQAIAAFAAEAAAABAAYABgABAAAAAAEAIAAHAAEAAAABAAgACAABAAAAAAEAJAABAAEAAAAFAAEAEgABAAAABAACABAAAgAAAAMARABpAGcAaQB0AGEAbAAtADcAIABNAG8AbgBvAAAAUgBlAGcAdQBsAGEAcgAAAEQAaQBnAGkAdABhAGwALQA3ACAATQBvAG4AbwAAAAAA')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RadioApp()
    window.show()
    sys.exit(app.exec())

