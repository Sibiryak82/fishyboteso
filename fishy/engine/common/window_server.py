import logging
import math
import traceback
from enum import Enum
from threading import Thread

import cv2
import numpy as np
import pywintypes
import win32gui
from PIL import ImageGrab
from win32api import GetSystemMetrics

from fishy.helper.config import config


class Status(Enum):
    CRASHED = -1
    STOPPED = 0
    RUNNING = 1


class WindowServer:
    """
    Records the game window, and allows to create instance to process it
    """
    Screen = None
    windowOffset = None
    hwnd = None
    status = Status.STOPPED


def init():
    """
    Executed once before the main loop,
    Finds the game window, and calculates the offset to remove the title bar
    """
    try:
        WindowServer.hwnd = win32gui.FindWindow(None, "Elder Scrolls Online")
        rect = win32gui.GetWindowRect(WindowServer.hwnd)
        client_rect = win32gui.GetClientRect(WindowServer.hwnd)
        WindowServer.windowOffset = math.floor(((rect[2] - rect[0]) - client_rect[2]) / 2)
        WindowServer.status = Status.RUNNING
    except pywintypes.error:
        logging.error("Game window not found")
        WindowServer.status = Status.CRASHED


def loop():
    """
    Executed in the start of the main loop
    finds the game window location and captures it
    """
    bbox = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

    temp_screen = np.array(ImageGrab.grab(bbox=bbox))

    rect = win32gui.GetWindowRect(WindowServer.hwnd)
    client_rect = win32gui.GetClientRect(WindowServer.hwnd)

    fullscreen = GetSystemMetrics(1) == (rect[3] - rect[1])
    titleOffset = ((rect[3] - rect[1]) - client_rect[3]) - WindowServer.windowOffset if not fullscreen else 0

    crop = (
        rect[0] + WindowServer.windowOffset, rect[1] + titleOffset, rect[2] - WindowServer.windowOffset,
        rect[3] - WindowServer.windowOffset)

    WindowServer.Screen = temp_screen[crop[1]:crop[3], crop[0]:crop[2]]

    if WindowServer.Screen.size == 0:
        logging.error("Don't minimize or drag game window outside the screen")
        WindowServer.status = Status.CRASHED


def loop_end():
    cv2.waitKey(25)


# noinspection PyBroadException
def run():
    # todo use config
    while WindowServer.status == Status.RUNNING:
        try:
            loop()
        except Exception:
            traceback.print_exc()
            WindowServer.status = Status.CRASHED
    loop_end()


def start():
    if WindowServer.status == Status.RUNNING:
        return

    init()
    if WindowServer.status == Status.RUNNING:
        Thread(target=run).start()


def screen_ready():
    return WindowServer.Screen is not None or WindowServer.status == Status.CRASHED


def stop():
    WindowServer.status = Status.STOPPED
