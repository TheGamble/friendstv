#!/usr/bin/python3

import logging
from gpiozero import Button
import time
import os
import socket
import sys

# GPIO pin assignments (BCM numbering - same as original)
BUTTON_PIN = 26

button = Button(BUTTON_PIN, pull_up=True)
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

def turnOnScreen():
    logging.info("turnOnScreen")
    # Turn on screen backlight
    os.system("pinctrl set 18 op dh")
    # Pause MPV
    SendMPV("set pause no")

def turnOffScreen():
    logging.info("turnOffScreen")
    # Turn off screen backlight
    os.system("pinctrl set 18 op dl")
    # Resume MPV
    SendMPV("set pause yes")

def main():
    global button_line, backlight_line

    logging.getLogger().setLevel(logging.INFO)

    turnOffScreen()
    screen_on = False

    try:
        while True:
            if button.is_pressed:
                if screen_on == False:
                    turnOnScreen()
                    screen_on = True
            else:
                if screen_on == True:
                    turnOffScreen()
                    screen_on = False
            time.sleep(0.3)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        button.close()

if __name__ == "__main__":
    main()
