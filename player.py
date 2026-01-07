import os
import random
import time
import re
from subprocess import Popen

directory = '/video'

videos = []


def extract_season_episode(filename):
    """Extract season and episode numbers from filename.
    Returns (season, episode) tuple or (999999, 999999) if not found."""
    # Match patterns like S01E01, S1E1, s01e01, etc.
    match = re.search(r'[Ss](\d+)[Ee](\d+)', filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    # Return high numbers if no match found (so they appear at the end)
    return (999999, 999999)


def getVideos():
    global videos
    videos = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.mp4'):
                full_path = os.path.join(root, filename)
                videos.append(full_path)

    # Sort videos by season and episode number
    videos.sort(key=lambda x: extract_season_episode(os.path.basename(x)))


def playVideos():
    global videos
    if len(videos) == 0:
        getVideos()
        time.sleep(5)
        return

    # Don't shuffle - play in order
    # random.shuffle(videos)

    # MPV command with socket interface for touch controls
    mpv_command = [
        'mpv',
        '--input-ipc-server=/tmp/mpvsocket',  # Enable socket for touch.py
        '--video-rotate=270',
        '--fullscreen',
        '--osd-duration=5000',
        '--osd-font-size=30',
        '--osd-playing-msg=${filename/no-ext}',
        '--osd-on-seek=msg-bar',
        '--loop-playlist=inf',  # Loop the entire playlist
        '--no-terminal',  # Don't clutter terminal output
        '--autocreate-playlist=same',
        '--directory-mode=recursive',
        '--save-position-on-quit',
        directory
    ]
    #] + videos
    playProcess = Popen(mpv_command)
    playProcess.wait()

while True:
    playVideos()
