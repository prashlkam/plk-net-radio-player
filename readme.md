Python Internet Radio Player

A full-featured internet radio player built with Python and PyQt6, featuring a classic, Winamp-inspired user interface. This application allows you to browse stations by genre, play Icecast and Shoutcast streams, and record your favorite broadcasts directly to your local Music folder as MP3 files.
Features

    Classic Winamp-style UI: A nostalgic, compact, and easy-to-use interface.

    Cross-Platform: Runs on Windows, macOS, and Linux.

    Genre-Based Playlists: Comes with a curated list of stations sorted by popular genres like Classic Rock, Jazz, 80s Hits, and more.

    Icecast & Shoutcast Support: Powered by the robust VLC media engine, it can play a wide variety of internet radio streams.

    Metadata Display: Shows the current station and song title (when provided by the stream).

    MP3 Recording: Record any live stream with a single click and save it as an MP3 file in your system's Music folder.

Requirements

Before you begin, ensure you have the following installed on your system:

    Python 3.6+

    VLC Media Player: The application requires the core VLC engine to be installed.

        Windows/macOS: Download from the VideoLAN website.

        Linux (Debian/Ubuntu): sudo apt-get install vlc

        Linux (Fedora): sudo dnf install vlc

    Python Packages: The necessary Python libraries are listed in requirements.txt.

Installation & Usage

    Clone the repository or download the files:

    git clone <repository_url>
    cd python-internet-radio

    Or simply download internet_radio.py and requirements.txt into a new folder.

    Create a virtual environment (recommended):

    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    Install the required Python packages:

    pip install -r requirements.txt

    Run the application:

    python internet_radio.py

How to Use

    Select a Genre: Use the dropdown menu at the top of the playlist to choose a genre.

    Choose a Station: The list below the dropdown will populate with stations. Double-click a station to start playing.

    Control Playback: Use the Play/Pause (▶/❚❚) and Stop (■) buttons.

    Adjust Volume: Use the horizontal slider to control the volume.

    Record a Stream: While a station is playing, click the Record (●) button to start saving the audio. The button will turn red. Click it again to stop recording. The MP3 file will be named with the station and a timestamp and saved to your default Music folder.

License

This project is licensed under the MIT License. See the LICENSE file for details.
