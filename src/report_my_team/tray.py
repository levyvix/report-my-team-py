import ctypes
import logging
import os
import threading
from collections.abc import Callable
from ctypes import wintypes

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _create_icon_image() -> Image.Image:
    """Create a 64x64 PIL image with a red circle as the tray icon."""
    image = Image.new("RGB", (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill=(220, 50, 50))
    return image


def _monitor_minimize(hwnd: int, on_minimize: Callable[[], None]) -> None:
    """Poll every 100ms for console window minimize state.

    When minimized, call on_minimize() to hide the console.
    Runs in a daemon thread.
    """
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    is_iconic = user32.IsIconic
    is_iconic.argtypes = [wintypes.HWND]
    is_iconic.restype = wintypes.BOOL

    was_iconic = False
    while True:
        try:
            is_min = is_iconic(hwnd)
            if is_min and not was_iconic:
                on_minimize()
            was_iconic = is_min
            threading.Event().wait(0.1)
        except Exception as e:
            logger.debug("Minimize monitor error: %s", e)


def run_tray() -> None:
    """Run the system tray icon and menu.

    Blocks the main thread (required by pystray on Windows).
    """
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    get_console_window = kernel32.GetConsoleWindow
    get_console_window.restype = wintypes.HWND
    hwnd = get_console_window()

    show_window = user32.ShowWindow
    show_window.argtypes = [wintypes.HWND, wintypes.INT]
    set_foreground = user32.SetForegroundWindow
    set_foreground.argtypes = [wintypes.HWND]
    set_active = user32.SetActiveWindow
    set_active.argtypes = [wintypes.HWND]

    SW_HIDE = 0
    SW_RESTORE = 9

    def on_minimize():
        """Hide the console window when minimize is detected."""
        show_window(hwnd, SW_HIDE)
        logger.debug("Console hidden to tray")

    def show_action(_):
        """Restore and focus the console window."""
        show_window(hwnd, SW_RESTORE)
        set_active(hwnd)
        set_foreground(hwnd)
        logger.debug("Console restored from tray")

    def exit_action(_):
        """Exit the application."""
        icon.stop()
        os._exit(0)

    # Start minimize monitor thread
    monitor_thread = threading.Thread(target=_monitor_minimize, args=(hwnd, on_minimize), daemon=True)
    monitor_thread.start()
    logger.debug("Minimize monitor thread started")

    # Create tray menu
    menu = pystray.Menu(
        pystray.MenuItem("Show", show_action),
        pystray.MenuItem("Exit", exit_action),
    )

    # Create and run tray icon (blocks until stopped)
    icon = pystray.Icon(
        name="report-my-team",
        title="Report My Team",
        icon=_create_icon_image(),
        menu=menu,
    )
    logger.info("System tray icon started")
    icon.run()
