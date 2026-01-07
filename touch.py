#!/usr/bin/python3

import evdev
import logging
import socket
import os
import sys

# This is oddly swapped. X is actually the long dimension on the physical screen.
MAX_X = 480
MAX_Y = 640

# Defines left/right touch area
X_MARGIN = 100
Y_MARGIN = 100
# How far to seek fwd/back
SEEK_SECS = 30

# Must match MPV's --input-ipc-server flag
SOCKET_PATH = "/tmp/mpvsocket"


def SendMPV(msg: str):
    logging.info("MPV command: %s", msg)
    msg += "\n"
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(SOCKET_PATH)
        sent = client.send(msg.encode())
        response = client.recv(4096)
        logging.info(f"Received response: {response.decode().strip()}")
        client.close()
    except socket.timeout:
        logging.error(f"Socket timeout connecting to {SOCKET_PATH}")
    except FileNotFoundError:
        logging.error(f"MPV socket not found at {SOCKET_PATH}. Is MPV running with --input-ipc-server?")
    except Exception as e:
        logging.error(f"Error communicating with MPV: {e}")


# Commands here: https://mpv.io/manual/master/#json-ipc
def Act(x: int, y: int, delta_x: int, delta_y: int):
    # Swipe left
    if delta_x < -(MAX_X / 2):
        SendMPV("playlist-next")
    # Swipe right
    elif delta_x > MAX_X / 2:
        SendMPV("playlist-prev")
    # Bottom Touch
    elif y < Y_MARGIN:
        SendMPV("playlist-next-playlist")
    # Top Touch
    elif y > MAX_Y - Y_MARGIN:
        SendMPV("playlist-prev-playlist")
    # Left touch
    elif x < X_MARGIN:
        SendMPV(f"seek {0-SEEK_SECS}")
    # Middle touch
    elif x > MAX_X - X_MARGIN:
        SendMPV(f"seek {SEEK_SECS}")
    # Right touch
    else:
        SendMPV("cycle pause")


def find_touch_device():
    """Find the touchscreen input device."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    for device in devices:
        # Look for devices with absolute X/Y axes (touchscreens)
        caps = device.capabilities()
        if evdev.ecodes.EV_ABS in caps:
            abs_events = caps[evdev.ecodes.EV_ABS]
            # Check if it has both X and Y multitouch axes
            has_mt_x = any(evdev.ecodes.ABS_MT_POSITION_X in event for event in abs_events)
            has_mt_y = any(evdev.ecodes.ABS_MT_POSITION_Y in event for event in abs_events)
            
            if has_mt_x and has_mt_y:
                logging.info(f"Found touchscreen: {device.name} at {device.path}")
                return device.path
    
    # Fallback to /dev/input/event0
    logging.warning("Could not auto-detect touchscreen, defaulting to /dev/input/event0")
    return "/dev/input/event0"


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Check if user is in input group
    if not os.access("/dev/input/event0", os.R_OK):
        logging.error("ERROR: No read access to /dev/input/event0")
        logging.error("Please run: sudo usermod -a -G input admin")
        logging.error("Then log out and log back in.")
        sys.exit(1)
    
    device_path = find_touch_device()
    
    try:
        device = evdev.InputDevice(device_path)
    except PermissionError:
        logging.error(f"Permission denied accessing {device_path}")
        logging.error("Please run: sudo usermod -a -G input admin")
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"Device not found: {device_path}")
        sys.exit(1)
    
    logging.info("Input device: %s", device)

    # Key event comes before location event. So assume first key down is in middle of screen
    x = int(MAX_X / 2)
    y = int(MAX_Y / 2)

    down_x = None
    down_y = None

    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            if event.code == evdev.ecodes.BTN_TOUCH:
                if event.value == 0x0:
                    delta_x = x - down_x
                    delta_y = y - down_y
                    Act(x, y, delta_x, delta_y)
                if event.value == 0x1:
                    down_x = x
                    down_y = y
        elif event.type == evdev.ecodes.EV_ABS:
            # Screen is rotated, so X & Y are swapped from how the input reports them.
            if event.code == evdev.ecodes.ABS_MT_POSITION_X:
                y = MAX_Y - event.value
            elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                x = MAX_X - event.value


if __name__ == "__main__":
    main()
