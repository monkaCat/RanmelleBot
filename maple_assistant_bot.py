"""
MeowMeowBot

Desktop automation helper for private MapleStory servers where macroing is allowed.

Install runtime dependencies in your own Python environment:
    pip install pyautogui pillow opencv-python numpy pytesseract

Optional:
    Install Tesseract OCR for Windows and set its path in the Settings tab.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import traceback
import ctypes
from ctypes import wintypes
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import pyautogui
except Exception:  # pragma: no cover - shown in GUI at runtime
    pyautogui = None

try:
    import keyboard
except Exception:  # pragma: no cover
    keyboard = None

try:
    import win32gui
except Exception:  # pragma: no cover
    win32gui = None

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    from PIL import Image, ImageGrab
except Exception:  # pragma: no cover
    Image = None
    ImageGrab = None


APP_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = APP_DIR / "meowmeowbot_config.json"
EVENT_LOG = APP_DIR / "log.txt"
REQUIRED_GAME_WINDOW = "Ranmelle"
APP_VERSION = "2026-06-15-low-latency-attack-v13"

UI_BG = "#080414"
UI_BG_2 = "#0f0a24"
UI_PANEL = "#171a46"
UI_PANEL_2 = "#20245c"
UI_PANEL_DARK = "#101238"
UI_TEXT = "#ffffff"
UI_MUTED = "#b8b7d8"
UI_PINK = "#d82b75"
UI_PINK_DARK = "#a81f5d"
UI_PURPLE = "#7c3aed"
UI_CYAN = "#38d7ff"
UI_GREEN = "#a3ff12"
UI_RED = "#ff355d"
UI_YELLOW = "#ffd447"
UI_ORANGE = "#ffb020"

if os.name == "nt":
    try:
        console = ctypes.windll.kernel32.GetConsoleWindow()
        if console:
            ctypes.windll.user32.ShowWindow(console, 0)
    except Exception:
        pass

DEFAULT_IMAGES = {
    "hot_time": str(APP_DIR / "Detections" / "detector1.png"),
    "cookbot": str(APP_DIR / "Detections" / "cockbot.png"),
    "finish": str(APP_DIR / "Detections" / "finish.png"),
    "dead": str(APP_DIR / "Detections" / "dead.png"),
    "char": str(APP_DIR / "Detections" / "ref_char.png"),
    "henesys": str(APP_DIR / "Detections" / "henesys.png"),
}

LEGACY_DUNGEON_DIALOG_STEPS = "wait:1\npress:enter"

KEY_OPTIONS = [
    "ctrl", "shift", "alt", "space", "enter", "esc", "tab", "backspace",
    "end", "home", "insert", "delete", "pageup", "pagedown",
    "up", "down", "left", "right",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "num0", "num1", "num2", "num3", "num4", "num5", "num6", "num7", "num8", "num9",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
]

MODE_OPTIONS = ["Farming", "Dungeon"]
KEYBOARD_LAYOUTS = ["DE", "US", "UK"]
OCR_ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
OCR_MIN_LENGTH = 6
OCR_MAX_LENGTH = 17
OCR_REJECT_KEYWORDS = (
    "SAVE", "DEFAULT", "SAVEDEFAULT", "START", "STOP", "BOT", "MEOW", "RANMELLE",
    "WINDOW", "CONFIG", "CURSOR", "DETECTOR", "DUNGEON", "HENESYS", "ATTACK",
    "BUFF", "SKILL", "PROFILE", "CONTROL", "OCR", "ENTERX2",
)
COOKBOT_CODE_OFFSET = (92, -47, 220, 24)
COOKBOT_INPUT_OFFSET = (164, -16)
COOKBOT_RESULT_OFFSET = (156, -74, 360, 82)
COOKBOT_CODE_SEARCH_OFFSET = (100, -88, 430, 92)

VK_CODES = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
}

for digit in "0123456789":
    VK_CODES[digit] = ord(digit)
for letter in "abcdefghijklmnopqrstuvwxyz":
    VK_CODES[letter] = ord(letter.upper())
for index in range(1, 13):
    VK_CODES[f"f{index}"] = 0x70 + index - 1
for index in range(10):
    VK_CODES[f"num{index}"] = 0x60 + index

PY_AUTO_GUI_KEY_MAP = {
    "control": "ctrl",
    "ctrl": "ctrl",
    "escape": "esc",
    "esc": "esc",
    "pgup": "pageup",
    "pgdn": "pagedown",
    "del": "delete",
    "ins": "insert",
    "return": "enter",
    "num0": "num0",
    "num1": "num1",
    "num2": "num2",
    "num3": "num3",
    "num4": "num4",
    "num5": "num5",
    "num6": "num6",
    "num7": "num7",
    "num8": "num8",
    "num9": "num9",
}


def now_ms() -> int:
    return int(time.monotonic() * 1000)


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def normalize_key(value: str) -> str:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    value = value.lower()
    return PY_AUTO_GUI_KEY_MAP.get(value, value)


def clean_ocr_text(text: str) -> str:
    return "".join(ch for ch in text.strip() if ch in OCR_ALLOWED_CHARS)


def validate_ld_code(text: str) -> tuple[bool, str]:
    if not (OCR_MIN_LENGTH <= len(text) <= OCR_MAX_LENGTH):
        return False, f"length {len(text)}, expected {OCR_MIN_LENGTH}-{OCR_MAX_LENGTH}"
    upper = text.upper()
    for keyword in OCR_REJECT_KEYWORDS:
        if keyword in upper:
            return False, f"contains UI keyword {keyword}"
    return True, "ok"


def is_valid_ld_code(text: str) -> bool:
    return validate_ld_code(text)[0]


def score_ld_code_candidate(text: str) -> int:
    valid, _ = validate_ld_code(text)
    if not valid:
        return -1000
    score = 100
    score -= abs(len(text) - 10) * 5
    if 8 <= len(text) <= 12:
        score += 18
    if 14 <= len(text):
        score -= 20
    if any(ch.isdigit() for ch in text):
        score += 4
    if any(ch.islower() for ch in text) and any(ch.isupper() for ch in text):
        score += 8
    lower = text.lower()
    for char in OCR_ALLOWED_CHARS.lower():
        if char * 3 in lower:
            score -= 18
    longest_run = 1
    current_run = 1
    for previous, current in zip(lower, lower[1:]):
        if previous == current:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 1
    score -= max(0, longest_run - 2) * 10
    return score


def append_event_log(text: str) -> None:
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(EVENT_LOG, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {text}\n")
    except Exception:
        pass


def resolve_template_path(template_path: str) -> str:
    if not template_path:
        return ""
    if os.path.exists(template_path):
        return template_path
    local = APP_DIR / "Detections" / Path(template_path).name
    if local.exists():
        return str(local)
    return template_path


def is_running_as_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_hotkey_pressed(key: str) -> bool:
    key = normalize_key(key)
    vk = VK_CODES.get(key)
    if vk is None or os.name != "nt":
        return False
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def send_virtual_key(key: str, hold_seconds: float = 0.065) -> bool:
    key = normalize_key(key)
    vk = VK_CODES.get(key)
    if vk is None or os.name != "nt":
        return False
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    INPUT_KEYBOARD = 1
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    if not scan:
        return False
    flags = KEYEVENTF_SCANCODE
    if key in {"up", "down", "left", "right", "insert", "delete", "home", "end", "pageup", "pagedown"}:
        flags |= KEYEVENTF_EXTENDEDKEY

    class KeyBdInput(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_void_p),
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [("ki", KeyBdInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", InputUnion)]

    def send_scan(scan_flags: int) -> bool:
        event = Input(type=INPUT_KEYBOARD, union=InputUnion(ki=KeyBdInput(0, scan, scan_flags, 0, None)))
        return ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) == 1

    if send_scan(flags):
        time.sleep(hold_seconds)
        if send_scan(flags | KEYEVENTF_KEYUP):
            return True

    ctypes.windll.user32.keybd_event(vk, scan, flags, 0)
    time.sleep(hold_seconds)
    ctypes.windll.user32.keybd_event(vk, scan, flags | KEYEVENTF_KEYUP, 0)
    return True


def send_virtual_key_down(key: str) -> bool:
    key = normalize_key(key)
    vk = VK_CODES.get(key)
    if vk is None or os.name != "nt":
        return False
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_SCANCODE = 0x0008
    INPUT_KEYBOARD = 1
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE if scan else 0
    if key in {"up", "down", "left", "right", "insert", "delete", "home", "end", "pageup", "pagedown"}:
        flags |= KEYEVENTF_EXTENDEDKEY

    class KeyBdInput(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_void_p),
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [("ki", KeyBdInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", InputUnion)]

    event = Input(type=INPUT_KEYBOARD, union=InputUnion(ki=KeyBdInput(0 if scan else vk, scan, flags, 0, None)))
    if ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) == 1:
        return True
    ctypes.windll.user32.keybd_event(0 if scan else vk, scan, flags, 0)
    return True


def send_virtual_key_up(key: str) -> bool:
    key = normalize_key(key)
    vk = VK_CODES.get(key)
    if vk is None or os.name != "nt":
        return False
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_SCANCODE = 0x0008
    INPUT_KEYBOARD = 1
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_KEYUP | (KEYEVENTF_SCANCODE if scan else 0)
    if key in {"up", "down", "left", "right", "insert", "delete", "home", "end", "pageup", "pagedown"}:
        flags |= KEYEVENTF_EXTENDEDKEY

    class KeyBdInput(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_void_p),
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [("ki", KeyBdInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", InputUnion)]

    event = Input(type=INPUT_KEYBOARD, union=InputUnion(ki=KeyBdInput(0 if scan else vk, scan, flags, 0, None)))
    if ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) == 1:
        return True
    ctypes.windll.user32.keybd_event(0 if scan else vk, scan, flags, 0)
    return True


def send_key_combo(*keys: str) -> bool:
    normalized = [normalize_key(key) for key in keys]
    vks = [VK_CODES.get(key) for key in normalized]
    if any(vk is None for vk in vks) or os.name != "nt":
        return False
    KEYEVENTF_KEYUP = 0x0002
    for vk in vks:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.025)
    for vk in reversed(vks):
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.025)
    return True


def release_virtual_key(key: str) -> None:
    send_virtual_key_up(key)


def release_modifiers() -> None:
    for key in ("ctrl", "shift", "alt"):
        release_virtual_key(key)


def force_foreground_window(hwnd: int) -> bool:
    if os.name != "nt" or not hwnd:
        return False
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        current_thread = kernel32.GetCurrentThreadId()
        foreground = user32.GetForegroundWindow()
        foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        if foreground_thread:
            user32.AttachThreadInput(current_thread, foreground_thread, True)
        if target_thread:
            user32.AttachThreadInput(current_thread, target_thread, True)
        try:
            user32.ShowWindow(hwnd, 5)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            return True
        finally:
            if target_thread:
                user32.AttachThreadInput(current_thread, target_thread, False)
            if foreground_thread:
                user32.AttachThreadInput(current_thread, foreground_thread, False)
    except Exception:
        return False


def set_windows_clipboard_text(text: str) -> bool:
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        data = text.encode("utf-16-le") + b"\x00\x00"
        GMEM_MOVEABLE = 0x0002
        CF_UNICODETEXT = 13
        if not user32.OpenClipboard(None):
            return False
        try:
            user32.EmptyClipboard()
            handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not handle:
                return False
            locked = kernel32.GlobalLock(handle)
            if not locked:
                kernel32.GlobalFree(handle)
                return False
            ctypes.memmove(locked, data, len(data))
            kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                kernel32.GlobalFree(handle)
                return False
            return True
        finally:
            user32.CloseClipboard()
    except Exception:
        return False


@dataclass
class SkillConfig:
    enabled: bool = False
    name: str = "Skill"
    key: str = ""
    interval_ms: int = 3000
    cast_pause_ms: int = 250
    taps: int = 1


@dataclass
class DetectorConfig:
    enabled: bool = False
    name: str = "Detector"
    mode: str = "Farming"
    image: str = ""
    confidence: float = 0.80
    action: str = "Press Enter"
    custom_key: str = "enter"
    cooldown_ms: int = 1500


@dataclass
class OcrConfig:
    enabled: bool = False
    popup_image: str = DEFAULT_IMAGES["cookbot"]
    popup_confidence: float = 0.75
    relative_to_popup: bool = False
    cookbot_label_preset: bool = True
    check_interval_ms: int = 5000
    region_x: int = 0
    region_y: int = 0
    region_w: int = 240
    region_h: int = 32
    input_x: int = 0
    input_y: int = 0
    result_x: int = 0
    result_y: int = 0
    result_w: int = 360
    result_h: int = 90
    max_attempts: int = 3
    max_failures: int = 2
    popup_settle_delay_ms: int = 3000
    retry_delay_ms: int = 1500
    result_delay_ms: int = 800
    tesseract_path: str = ""


@dataclass
class DungeonConfig:
    enabled: bool = False
    role: str = "Leader"
    drop_option: str = "4 drops"
    custom_coins: int = 1
    npc_image: str = DEFAULT_IMAGES["henesys"]
    finish_image: str = DEFAULT_IMAGES["finish"]
    char_image: str = DEFAULT_IMAGES["char"]
    portal_image: str = ""
    confidence: float = 0.80
    playfield_x: int = 0
    playfield_y: int = 0
    playfield_w: int = 0
    playfield_h: int = 0
    minimap_x: int = 0
    minimap_y: int = 0
    minimap_w: int = 0
    minimap_h: int = 0
    home_x: int = 0
    home_y: int = 0
    tolerance_px: int = 12
    npc_offset_x: int = 10
    npc_offset_y: int = 10
    portal_offset_x: int = 0
    portal_offset_y: int = 0
    portal_x: int = 0
    portal_y: int = 0
    death_ok_x: int = 0
    death_ok_y: int = 0
    henesys_wait_after_exit_sec: int = 10
    dialog_steps: str = ""
    return_home_every_ms: int = 750


@dataclass
class BotConfig:
    mode: str = "Farming"
    game_window: str = "Ranmelle"
    keyboard_layout: str = "DE"
    start_hotkey: str = "f1"
    stop_hotkey: str = "f2"
    mouse_hotkey: str = "f3"
    attack_enabled: bool = True
    attack_key: str = "ctrl"
    attack_delay_ms: int = 250
    command_enabled: bool = False
    command_text: str = "@useallbuffitems"
    command_every_sec: int = 360
    command_step_delay_ms: int = 250
    skills: list[SkillConfig] = field(default_factory=list)
    detectors: list[DetectorConfig] = field(default_factory=list)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    dungeon: DungeonConfig = field(default_factory=DungeonConfig)


def default_config() -> BotConfig:
    skills = [
        SkillConfig(True, "Buff", "1", 3000, 650, 2),
        SkillConfig(False, "Skill 2", "end", 3000, 300),
        SkillConfig(False, "Skill 3", "", 10000, 300),
        SkillConfig(False, "Skill 4", "", 15000, 300),
        SkillConfig(False, "Skill 5", "", 20000, 300),
        SkillConfig(False, "Skill 6", "", 30000, 300),
        SkillConfig(False, "Skill 7", "", 30000, 300),
        SkillConfig(False, "Skill 8", "", 30000, 300),
    ]
    detectors = [
        DetectorConfig(True, "Hot Time", "Farming", DEFAULT_IMAGES["hot_time"], 0.80, "Press Enter", "enter", 3000),
        DetectorConfig(True, "Death Dialog", "Dungeon", DEFAULT_IMAGES["dead"], 0.80, "Click Death OK", "space", 3000),
        DetectorConfig(False, "Farming Detector", "Farming", "", 0.80, "Click Image", "enter", 1500),
        DetectorConfig(False, "Dungeon Detector", "Dungeon", "", 0.80, "Click Image", "enter", 1500),
    ]
    return BotConfig(skills=skills, detectors=detectors)


class AutomationBackend:
    def __init__(self, log: Callable[[str], None]) -> None:
        self.log = log
        self.stop_event = threading.Event()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_skill: dict[str, int] = {}
        self.last_detector: dict[str, int] = {}
        self.last_command = 0
        self.last_home_return = 0
        self.finish_handled = False
        self.target_hwnd: Optional[int] = None
        self.ocr_last_answer = ""
        self.ocr_attempt_count = 0
        self.ocr_failure_count = 0
        self.ocr_pause_until = 0
        self.ocr_active_until = 0
        self.last_ocr_popup: Optional[dict[str, Any]] = None
        self.last_attack_log = 0
        self.last_attack_pulse = 0
        self.attack_held = False
        self.attack_hold_started = 0
        self.attack_resume_at = 0
        self.attack_key_held = ""
        self.last_focus_error_log = 0
        self.last_dungeon_entry_check = 0
        self.last_dungeon_gate_log = 0
        self.last_home_debug_log = 0
        self.action_pause_until = 0
        self.last_minimap_position: Optional[tuple[int, int]] = None
        self.dungeon_entry_started = False

    def start(self, config: BotConfig) -> None:
        if self.running:
            return
        self.ensure_dependencies()
        self.target_hwnd = self.focus_game_window(REQUIRED_GAME_WINDOW)
        self.stop_event.clear()
        self.dungeon_entry_started = False
        self.last_dungeon_entry_check = 0
        self.last_dungeon_gate_log = 0
        self.last_home_return = 0
        self.last_home_debug_log = 0
        self.last_minimap_position = None
        self.ocr_active_until = 0
        self.ocr_pause_until = 0
        self.last_ocr_popup = None
        self.release_attack()
        self.running = True
        self.thread = threading.Thread(target=self.loop, args=(config,), daemon=True)
        self.thread.start()
        self.log(f"Bot started. Version: {APP_VERSION}. Keyboard layout: {config.keyboard_layout}.")
        append_event_log(f"Bot started. Version={APP_VERSION}")

    def stop(self) -> None:
        self.stop_event.set()
        self.release_attack()
        self.ocr_active_until = 0
        self.action_pause_until = 0
        self.running = False
        self.log("Bot stopped.")

    def ensure_dependencies(self) -> None:
        if not is_running_as_admin():
            raise RuntimeError("MeowMeowBot must be started as admin. Use Start_MeowMeowBot_Hidden.vbs.")
        missing = []
        if pyautogui is None:
            missing.append("pyautogui")
        if ImageGrab is None or Image is None:
            missing.append("pillow")
        if cv2 is None:
            missing.append("opencv-python")
        if np is None:
            missing.append("numpy")
        if pytesseract is None:
            missing.append("pytesseract")
        if missing:
            raise RuntimeError("Missing dependencies: " + ", ".join(missing))
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.02

    def focus_game_window(self, title_part: str) -> int:
        if not title_part:
            raise RuntimeError("Game window title is required.")
        if win32gui is None:
            raise RuntimeError("pywin32 is required so the bot can access the Ranmelle window.")
        title_part = title_part.lower()
        matches: list[int] = []

        def callback(hwnd: int, _: Any) -> None:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if title and title_part in title.lower():
                matches.append(hwnd)

        win32gui.EnumWindows(callback, None)
        if not matches:
            raise RuntimeError(f"Ranmelle window was not found. Open Ranmelle before starting the bot.")
        try:
            try:
                win32gui.ShowWindow(matches[0], 5)
            except Exception:
                pass
            if not force_foreground_window(matches[0]):
                win32gui.SetForegroundWindow(matches[0])
            time.sleep(0.15)
            self.log("Ranmelle window focused.")
            return matches[0]
        except Exception as exc:
            raise RuntimeError(f"Could not focus the Ranmelle window: {exc}") from exc

    def ensure_target_window(self) -> None:
        if win32gui is None:
            raise RuntimeError("pywin32 is required so the bot can access the Ranmelle window.")
        if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
            self.target_hwnd = self.focus_game_window(REQUIRED_GAME_WINDOW)
            return
        if win32gui.GetForegroundWindow() != self.target_hwnd:
            try:
                win32gui.ShowWindow(self.target_hwnd, 5)
            except Exception:
                pass
            try:
                win32gui.SetForegroundWindow(self.target_hwnd)
            except Exception as exc:
                if force_foreground_window(self.target_hwnd):
                    time.sleep(0.04)
                    return
                current = now_ms()
                if current - self.last_focus_error_log > 5000:
                    self.last_focus_error_log = current
                    self.log(f"Window focus warning: {exc}")
                return
            time.sleep(0.04)

    def loop(self, config: BotConfig) -> None:
        try:
            while not self.stop_event.is_set():
                current = now_ms()
                if config.mode == "Farming":
                    if self.run_ocr(config, current):
                        time.sleep(0.03)
                        continue
                    self.run_attack(config, current)
                    self.run_skills(config, current)
                    self.run_command(config, current)
                    self.run_detectors(config, current)
                elif config.mode == "Dungeon":
                    self.run_detectors(config, current)
                    combat_active = self.run_dungeon(config, current)
                    if combat_active:
                        self.run_attack(config, current)
                        self.run_skills(config, current)
                time.sleep(0.03)
        except Exception as exc:
            self.log("Bot error: " + str(exc))
            details = traceback.format_exc()
            self.log(details)
            append_event_log("Bot error: " + str(exc))
            append_event_log(details)
        finally:
            self.release_attack()
            self.running = False

    def press(self, key: str, hold_seconds: float = 0.075) -> None:
        key = normalize_key(key)
        if key:
            self.ensure_target_window()
            if not send_virtual_key(key, hold_seconds):
                pyautogui.keyDown(key)
                time.sleep(hold_seconds)
                pyautogui.keyUp(key)

    def click(self, x: int, y: int) -> None:
        if x > 0 and y > 0:
            self.ensure_target_window()
            pyautogui.click(x, y)

    def should_abort_actions(self) -> bool:
        return self.stop_event.is_set() or not self.running

    def interruptible_sleep(self, seconds: float) -> bool:
        end = time.monotonic() + max(seconds, 0)
        while time.monotonic() < end:
            if self.should_abort_actions():
                return False
            time.sleep(min(0.05, max(end - time.monotonic(), 0)))
        return True

    def type_text(self, text: str) -> None:
        if text:
            self.ensure_target_window()
            if set_windows_clipboard_text(text):
                if not send_key_combo("ctrl", "v"):
                    pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(text, interval=0.01)

    def hold_attack(self, key: str) -> None:
        key = normalize_key(key)
        if not key:
            return
        if self.attack_held and self.attack_key_held == key:
            return
        self.release_attack()
        self.ensure_target_window()
        release_modifiers()
        if not send_virtual_key_down(key):
            pyautogui.keyDown(key)
        self.attack_held = True
        self.attack_key_held = key
        self.attack_hold_started = now_ms()
        self.last_attack_pulse = self.attack_hold_started
        self.log(f"Attack hold started: {key}")

    def release_attack(self) -> None:
        if not self.attack_held or not self.attack_key_held:
            self.attack_held = False
            self.attack_key_held = ""
            return
        key = self.attack_key_held
        if key in VK_CODES and os.name == "nt":
            release_virtual_key(key)
        else:
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
        self.attack_held = False
        self.attack_key_held = ""

    def run_attack(self, config: BotConfig, current: int) -> None:
        if not config.attack_enabled:
            self.release_attack()
            return
        if current < self.action_pause_until:
            self.release_attack()
            return
        self.hold_attack(config.attack_key)
        pulse_interval = max(min(config.attack_delay_ms, 1000), 15)
        if current - self.last_attack_pulse >= pulse_interval:
            key = normalize_key(config.attack_key)
            if key in VK_CODES and os.name == "nt":
                send_virtual_key_up(key)
                time.sleep(0.003)
                send_virtual_key_down(key)
            else:
                pyautogui.keyUp(key)
                time.sleep(0.003)
                pyautogui.keyDown(key)
            self.last_attack_pulse = current
        if current - self.last_attack_log >= 5000:
            self.last_attack_log = current
            self.log(f"Attack key refreshed: {config.attack_key} every {pulse_interval}ms")

    def run_skills(self, config: BotConfig, current: int) -> None:
        for index, skill in enumerate(config.skills):
            if not skill.enabled or not skill.key:
                continue
            ident = f"skill_{index}"
            if current - self.last_skill.get(ident, 0) >= max(skill.interval_ms, 20):
                pause_ms = max(skill.cast_pause_ms, 0)
                taps = max(skill.taps, 1)
                self.action_pause_until = now_ms() + pause_ms + 80
                self.release_attack()
                release_modifiers()
                time.sleep(0.03)
                for tap_index in range(taps):
                    self.press(skill.key, 0.08)
                    if tap_index + 1 < taps:
                        time.sleep(0.05)
                release_modifiers()
                self.last_skill[ident] = current
                self.log(f"Used {skill.name}. ({taps} tap{'s' if taps != 1 else ''})")
                time.sleep(pause_ms / 1000)

    def run_command(self, config: BotConfig, current: int) -> None:
        if not config.command_enabled:
            return
        interval = max(config.command_every_sec, 1) * 1000
        if current - self.last_command < interval:
            return
        self.last_command = current
        self.send_chat_command(config.command_text, max(config.command_step_delay_ms, 500))
        self.log("Scheduled command sent.")

    def send_chat_command(self, command_text: str, step_delay_ms: int = 500) -> None:
        if not command_text:
            return
        release_modifiers()
        self.press("enter")
        time.sleep(max(step_delay_ms, 250) / 1000)
        self.type_text(command_text)
        time.sleep(max(step_delay_ms, 250) / 1000)
        self.ensure_target_window()
        self.press("enter")
        release_modifiers()

    def run_detectors(self, config: BotConfig, current: int) -> None:
        for index, detector in enumerate(config.detectors):
            if not detector.enabled or not detector.image:
                continue
            if detector.mode != config.mode:
                continue
            ident = f"detector_{index}"
            if current - self.last_detector.get(ident, 0) < max(detector.cooldown_ms, 200):
                continue
            match = self.find_image(detector.image, detector.confidence)
            if not match:
                continue
            self.last_detector[ident] = current
            self.log(f"{detector.name} detected at {match['center']}.")
            self.apply_detector_action(config, detector, match)

    def apply_detector_action(self, config: BotConfig, detector: DetectorConfig, match: dict[str, Any]) -> None:
        action = detector.action
        if detector.mode == "Dungeon" and "death" in detector.name.lower():
            self.handle_death_dialog(config.dungeon)
            return
        if action == "Hold Space 3s":
            self.hold_key("space", 3.0)
            self.log("Detector handled: held Space for 3 seconds.")
        elif action == "Press Enter":
            self.press("enter")
        elif action == "Click Death OK":
            self.handle_death_dialog(config.dungeon)
        elif action == "Click Image":
            x, y = match["center"]
            self.ensure_target_window()
            pyautogui.click(x, y)
        elif action == "Press Custom Key":
            self.press(detector.custom_key)
        elif action == "None":
            return

    def run_ocr(self, config: BotConfig, current: int) -> bool:
        ocr = config.ocr
        if not ocr.enabled:
            return False
        if current < self.ocr_pause_until:
            return current < self.ocr_active_until
        if current - self.last_detector.get("__ocr__", 0) < max(ocr.check_interval_ms, 500):
            return current < self.ocr_active_until
        self.last_detector["__ocr__"] = current
        if ocr.tesseract_path and pytesseract is not None:
            pytesseract.pytesseract.tesseract_cmd = ocr.tesseract_path
        popup = self.find_ocr_popup(ocr)
        if not popup:
            self.ocr_last_answer = ""
            self.ocr_attempt_count = 0
            self.ocr_active_until = 0
            self.last_ocr_popup = None
            return False
        self.last_ocr_popup = popup
        settle_ms = max(ocr.popup_settle_delay_ms, 3000)
        pause_ms = settle_ms + max(ocr.retry_delay_ms, 1500) + max(ocr.result_delay_ms, 500) + 1500
        self.ocr_active_until = now_ms() + pause_ms
        self.action_pause_until = self.ocr_active_until
        self.release_attack()
        release_modifiers()
        self.park_mouse_for_ocr(ocr)
        self.log("Lie Detector popup detected.")
        append_event_log(
            f"Lie Detector detected at top_left={popup.get('top_left')} center={popup.get('center')} "
            f"confidence={popup.get('confidence'):.3f}; automation paused; waiting {settle_ms}ms before OCR."
        )
        self.log(f"Waiting {settle_ms}ms for Lie Detector OCR to settle.")
        wait_until = now_ms() + settle_ms
        while now_ms() < wait_until:
            if self.should_abort_actions():
                append_event_log("Lie Detector OCR aborted during popup settle delay because bot was stopped.")
                return True
            time.sleep(0.05)
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted before reading because bot was stopped.")
            return True
        text = self.read_ocr_region(ocr)
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted after reading because bot was stopped.")
            return True
        if not text:
            self.log("OCR returned no text.")
            append_event_log("Lie Detector OCR returned no text; waiting before retry.")
            self.register_ocr_attempt("", ocr)
            self.ocr_pause_until = now_ms() + max(ocr.retry_delay_ms, 500)
            return True
        valid_code, reject_reason = validate_ld_code(text)
        if not valid_code:
            self.log(f"OCR rejected: {text} ({reject_reason}).")
            append_event_log(
                f"Lie Detector OCR rejected. text={text!r} reason={reject_reason}. "
                "Check Code region / popup-relative X/Y."
            )
            self.register_ocr_attempt(text, ocr)
            self.ocr_pause_until = now_ms() + max(ocr.retry_delay_ms, 500)
            return True
        if not self.register_ocr_attempt(text, ocr):
            append_event_log(f"Lie Detector OCR attempt rejected by failsafe. text={text}")
            return True
        input_x, input_y = self.ld_input_point(ocr)
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted before input click because bot was stopped.")
            return True
        self.click(input_x, input_y)
        if not self.interruptible_sleep(0.08):
            append_event_log("Lie Detector OCR aborted after input click because bot was stopped.")
            return True
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted before typing because bot was stopped.")
            return True
        self.type_text(text)
        self.press("enter")
        if not self.interruptible_sleep(0.08):
            append_event_log("Lie Detector OCR aborted after first Enter because bot was stopped.")
            return True
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted before second Enter because bot was stopped.")
            return True
        self.press("enter")
        self.log(f"Lie Detector answered: {text} (Enter x2)")
        append_event_log(f"Lie Detector answered text={text}; clicked input=({input_x}, {input_y}); pressed Enter twice.")
        if self.should_abort_actions():
            append_event_log("Lie Detector OCR aborted before result check because bot was stopped.")
            return True
        self.check_ocr_result_after_submit(ocr)
        self.ocr_pause_until = now_ms() + max(ocr.retry_delay_ms, 500)
        return True

    def register_ocr_attempt(self, text: str, ocr: OcrConfig) -> bool:
        if text == self.ocr_last_answer:
            self.ocr_attempt_count += 1
        else:
            self.ocr_last_answer = text
            self.ocr_attempt_count = 1
        if self.ocr_attempt_count > max(ocr.max_attempts, 1):
            self.log(f"OCR failsafe stopped the bot after {ocr.max_attempts} repeated attempts.")
            append_event_log(f"OCR failsafe stopped bot after repeated attempts. last_text={text}")
            self.stop()
            return False
        return True

    def check_ocr_result_after_submit(self, ocr: OcrConfig) -> None:
        if ocr.result_x <= 0 or ocr.result_y <= 0 or ocr.result_w <= 0 or ocr.result_h <= 0:
            append_event_log("Lie Detector result region not set; result could not be checked.")
            return
        time.sleep(max(ocr.result_delay_ms, 100) / 1000)
        if self.should_abort_actions():
            append_event_log("Lie Detector result check aborted because bot was stopped.")
            return
        result_x, result_y, result_w, result_h = self.ld_result_region(ocr)
        result = self.read_text_region(
            result_x,
            result_y,
            result_w,
            result_h,
            save_name="last_ld_result_crop.png",
        )
        if self.should_abort_actions():
            append_event_log("Lie Detector result check aborted after OCR read because bot was stopped.")
            return
        normalized = clean_ocr_text(result).lower()
        if len(normalized) > 80:
            self.log("Lie Detector result region looks too large or wrong; skipped classification.")
            append_event_log(
                f"Lie Detector result region likely wrong. region=({result_x}, {result_y}, {result_w}, {result_h}) "
                f"normalized_length={len(normalized)} raw={result!r}"
            )
            return
        passed_hit = "passed" in normalized or "pass" in normalized
        failed_hit = "failed" in normalized or "failure" in normalized or "fail" in normalized
        if passed_hit and not failed_hit:
            self.ocr_last_answer = ""
            self.ocr_attempt_count = 0
            self.ocr_failure_count = 0
            self.press("enter")
            self.log("Lie Detector result: passed.")
            append_event_log(f"Lie Detector result classified as passed. raw={result!r}")
            return
        if failed_hit:
            self.ocr_failure_count += 1
            self.log(f"Lie Detector result: failed ({self.ocr_failure_count}/{ocr.max_failures}).")
            self.press("enter")
            append_event_log(f"Lie Detector result classified as failed. raw={result!r}")
            if self.ocr_failure_count >= max(ocr.max_failures, 1):
                self.log("OCR failsafe stopped the bot after repeated failed bot checks.")
                append_event_log("OCR failsafe stopped bot after repeated failed Lie Detector checks.")
                self.stop()
            return
        if normalized:
            self.log(f"Lie Detector result could not be classified: {normalized}")
            append_event_log(f"Lie Detector result could not be classified. raw={result!r} normalized={normalized!r}")

    def read_ocr_region(self, ocr: OcrConfig) -> str:
        x, y, width, height = self.ld_code_region(ocr)
        if width > 260 or height > 80:
            self.log("OCR code region looks too large; skipped OCR.")
            append_event_log(
                f"Lie Detector code region likely wrong. region=({x}, {y}, {width}, {height}). "
                "Use Cookbot label preset or shrink Code region to the text only."
            )
            return ""
        self.park_mouse_for_ocr(ocr, (x, y, width, height))
        append_event_log(
            f"Reading Lie Detector OCR region=({x}, {y}, {width}, {height}) "
            f"relative_to_popup={ocr.relative_to_popup} cookbot_label_preset={ocr.cookbot_label_preset}"
        )
        return self.read_text_region(
            x,
            y,
            width,
            height,
            psm_modes=("7", "8", "13"),
            save_name="last_ld_code_crop.png",
        )

    def park_mouse_for_ocr(self, ocr: OcrConfig, region: Optional[tuple[int, int, int, int]] = None) -> None:
        if pyautogui is None:
            return
        try:
            if self.use_cookbot_label_preset(ocr) and self.last_ocr_popup:
                left, top = self.last_ocr_popup["top_left"]
                width, height = self.last_ocr_popup.get("size", (54, 17))
                safe_x = left + max(4, width // 2)
                safe_y = top + max(4, height // 2)
            elif self.last_ocr_popup:
                left, top = self.last_ocr_popup["top_left"]
                safe_x = left + 8
                safe_y = top + 8
            elif region:
                x, y, _, height = region
                safe_x = max(0, x - 80)
                safe_y = y + height + 50
            else:
                return
            pyautogui.moveTo(safe_x, safe_y, duration=0)
            append_event_log(f"Mouse parked for OCR at ({safe_x}, {safe_y}).")
        except Exception as exc:
            append_event_log(f"Mouse parking for OCR failed: {exc}")

    def use_cookbot_label_preset(self, ocr: OcrConfig) -> bool:
        if not self.last_ocr_popup:
            return False
        width, height = self.last_ocr_popup.get("size", (999, 999))
        label_sized_popup = width <= 100 and height <= 40
        return label_sized_popup or ocr.cookbot_label_preset

    def cookbot_offset_region(self, offset: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        left, top = self.last_ocr_popup["top_left"]
        x, y, width, height = offset
        return left + x, top + y, width, height

    def cookbot_offset_point(self, offset: tuple[int, int]) -> tuple[int, int]:
        left, top = self.last_ocr_popup["top_left"]
        x, y = offset
        return left + x, top + y

    def ld_code_region(self, ocr: OcrConfig) -> tuple[int, int, int, int]:
        if self.use_cookbot_label_preset(ocr):
            if self.last_ocr_popup and self.last_ocr_popup.get("code_region"):
                return self.last_ocr_popup["code_region"]
            return self.cookbot_offset_region(COOKBOT_CODE_OFFSET)
        return self.ocr_region(ocr, ocr.region_x, ocr.region_y, ocr.region_w, ocr.region_h)

    def ld_input_point(self, ocr: OcrConfig) -> tuple[int, int]:
        if self.use_cookbot_label_preset(ocr):
            return self.cookbot_offset_point(COOKBOT_INPUT_OFFSET)
        return self.ocr_point(ocr, ocr.input_x, ocr.input_y)

    def ld_result_region(self, ocr: OcrConfig) -> tuple[int, int, int, int]:
        if self.use_cookbot_label_preset(ocr):
            return self.cookbot_offset_region(COOKBOT_RESULT_OFFSET)
        return self.ocr_region(ocr, ocr.result_x, ocr.result_y, ocr.result_w, ocr.result_h)

    def ocr_point(self, ocr: OcrConfig, x: int, y: int) -> tuple[int, int]:
        if ocr.relative_to_popup and self.last_ocr_popup:
            left, top = self.last_ocr_popup["top_left"]
            return left + x, top + y
        return x, y

    def ocr_region(self, ocr: OcrConfig, x: int, y: int, width: int, height: int) -> tuple[int, int, int, int]:
        point_x, point_y = self.ocr_point(ocr, x, y)
        return point_x, point_y, width, height

    def read_text_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        psm_modes: tuple[str, ...] = ("6", "7"),
        save_name: str = "last_ocr_crop.png",
    ) -> str:
        if pytesseract is None:
            self.log("pytesseract is not installed.")
            return ""
        if ImageGrab is None:
            return ""
        bbox = (x, y, x + width, y + height)
        img = ImageGrab.grab(bbox=bbox)
        try:
            img.save(APP_DIR / save_name)
        except Exception:
            pass
        processed_images = self.prepare_ocr_images(img)
        candidates = []
        for processed in processed_images:
            for psm in psm_modes:
                config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist={OCR_ALLOWED_CHARS}"
                candidates.append(clean_ocr_text(pytesseract.image_to_string(processed, config=config)))
        append_event_log(f"OCR candidates from {save_name}: {candidates}")
        valid = [candidate for candidate in candidates if is_valid_ld_code(candidate)]
        if valid:
            ranked = sorted(valid, key=lambda candidate: (score_ld_code_candidate(candidate), len(candidate)), reverse=True)
            append_event_log(f"OCR ranked candidates from {save_name}: {[(candidate, score_ld_code_candidate(candidate)) for candidate in ranked]}")
            return ranked[0]
        return max(candidates, key=len, default="")

    def prepare_ocr_images(self, img: Any) -> list[Any]:
        gray = img.convert("L")
        if cv2 is None or np is None or Image is None:
            return [gray.resize((gray.width * 4, gray.height * 4))]
        variants = []
        rgb = np.array(img.convert("RGB"))
        gray_arr = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        blue_score = rgb[:, :, 2].astype(np.int16) - ((rgb[:, :, 0].astype(np.int16) + rgb[:, :, 1].astype(np.int16)) // 2)
        color_mask = ((gray_arr < 245) | (blue_score > 12)).astype(np.uint8) * 255
        color_mask = cv2.bitwise_not(color_mask)
        color_mask = cv2.resize(color_mask, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        variants.append(Image.fromarray(color_mask))
        arr = np.array(gray)
        arr = cv2.resize(arr, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        variants.append(Image.fromarray(arr))
        arr = cv2.GaussianBlur(arr, (3, 3), 0)
        _, otsu = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(Image.fromarray(otsu))
        adaptive = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
        variants.append(Image.fromarray(adaptive))
        return variants

    def run_dungeon(self, config: BotConfig, current: int) -> bool:
        dungeon = config.dungeon
        if not dungeon.enabled:
            return False
        henesys_visible = self.is_henesys_visible(dungeon)
        if dungeon.role == "Leecher":
            if not self.dungeon_entry_started:
                self.dungeon_entry_started = True
                self.log("Dungeon role is Leecher; combat automation is disabled.")
            return False
        if not self.dungeon_entry_started:
            if current - self.last_dungeon_entry_check >= 2000:
                self.last_dungeon_entry_check = current
                if not henesys_visible:
                    if current - self.last_dungeon_gate_log >= 7000:
                        self.last_dungeon_gate_log = current
                        self.log("Henesys/NPC image not visible; skipping dungeon NPC cycle.")
                    return True
                self.dungeon_entry_started = self.start_dungeon_entry(dungeon, current, henesys_visible=True)
            return False
        if henesys_visible:
            if current - self.last_dungeon_gate_log >= 7000:
                self.last_dungeon_gate_log = current
                self.log("Henesys/NPC image visible; dungeon combat paused.")
            return False
        finish = self.find_image(dungeon.finish_image, dungeon.confidence)
        if finish and not self.finish_handled:
            self.finish_handled = True
            self.log("Dungeon finish banner detected.")
            self.finish_dungeon(dungeon)
            return False
        if not finish:
            self.finish_handled = False
        if current - self.last_home_return >= max(dungeon.return_home_every_ms, 250):
            self.last_home_return = current
            self.return_to_home(dungeon)
        return True

    def is_henesys_visible(self, dungeon: DungeonConfig) -> bool:
        return self.find_image(dungeon.npc_image, min(dungeon.confidence, 0.65)) is not None

    def find_ocr_popup(self, ocr: OcrConfig) -> Optional[dict[str, Any]]:
        if not ocr.popup_image:
            return None
        if not ocr.cookbot_label_preset:
            return self.find_image(ocr.popup_image, ocr.popup_confidence)
        candidates = self.find_image_candidates(ocr.popup_image, ocr.popup_confidence, limit=20)
        for candidate in candidates:
            self.last_ocr_popup = candidate
            if self.is_valid_cookbot_code_crop(candidate):
                append_event_log(
                    f"Lie Detector popup candidate accepted at {candidate.get('top_left')} "
                    f"confidence={candidate.get('confidence'):.3f}."
                )
                return candidate
            append_event_log(
                f"Lie Detector popup candidate rejected at {candidate.get('top_left')} "
                f"confidence={candidate.get('confidence'):.3f}; code crop did not look valid."
            )
        self.last_ocr_popup = None
        return None

    def is_valid_cookbot_code_crop(self, popup: dict[str, Any]) -> bool:
        if ImageGrab is None or cv2 is None or np is None:
            return True
        region = self.locate_cookbot_code_region(popup)
        if not region:
            return False
        popup["code_region"] = region
        x, y, width, height = region
        try:
            img = ImageGrab.grab(bbox=(x, y, x + width, y + height)).convert("RGB")
        except Exception as exc:
            append_event_log(f"Cookbot code crop validation failed to grab region=({x}, {y}, {width}, {height}): {exc}")
            return False
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        white_ratio = float((gray > 235).mean())
        dark_ratio = float((gray < 90).mean())
        blue_score = arr[:, :, 2].astype(np.int16) - (
            (arr[:, :, 0].astype(np.int16) + arr[:, :, 1].astype(np.int16)) // 2
        )
        colored_text_ratio = float(((gray < 210) & (blue_score > 8)).mean())
        append_event_log(
            f"Cookbot code crop validation region=({x}, {y}, {width}, {height}) "
            f"white_ratio={white_ratio:.3f} dark_ratio={dark_ratio:.3f} colored_text_ratio={colored_text_ratio:.3f}."
        )
        return white_ratio >= 0.65 and dark_ratio <= 0.20 and colored_text_ratio <= 0.25

    def locate_cookbot_code_region(self, popup: dict[str, Any]) -> Optional[tuple[int, int, int, int]]:
        if ImageGrab is None or cv2 is None or np is None:
            return None
        left, top = popup["top_left"]
        x_off, y_off, search_w, search_h = COOKBOT_CODE_SEARCH_OFFSET
        search_x = max(0, left + x_off)
        search_y = max(0, top + y_off)
        try:
            if pyautogui is not None:
                screen_w, screen_h = pyautogui.size()
                safe_x = min(max(0, search_x + search_w + 60), max(0, screen_w - 2))
                safe_y = min(max(0, search_y + search_h + 60), max(0, screen_h - 2))
                pyautogui.moveTo(safe_x, safe_y, duration=0)
                time.sleep(0.05)
            img = ImageGrab.grab(bbox=(search_x, search_y, search_x + search_w, search_y + search_h)).convert("RGB")
            img.save(APP_DIR / "last_ld_code_search.png")
        except Exception as exc:
            append_event_log(
                f"Cookbot code search grab failed region=({search_x}, {search_y}, {search_w}, {search_h}): {exc}"
            )
            return None

        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        white_col_ratio = (gray > 238).mean(axis=0)
        panel_candidates = np.where(white_col_ratio > 0.48)[0]
        panel_right = int(panel_candidates[-1]) + 1 if len(panel_candidates) else search_w
        panel_right = max(120, min(panel_right, search_w))
        panel_gray = gray[:, :panel_right]
        row_dark = (panel_gray < 80).sum(axis=1)
        input_line_candidates = np.where(row_dark > max(70, panel_right * 0.28))[0]
        input_line_y = int(input_line_candidates[0]) if len(input_line_candidates) else search_h

        usable_bottom = max(10, min(input_line_y - 2, search_h))
        blue_score = arr[:, :, 2].astype(np.int16) - (
            (arr[:, :, 0].astype(np.int16) + arr[:, :, 1].astype(np.int16)) // 2
        )
        text_mask = ((gray < 225) | (blue_score > 10))
        text_mask[:8, :] = False
        text_mask[usable_bottom:, :] = False
        text_mask[:, panel_right:] = False
        text_mask[:, :2] = False

        band_top = max(8, input_line_y - 42)
        band_bottom = max(band_top + 8, min(input_line_y - 6, search_h))
        band_mask = text_mask[band_top:band_bottom, :panel_right]
        band_row_counts = band_mask.sum(axis=1)
        active_band_rows = np.where((band_row_counts >= 1) & (band_row_counts <= 140))[0]
        band_region: Optional[tuple[int, int, int, int]] = None
        band_candidate: Optional[tuple[int, int, int, int]] = None
        if len(active_band_rows):
            band_active = np.zeros_like(band_mask, dtype=bool)
            band_active[active_band_rows, :] = band_mask[active_band_rows, :]
            ys, xs = np.where(band_active)
            if len(xs) >= 12 and len(ys):
                min_x = int(xs.min())
                max_x = int(xs.max())
                min_y = int(ys.min()) + band_top
                max_y = int(ys.max()) + band_top
                crop_w = max_x - min_x + 1
                crop_h_raw = max_y - min_y + 1
                if 25 <= crop_w <= 190 and 2 <= crop_h_raw <= 18:
                    crop_x = max(0, min_x - 8)
                    crop_y = max(0, min_y - 8)
                    crop_w = min(panel_right - crop_x, crop_w + 20)
                    crop_h = min(search_h - crop_y, max(24, crop_h_raw + 16))
                    band_region = (search_x + crop_x, search_y + crop_y, crop_w, crop_h)
                    band_candidate = (min_y, max_y, min_x, max_x)

        row_counts = text_mask.sum(axis=1)
        active_rows = np.where((row_counts >= 2) & (row_counts <= 160))[0]
        groups: list[tuple[int, int]] = []
        if len(active_rows):
            start = int(active_rows[0])
            previous = start
            for row in active_rows[1:]:
                row = int(row)
                if row <= previous + 2:
                    previous = row
                    continue
                groups.append((start, previous))
                start = row
                previous = row
            groups.append((start, previous))

        code_candidates: list[tuple[int, tuple[int, int, int, int], tuple[int, int, int, int]]] = []
        for start, end in groups:
            group_h = end - start + 1
            if group_h < 3 or group_h > 18:
                continue
            group_mask = text_mask[max(0, start - 2):min(usable_bottom, end + 3), :]
            xs = np.where(group_mask.any(axis=0))[0]
            if len(xs) < 25:
                continue
            min_x = int(xs[0])
            max_x = int(xs[-1])
            crop_w = max_x - min_x + 1
            if crop_w < 35 or crop_w > 180:
                continue
            if start < 28 or end > input_line_y - 7:
                continue
            crop_x = max(0, min_x - 8)
            crop_y = max(0, start - 7)
            crop_w = min(panel_right - crop_x, crop_w + 20)
            crop_h = min(search_h - crop_y, max(22, end - start + 15))
            # The LD code is the compact text row closest above the input line.
            score = input_line_y - end
            region = (search_x + crop_x, search_y + crop_y, crop_w, crop_h)
            code_candidates.append((score, region, (start, end, min_x, max_x)))

        best_region: Optional[tuple[int, int, int, int]] = None
        best_candidate: Optional[tuple[int, int, int, int]] = None
        if band_region:
            best_region = band_region
            best_candidate = band_candidate
        elif code_candidates:
            code_candidates.sort(key=lambda item: item[0])
            _, best_region, best_candidate = code_candidates[0]

        if not best_region:
            fallback = self.cookbot_offset_region(COOKBOT_CODE_OFFSET)
            append_event_log(
                f"Cookbot dynamic code crop not found; using fallback region={fallback} "
                f"search=({search_x}, {search_y}, {search_w}, {search_h}) panel_right={panel_right} "
                f"input_line_y={input_line_y} band=({band_top}, {band_bottom}) groups={groups}."
            )
            return fallback

        append_event_log(
            f"Cookbot dynamic code crop selected region={best_region} "
            f"search=({search_x}, {search_y}, {search_w}, {search_h}) panel_right={panel_right} "
            f"input_line_y={input_line_y} band=({band_top}, {band_bottom}) "
            f"groups={groups} best_candidate={best_candidate}."
        )
        return best_region

    def start_dungeon_entry(self, dungeon: DungeonConfig, current: Optional[int] = None, henesys_visible: Optional[bool] = None) -> bool:
        current = current or now_ms()
        npc = self.find_image(dungeon.npc_image, min(dungeon.confidence, 0.65))
        if not npc:
            if current - self.last_dungeon_gate_log >= 7000:
                self.last_dungeon_gate_log = current
                self.log("Henesys/NPC image not visible; skipping dungeon NPC cycle.")
            return False
        if dungeon.npc_offset_x > 0 and dungeon.npc_offset_y > 0:
            click_x = dungeon.npc_offset_x
            click_y = dungeon.npc_offset_y
        else:
            click_x, click_y = npc["center"]
        self.ensure_target_window()
        pyautogui.moveTo(click_x, click_y, duration=0.15)
        time.sleep(0.25)
        pyautogui.click(click_x, click_y)
        time.sleep(0.12)
        pyautogui.click(click_x, click_y)
        self.log(f"NPC clicked at {click_x}, {click_y}.")
        self.run_dungeon_drop_selection(dungeon)
        return True

    def run_dungeon_drop_selection(self, dungeon: DungeonConfig) -> None:
        option_index = {
            "4 drops": 0,
            "8 drops": 1,
            "12 drops": 2,
            "24 drops": 3,
            "Custom Drops": 4,
        }.get(dungeon.drop_option, 0)
        time.sleep(0.5)
        for _ in range(option_index):
            self.press("down")
            time.sleep(0.08)
        self.press("enter")
        self.log(f"Dungeon option selected: {dungeon.drop_option}")
        if dungeon.drop_option == "Custom Drops":
            time.sleep(0.45)
            self.type_text(str(max(dungeon.custom_coins, 1)))
            self.press("enter")
            self.log(f"Custom dungeon coins entered: {dungeon.custom_coins}")
        if dungeon.dialog_steps.strip() == LEGACY_DUNGEON_DIALOG_STEPS:
            self.log("Skipped legacy dungeon Enter step.")
            return
        self.run_dialog_steps(dungeon.dialog_steps)

    def handle_death_dialog(self, dungeon: DungeonConfig) -> None:
        if dungeon.death_ok_x > 0 and dungeon.death_ok_y > 0:
            self.click(dungeon.death_ok_x, dungeon.death_ok_y)
            self.log(f"Death Dialog handled: OK clicked at {dungeon.death_ok_x}, {dungeon.death_ok_y}.")
            return
        self.log("Death Dialog detected, but Death OK X/Y is not set.")

    def run_dialog_steps(self, steps: str) -> None:
        for raw in steps.splitlines():
            step = raw.strip()
            if not step or step.startswith("#"):
                continue
            kind, _, value = step.partition(":")
            kind = kind.strip().lower()
            value = value.strip()
            if kind == "wait":
                time.sleep(parse_float(value, 1.0))
            elif kind == "press":
                self.press(value)
            elif kind == "type":
                self.type_text(value)
            elif kind == "click":
                x_text, _, y_text = value.partition(",")
                self.click(parse_int(x_text), parse_int(y_text))
            elif kind == "enter":
                self.press("enter")
            self.log(f"Dialog step: {step}")

    def return_to_home(self, dungeon: DungeonConfig) -> None:
        current = now_ms()
        if dungeon.home_x <= 0 or dungeon.home_y <= 0:
            if current - self.last_home_debug_log >= 5000:
                self.last_home_debug_log = current
                self.log("Home return skipped: Minimap Home X/Y is not set.")
            return
        if dungeon.minimap_w > 0 and dungeon.minimap_h > 0:
            if not (
                dungeon.minimap_x <= dungeon.home_x <= dungeon.minimap_x + dungeon.minimap_w
                and dungeon.minimap_y <= dungeon.home_y <= dungeon.minimap_y + dungeon.minimap_h
            ):
                if current - self.last_home_debug_log >= 5000:
                    self.last_home_debug_log = current
                    self.log(
                        "Home return skipped: Minimap Home X/Y is outside the Minimap X/Y/W/H box. "
                        "Use the cursor position on the minimap, not the character position in the map."
                    )
                return
            char = self.find_minimap_character(dungeon)
            if not char:
                if current - self.last_home_debug_log >= 5000:
                    self.last_home_debug_log = current
                    self.log("Home return skipped: yellow minimap character was not found.")
                return
            if current - self.last_home_debug_log >= 5000:
                self.last_home_debug_log = current
                self.log(
                    f"Minimap marker: {char['center']} candidates={char.get('candidates', 0)} "
                    f"area={char.get('area', 0):.1f} size={char.get('size', ('?', '?'))}"
                )
            self.move_towards_home(dungeon, char["center"][0], char["center"][1], "minimap")
            return
        if current - self.last_home_debug_log >= 5000:
            self.last_home_debug_log = current
            self.log("Home return skipped: Minimap X/Y/W/H is not set.")

    def move_towards_home(self, dungeon: DungeonConfig, x: int, y: int, source: str) -> None:
        current = now_ms()
        dx = dungeon.home_x - x
        dy = dungeon.home_y - y
        if abs(dx) <= dungeon.tolerance_px and abs(dy) <= dungeon.tolerance_px:
            if current - self.last_home_debug_log >= 5000:
                self.last_home_debug_log = current
                self.log(f"Home position OK ({source}). Current: {x}, {y}")
            return
        if dx < -dungeon.tolerance_px:
            self.nudge("left", abs(dx), source)
        elif dx > dungeon.tolerance_px:
            self.nudge("right", abs(dx), source)
        if dy < -dungeon.tolerance_px:
            self.nudge("up", abs(dy), source)
        elif dy > dungeon.tolerance_px:
            self.nudge("down", abs(dy), source)
        self.log(f"Returning to home position ({source}). Current: {x}, {y}; Target: {dungeon.home_x}, {dungeon.home_y}")

    def find_minimap_character(self, dungeon: DungeonConfig) -> Optional[dict[str, Any]]:
        if ImageGrab is None or cv2 is None or np is None:
            return None
        x = max(dungeon.minimap_x, 0)
        y = max(dungeon.minimap_y, 0)
        w = max(dungeon.minimap_w, 1)
        h = max(dungeon.minimap_h, 1)
        screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([18, 80, 120], dtype=np.uint8)
        upper = np.array([42, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        max_area = max((w * h) * 0.04, 12)
        candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            rx, ry, rw, rh = cv2.boundingRect(contour)
            if not (3 <= area <= max_area):
                continue
            if not (2 <= rw <= 14 and 2 <= rh <= 14):
                continue
            candidates.append((contour, area, rx, ry, rw, rh))
        if not candidates:
            return None
        if self.last_minimap_position:
            px, py = self.last_minimap_position
            contour, area, rx, ry, rw, rh = min(
                candidates,
                key=lambda item: ((x + item[2] + item[4] / 2) - px) ** 2 + ((y + item[3] + item[5] / 2) - py) ** 2,
            )
        else:
            contour, area, rx, ry, rw, rh = max(candidates, key=lambda item: item[1])
        moments = cv2.moments(contour)
        if not moments["m00"]:
            cx = x + rx + rw // 2
            cy = y + ry + rh // 2
        else:
            cx = x + int(moments["m10"] / moments["m00"])
            cy = y + int(moments["m01"] / moments["m00"])
        self.last_minimap_position = (cx, cy)
        return {"center": (cx, cy), "confidence": 1.0, "candidates": len(candidates), "area": float(area), "size": (int(rw), int(rh))}

    def nudge(self, key: str, distance: int, source: str = "image") -> None:
        if source == "minimap":
            hold = min(max(distance / 75.0, 0.18), 1.15)
        else:
            hold = min(max(distance / 450.0, 0.08), 0.55)
        self.ensure_target_window()
        if key in VK_CODES and os.name == "nt":
            send_virtual_key(key, hold)
            return
        pyautogui.keyDown(key)
        time.sleep(hold)
        pyautogui.keyUp(key)

    def hold_key(self, key: str, seconds: float) -> None:
        key = normalize_key(key)
        self.ensure_target_window()
        if key in VK_CODES and os.name == "nt":
            send_virtual_key(key, max(seconds, 0.05))
            return
        pyautogui.keyDown(key)
        time.sleep(max(seconds, 0.05))
        pyautogui.keyUp(key)

    def finish_dungeon(self, dungeon: DungeonConfig) -> None:
        self.ensure_target_window()
        self.action_pause_until = now_ms() + 12000
        release_modifiers()
        pyautogui.keyDown("left")
        time.sleep(0.15)
        for _ in range(3):
            self.press("alt", 0.08)
            time.sleep(0.08)
            self.press("alt", 0.08)
            time.sleep(0.30)
        time.sleep(0.55)
        pyautogui.keyUp("left")
        release_virtual_key("left")
        time.sleep(0.35)
        self.log("Finish movement: 3x left double-Alt flash jump before portal.")
        self.send_chat_command("@check", 450)
        time.sleep(0.25)
        self.log("Finish command sent: @check")
        self.send_chat_command("@dispose", 450)
        time.sleep(0.35)
        self.log("Finish command sent: @dispose")
        portal = self.find_dungeon_image(dungeon.portal_image, dungeon)
        if portal:
            x, y = portal["center"]
            self.ensure_target_window()
            pyautogui.click(x + dungeon.portal_offset_x, y + dungeon.portal_offset_y)
            self.log(f"Portal image clicked at {x}, {y}.")
        else:
            self.click(dungeon.portal_x, dungeon.portal_y)
            self.log("Finish movement complete; portal fallback coordinates clicked if set.")
        time.sleep(0.45)
        self.press("space", 0.12)
        self.log("Portal confirmation sent: Space.")
        wait_seconds = max(dungeon.henesys_wait_after_exit_sec, 0)
        if wait_seconds:
            self.log(f"Waiting in Henesys after exit: {wait_seconds}s.")
            time.sleep(wait_seconds)
        self.dungeon_entry_started = False

    def find_dungeon_image(self, template_path: str, dungeon: DungeonConfig) -> Optional[dict[str, Any]]:
        region = self.dungeon_playfield_region(dungeon)
        match = self.find_image(template_path, dungeon.confidence, region)
        if match or region is None:
            return match
        return self.find_image(template_path, dungeon.confidence)

    def dungeon_playfield_region(self, dungeon: DungeonConfig) -> Optional[tuple[int, int, int, int]]:
        if dungeon.playfield_w <= 0 or dungeon.playfield_h <= 0:
            return None
        return (dungeon.playfield_x, dungeon.playfield_y, dungeon.playfield_w, dungeon.playfield_h)

    def find_image(self, template_path: str, confidence: float, region: Optional[tuple[int, int, int, int]] = None) -> Optional[dict[str, Any]]:
        template_path = resolve_template_path(template_path)
        if not template_path or not os.path.exists(template_path):
            return None
        if ImageGrab is None or cv2 is None or np is None:
            return None
        offset_x = 0
        offset_y = 0
        if region:
            offset_x, offset_y, width, height = region
            screenshot = ImageGrab.grab(bbox=(offset_x, offset_y, offset_x + width, offset_y + height))
        else:
            screenshot = ImageGrab.grab()
        screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            return None
        h, w = template.shape[:2]
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        best_val = float(max_val)
        best_loc = max_loc
        gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        gray_result = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
        _, gray_val, _, gray_loc = cv2.minMaxLoc(gray_result)
        if gray_val > best_val:
            best_val = float(gray_val)
            best_loc = gray_loc
        if best_val < confidence:
            return None
        x, y = best_loc
        screen_x = x + offset_x
        screen_y = y + offset_y
        return {
            "confidence": best_val,
            "top_left": (int(screen_x), int(screen_y)),
            "center": (int(screen_x + w / 2), int(screen_y + h / 2)),
            "size": (int(w), int(h)),
        }

    def find_image_candidates(
        self,
        template_path: str,
        confidence: float,
        region: Optional[tuple[int, int, int, int]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        template_path = resolve_template_path(template_path)
        if not template_path or not os.path.exists(template_path):
            return []
        if ImageGrab is None or cv2 is None or np is None:
            return []
        offset_x = 0
        offset_y = 0
        if region:
            offset_x, offset_y, width, height = region
            screenshot = ImageGrab.grab(bbox=(offset_x, offset_y, offset_x + width, offset_y + height))
        else:
            screenshot = ImageGrab.grab()
        screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            return []
        h, w = template.shape[:2]
        maps = [cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)]
        gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        maps.append(cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED))

        raw: list[tuple[float, int, int]] = []
        for result in maps:
            ys, xs = np.where(result >= confidence)
            for x, y in zip(xs, ys):
                raw.append((float(result[y, x]), int(x), int(y)))
        raw.sort(reverse=True, key=lambda item: item[0])

        candidates: list[dict[str, Any]] = []
        for score, x, y in raw:
            if any(abs(x - kept["raw_top_left"][0]) < w and abs(y - kept["raw_top_left"][1]) < h for kept in candidates):
                continue
            screen_x = x + offset_x
            screen_y = y + offset_y
            candidates.append(
                {
                    "confidence": score,
                    "top_left": (int(screen_x), int(screen_y)),
                    "center": (int(screen_x + w / 2), int(screen_y + h / 2)),
                    "size": (int(w), int(h)),
                    "raw_top_left": (x, y),
                }
            )
            if len(candidates) >= limit:
                break
        for candidate in candidates:
            candidate.pop("raw_top_left", None)
        return candidates


class MapleBotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MeowMeowBot")
        self.geometry("1180x780")
        self.minsize(760, 520)
        self.configure(bg=UI_BG)
        self.config_data = default_config()
        self.vars: dict[str, Any] = {}
        self.skill_rows: list[dict[str, Any]] = []
        self.detector_rows: list[dict[str, Any]] = []
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.log_lines: list[str] = []
        self.backend = AutomationBackend(self.enqueue_log)
        self.hotkey_latch: set[str] = set()
        self.pending_mouse_capture: Optional[list[str]] = None
        self.pending_mouse_label = ""
        self.compact_mode = False
        self.full_geometry_before_compact = ""
        self.cursor_tracking_enabled = False
        self.build_style()
        self.build_ui()
        self.load_config(DEFAULT_CONFIG, quiet=True)
        self.after(100, self.drain_log)
        self.after(500, self.hotkey_poll)
        self.after(120, self.update_cursor_position)

    def build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background=UI_BG, foreground=UI_TEXT, fieldbackground=UI_PANEL_DARK)
        style.configure("TFrame", background=UI_BG)
        style.configure("Card.TFrame", background=UI_PANEL, relief="flat")
        style.configure("Hero.TFrame", background=UI_PANEL_DARK, relief="flat")
        style.configure("TNotebook", background=UI_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(26, 13), background=UI_PANEL, foreground=UI_MUTED)
        style.map("TNotebook.Tab", background=[("selected", UI_PINK_DARK)], foreground=[("selected", UI_TEXT)])
        style.configure("TButton", padding=(14, 9), background=UI_PANEL_2, foreground=UI_TEXT, borderwidth=0)
        style.configure("Start.TButton", background=UI_PINK, foreground=UI_TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("Stop.TButton", background=UI_PANEL_2, foreground=UI_TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background=UI_PINK, foreground=UI_TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=UI_BG, foreground=UI_TEXT)
        style.configure("Muted.TLabel", background=UI_BG, foreground=UI_MUTED)
        style.configure("Card.TLabel", background=UI_PANEL, foreground=UI_TEXT)
        style.configure("Hero.TLabel", background=UI_PANEL_DARK, foreground=UI_TEXT)
        style.configure("TCheckbutton", background=UI_BG, foreground=UI_TEXT)
        style.configure("TLabelframe", background=UI_BG, foreground=UI_TEXT, bordercolor=UI_PANEL_2, lightcolor=UI_PANEL_2, darkcolor=UI_PANEL_2)
        style.configure("TLabelframe.Label", background=UI_BG, foreground=UI_TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground=UI_PANEL_DARK, foreground=UI_TEXT, insertcolor=UI_TEXT, padding=(8, 6))
        style.configure("TCombobox", fieldbackground=UI_PANEL_DARK, background=UI_PANEL_2, foreground=UI_TEXT, arrowcolor=UI_CYAN, padding=(8, 6))
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", UI_PANEL_DARK), ("!disabled", UI_PANEL_DARK)],
            foreground=[("readonly", UI_TEXT), ("!disabled", UI_TEXT)],
            selectbackground=[("readonly", UI_PANEL_2), ("!disabled", UI_PANEL_2)],
            selectforeground=[("readonly", UI_TEXT), ("!disabled", UI_TEXT)],
        )
        self.option_add("*TCombobox*Listbox.background", UI_PANEL_DARK)
        self.option_add("*TCombobox*Listbox.foreground", UI_TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", UI_PINK_DARK)
        self.option_add("*TCombobox*Listbox.selectForeground", UI_TEXT)

    def build_ui(self) -> None:
        self.root_frame = ttk.Frame(self, padding=18)
        self.root_frame.pack(fill="both", expand=True)
        accent = tk.Frame(self.root_frame, bg=UI_PINK, height=5)
        accent.pack(fill="x", pady=(0, 14))
        header = tk.Frame(self.root_frame, bg=UI_BG)
        header.pack(fill="x")
        title_block = tk.Frame(header, bg=UI_BG)
        title_block.pack(side="left", fill="x", expand=True)
        tk.Label(title_block, text="MEOW", bg=UI_BG, fg=UI_TEXT, font=("Segoe UI Black", 34, "bold")).pack(side="left")
        tk.Label(title_block, text="MEOWBOT", bg=UI_BG, fg=UI_TEXT, font=("Segoe UI Black", 34, "bold")).pack(side="left", padx=(10, 0))
        tk.Label(title_block, text="Alpha Version", bg=UI_BG, fg=UI_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(12, 0), pady=(0, 28))
        header_controls = tk.Frame(header, bg=UI_BG)
        header_controls.pack(side="right")
        self.vars["mode"] = tk.StringVar()
        ttk.Label(header_controls, text="MODE").pack(side="left", padx=(0, 6))
        ttk.Combobox(header_controls, textvariable=self.vars["mode"], values=MODE_OPTIONS, width=12, state="readonly").pack(side="left")
        self.vars["mode"].trace_add("write", lambda *_: self.on_mode_changed())
        self.compact_button = ttk.Button(header, text="Compact", command=self.toggle_compact_mode)
        self.compact_button.pack(side="right", padx=(16, 0))
        self.status_var = tk.StringVar(value="Stopped")
        self.timer_var = tk.StringVar(value="00:00:00")
        ttk.Label(header_controls, textvariable=self.timer_var, font=("Consolas", 12, "bold")).pack(side="left", padx=18)
        ttk.Label(header_controls, textvariable=self.status_var, font=("Segoe UI", 10, "bold")).pack(side="left")

        self.main_frame = ttk.Frame(self.root_frame)
        self.main_frame.pack(fill="both", expand=True, pady=(18, 0))
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.rowconfigure(0, weight=1)
        left = ttk.Frame(self.main_frame)
        left.grid(row=0, column=0, sticky="nsew")
        right = ttk.Frame(self.main_frame, width=280)
        right.grid(row=0, column=1, sticky="nsew", padx=(22, 0))
        right.grid_propagate(False)

        self.build_module_strip(left)
        self.tabs = ttk.Notebook(left)
        self.tabs.pack(fill="both", expand=True)
        self.build_combat_tab()
        self.build_detectors_tab()
        self.build_ocr_tab()
        self.build_dungeon_tab()
        self.build_command_tab()
        self.build_log_tab()
        right_inner = self.create_scrollable_container(right)
        self.build_side_panel(right_inner)
        self.build_compact_panel()

    def build_module_strip(self, parent: ttk.Frame) -> None:
        strip = tk.Frame(parent, bg=UI_BG)
        strip.pack(fill="x", pady=(0, 16))
        self.module_card(strip, "FARMING", "Attack loop, buffs, Hot Time", UI_CYAN).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.module_card(strip, "DUNGEON", "Boss flow, revive, portal exit", UI_PINK).pack(side="left", fill="x", expand=True, padx=10)
        self.module_card(strip, "LIE DETECTOR", "OCR cleanup and auto-submit", UI_GREEN).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def module_card(self, parent: tk.Frame, title: str, subtitle: str, color: str) -> tk.Frame:
        card = tk.Frame(parent, bg=UI_PANEL, padx=14, pady=14)
        icon = tk.Canvas(card, width=44, height=44, bg=UI_PANEL, highlightthickness=0)
        icon.pack(side="left", padx=(0, 12))
        icon.create_oval(3, 3, 41, 41, fill=color, outline="")
        icon.create_text(22, 22, text=title[:1], fill=UI_TEXT, font=("Segoe UI Black", 15, "bold"))
        text = tk.Frame(card, bg=UI_PANEL)
        text.pack(side="left", fill="both", expand=True)
        tk.Label(text, text=title, bg=UI_PANEL, fg=UI_TEXT, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(text, text=subtitle, bg=UI_PANEL, fg=UI_MUTED, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(4, 0))
        return card

    def create_scrollable_container(self, parent: ttk.Frame) -> ttk.Frame:
        canvas = tk.Canvas(parent, bg=UI_BG, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_configure(_: Any) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event: Any) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        return inner

    def create_scrollable_tab(self, title: str, padding: int = 16) -> ttk.Frame:
        outer = ttk.Frame(self.tabs)
        self.tabs.add(outer, text=title)
        canvas = tk.Canvas(outer, bg=UI_BG, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=padding)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        inner.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        return inner

    def build_side_panel(self, parent: ttk.Frame) -> None:
        self.bind_card = self.info_card(parent, "WINDOW BINDING", [("TARGET", "Ranmelle"), ("STATUS", "Required")], UI_CYAN)
        self.mode_card = self.info_card(parent, "ACTIVE PROFILE", [("MODE", "Farming"), ("DUNGEON", "Auto")], UI_PINK)
        self.build_cursor_card(parent)
        ttk.Label(parent, text="CONTROL CENTER", font=("Segoe UI", 11, "bold")).pack(pady=(8, 12))
        ttk.Button(parent, text="START BOT", style="Start.TButton", command=self.start_bot).pack(fill="x", pady=(0, 10))
        ttk.Button(parent, text="STOP", style="Stop.TButton", command=self.stop_bot).pack(fill="x", pady=(0, 10))
        ttk.Separator(parent).pack(fill="x", pady=12)
        self.vars["start_hotkey"] = tk.StringVar()
        self.vars["stop_hotkey"] = tk.StringVar()
        self.vars["mouse_hotkey"] = tk.StringVar()
        self.vars["keyboard_layout"] = tk.StringVar()
        self.vars["game_window"] = tk.StringVar()
        self.combo_row(parent, "Keyboard layout", self.vars["keyboard_layout"], KEYBOARD_LAYOUTS)
        self.combo_row(parent, "Start hotkey", self.vars["start_hotkey"], KEY_OPTIONS)
        self.combo_row(parent, "Stop hotkey", self.vars["stop_hotkey"], KEY_OPTIONS)
        self.combo_row(parent, "Cursor toggle", self.vars["mouse_hotkey"], KEY_OPTIONS)
        self.hotkey_card = self.info_card(parent, "HOTKEYS", [("START", "F1"), ("STOP", "F2"), ("CURSOR", "F3")], UI_ORANGE)
        ttk.Separator(parent).pack(fill="x", pady=12)
        self.entry_row(parent, "Required window", self.vars["game_window"])
        ttk.Button(parent, text="LOAD CONFIG", style="Accent.TButton", command=self.load_config_dialog).pack(fill="x", pady=(18, 8))
        ttk.Button(parent, text="SAVE CONFIG", style="Accent.TButton", command=self.save_config_dialog).pack(fill="x", pady=8)
        ttk.Button(parent, text="SAVE DEFAULT", command=lambda: self.save_config(DEFAULT_CONFIG)).pack(fill="x", pady=8)

    def build_cursor_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="x", pady=(0, 14))
        ttk.Label(card, text="CURSOR POSITION", font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(anchor="w")
        row = tk.Frame(card, bg=UI_PANEL)
        row.pack(fill="x", pady=(10, 0))
        self.cursor_x_var = tk.StringVar(value="X: --")
        self.cursor_y_var = tk.StringVar(value="Y: --")
        self.cursor_tracking_var = tk.StringVar(value="F3: OFF")
        tk.Label(row, textvariable=self.cursor_x_var, bg=UI_PANEL, fg=UI_CYAN, font=("Cascadia Mono", 12, "bold")).pack(side="left", fill="x", expand=True)
        tk.Label(row, textvariable=self.cursor_y_var, bg=UI_PANEL, fg=UI_CYAN, font=("Cascadia Mono", 12, "bold")).pack(side="left", fill="x", expand=True)
        tk.Label(card, textvariable=self.cursor_tracking_var, bg=UI_PANEL, fg=UI_MUTED, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8, 0))

    def info_card(self, parent: ttk.Frame, title: str, rows: list[tuple[str, str]], color: str) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="x", pady=(0, 14))
        top = tk.Frame(card, bg=UI_PANEL)
        top.pack(fill="x")
        marker = tk.Canvas(top, width=34, height=34, bg=UI_PANEL, highlightthickness=0)
        marker.pack(side="left")
        marker.create_oval(4, 4, 30, 30, fill=color, outline="")
        marker.create_text(17, 17, text="●", fill=UI_TEXT, font=("Segoe UI", 8, "bold"))
        ttk.Label(top, text=title, font=("Segoe UI", 9, "bold"), style="Card.TLabel").pack(side="left", padx=(8, 0))
        for label, value in rows:
            line = tk.Frame(card, bg=UI_PANEL)
            line.pack(fill="x", pady=(8 if label == rows[0][0] else 2, 0))
            tk.Label(line, text=f"{label}:", bg=UI_PANEL, fg=UI_MUTED, font=("Segoe UI", 8, "bold"), width=10, anchor="w").pack(side="left")
            tk.Label(line, text=value, bg=UI_PANEL, fg=UI_TEXT, font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        return card

    def build_compact_panel(self) -> None:
        self.compact_frame = ttk.Frame(self.root_frame, style="Card.TFrame", padding=12)
        top = ttk.Frame(self.compact_frame, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="MeowMeowBot", font=("Segoe UI", 13, "bold"), style="Card.TLabel").pack(side="left")
        self.compact_status_var = tk.StringVar(value="Stopped")
        self.compact_full_button = ttk.Button(top, text="Full", command=self.toggle_compact_mode)
        self.compact_full_button.pack(side="right", padx=(10, 0))
        ttk.Label(top, textvariable=self.compact_status_var, font=("Segoe UI", 13, "bold"), style="Card.TLabel").pack(side="right")
        self.compact_log = tk.Text(
            self.compact_frame,
            height=3,
            bg=UI_PANEL_DARK,
            fg=UI_TEXT,
            insertbackground=UI_TEXT,
            relief="flat",
            borderwidth=0,
            font=("Cascadia Mono", 9),
            padx=8,
            pady=8,
            wrap="word",
        )
        self.compact_log.pack(fill="both", expand=True, pady=(10, 0))
        self.compact_log.tag_configure("time", foreground=UI_GREEN)
        self.compact_log.tag_configure("start", foreground=UI_GREEN)
        self.compact_log.tag_configure("stop", foreground=UI_RED)
        self.compact_log.tag_configure("warning", foreground=UI_YELLOW)
        self.compact_log.tag_configure("error", foreground=UI_RED)
        self.compact_log.tag_configure("normal", foreground=UI_TEXT)

    def toggle_compact_mode(self) -> None:
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.full_geometry_before_compact = self.geometry()
            self.main_frame.pack_forget()
            self.compact_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.compact_button.configure(text="Full")
            self.geometry("560x190")
            self.minsize(440, 170)
            self.update_compact_log()
        else:
            self.compact_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True, pady=(18, 0))
            self.compact_button.configure(text="Compact")
            self.minsize(760, 520)
            if self.full_geometry_before_compact:
                self.geometry(self.full_geometry_before_compact)

    def on_mode_changed(self) -> None:
        if "dungeon_enabled" not in self.vars:
            return
        self.vars["dungeon_enabled"].set(self.vars["mode"].get() == "Dungeon")

    def build_combat_tab(self) -> None:
        tab = self.create_scrollable_tab("Actions")
        attack = ttk.LabelFrame(tab, text="Farming Attack")
        attack.pack(fill="x", pady=(0, 10))
        self.vars["attack_enabled"] = tk.BooleanVar()
        self.vars["attack_key"] = tk.StringVar()
        self.vars["attack_delay_ms"] = tk.StringVar()
        ttk.Checkbutton(attack, text="Enable attack", variable=self.vars["attack_enabled"]).grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.grid_combo(attack, 0, 1, "Attack key", self.vars["attack_key"], KEY_OPTIONS, 12)
        self.grid_entry(attack, 0, 3, "Attack delay (ms)", self.vars["attack_delay_ms"], 12)

        skills = ttk.LabelFrame(tab, text="Skills and Buffs")
        skills.pack(fill="both", expand=True)
        headers = ["Active", "Name", "Key", "Interval (ms)", "Cast pause (ms)", "Taps"]
        for col, header in enumerate(headers):
            ttk.Label(skills, text=header, font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=6, pady=4, sticky="w")
        for idx in range(8):
            row: dict[str, Any] = {
                "enabled": tk.BooleanVar(),
                "name": tk.StringVar(),
                "key": tk.StringVar(),
                "interval_ms": tk.StringVar(),
                "cast_pause_ms": tk.StringVar(),
                "taps": tk.StringVar(),
            }
            self.skill_rows.append(row)
            ttk.Checkbutton(skills, variable=row["enabled"]).grid(row=idx + 1, column=0, padx=6, pady=4)
            ttk.Entry(skills, textvariable=row["name"], width=20).grid(row=idx + 1, column=1, padx=6, pady=4, sticky="ew")
            ttk.Combobox(skills, textvariable=row["key"], width=12, values=KEY_OPTIONS).grid(row=idx + 1, column=2, padx=6, pady=4)
            ttk.Entry(skills, textvariable=row["interval_ms"], width=14).grid(row=idx + 1, column=3, padx=6, pady=4)
            ttk.Entry(skills, textvariable=row["cast_pause_ms"], width=14).grid(row=idx + 1, column=4, padx=6, pady=4)
            ttk.Entry(skills, textvariable=row["taps"], width=7).grid(row=idx + 1, column=5, padx=6, pady=4)
        skills.columnconfigure(1, weight=1)

    def build_detectors_tab(self) -> None:
        tab = self.create_scrollable_tab("Detections")
        headers = ["Active", "Name", "Mode", "Image", "Confidence", "Action", "Custom key", "Cooldown"]
        for col, header in enumerate(headers):
            ttk.Label(tab, text=header, font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=4, pady=4, sticky="w")
        for idx in range(4):
            row: dict[str, Any] = {
                "enabled": tk.BooleanVar(),
                "name": tk.StringVar(),
                "mode": tk.StringVar(),
                "image": tk.StringVar(),
                "confidence": tk.StringVar(),
                "action": tk.StringVar(),
                "custom_key": tk.StringVar(),
                "cooldown_ms": tk.StringVar(),
            }
            self.detector_rows.append(row)
            ttk.Checkbutton(tab, variable=row["enabled"]).grid(row=idx + 1, column=0, padx=4, pady=4)
            ttk.Entry(tab, textvariable=row["name"], width=14).grid(row=idx + 1, column=1, padx=4, pady=4)
            ttk.Combobox(tab, textvariable=row["mode"], values=MODE_OPTIONS, width=10, state="readonly").grid(row=idx + 1, column=2, padx=4, pady=4)
            ttk.Entry(tab, textvariable=row["image"], width=28).grid(row=idx + 1, column=3, padx=4, pady=4, sticky="ew")
            ttk.Button(tab, text="Browse", command=lambda r=row: self.pick_file(r["image"])).grid(row=idx + 1, column=4, padx=4, pady=4)
            ttk.Entry(tab, textvariable=row["confidence"], width=8).grid(row=idx + 1, column=5, padx=4, pady=4)
            combo = ttk.Combobox(tab, textvariable=row["action"], width=16, values=["Press Enter", "Hold Space 3s", "Click Death OK", "Click Image", "Press Custom Key", "None"], state="readonly")
            combo.grid(row=idx + 1, column=6, padx=4, pady=4)
            ttk.Combobox(tab, textvariable=row["custom_key"], width=10, values=KEY_OPTIONS).grid(row=idx + 1, column=7, padx=4, pady=4)
            ttk.Entry(tab, textvariable=row["cooldown_ms"], width=9).grid(row=idx + 1, column=8, padx=4, pady=4)
        tab.columnconfigure(3, weight=1)

    def build_ocr_tab(self) -> None:
        tab = self.create_scrollable_tab("Lie Detector")
        self.vars["ocr_enabled"] = tk.BooleanVar()
        self.vars["ocr_relative_to_popup"] = tk.BooleanVar()
        self.vars["ocr_cookbot_label_preset"] = tk.BooleanVar()
        self.vars["ocr_popup_image"] = tk.StringVar()
        self.vars["ocr_popup_confidence"] = tk.StringVar()
        self.vars["ocr_check_interval_ms"] = tk.StringVar()
        self.vars["ocr_region_x"] = tk.StringVar()
        self.vars["ocr_region_y"] = tk.StringVar()
        self.vars["ocr_region_w"] = tk.StringVar()
        self.vars["ocr_region_h"] = tk.StringVar()
        self.vars["ocr_input_x"] = tk.StringVar()
        self.vars["ocr_input_y"] = tk.StringVar()
        self.vars["ocr_result_x"] = tk.StringVar()
        self.vars["ocr_result_y"] = tk.StringVar()
        self.vars["ocr_result_w"] = tk.StringVar()
        self.vars["ocr_result_h"] = tk.StringVar()
        self.vars["ocr_max_attempts"] = tk.StringVar()
        self.vars["ocr_max_failures"] = tk.StringVar()
        self.vars["ocr_popup_settle_delay_ms"] = tk.StringVar()
        self.vars["ocr_retry_delay_ms"] = tk.StringVar()
        self.vars["ocr_result_delay_ms"] = tk.StringVar()
        self.vars["ocr_tesseract_path"] = tk.StringVar()

        ttk.Checkbutton(tab, text="Enable Lie Detector OCR (Farming only)", variable=self.vars["ocr_enabled"]).pack(anchor="w", pady=(0, 10))
        popup = ttk.LabelFrame(tab, text="Popup detection")
        popup.pack(fill="x", pady=6)
        ttk.Checkbutton(popup, text="Popup-relative X/Y", variable=self.vars["ocr_relative_to_popup"]).pack(anchor="w", padx=12, pady=(8, 0))
        ttk.Checkbutton(popup, text="Cookbot label preset", variable=self.vars["ocr_cookbot_label_preset"]).pack(anchor="w", padx=12, pady=(4, 0))
        self.path_row(popup, "Lie Detector image", self.vars["ocr_popup_image"])
        self.inline_entries(popup, [("Confidence", "ocr_popup_confidence"), ("Check every (ms)", "ocr_check_interval_ms")])

        region = ttk.LabelFrame(tab, text="Code region to read")
        region.pack(fill="x", pady=6)
        self.inline_entries(region, [("X", "ocr_region_x"), ("Y", "ocr_region_y"), ("W", "ocr_region_w"), ("H", "ocr_region_h")])

        click = ttk.LabelFrame(tab, text="Input field click")
        click.pack(fill="x", pady=6)
        self.inline_entries(click, [("X", "ocr_input_x"), ("Y", "ocr_input_y")])

        result = ttk.LabelFrame(tab, text="Result text region")
        result.pack(fill="x", pady=6)
        self.inline_entries(result, [("X", "ocr_result_x"), ("Y", "ocr_result_y"), ("W", "ocr_result_w"), ("H", "ocr_result_h")])

        failsafe = ttk.LabelFrame(tab, text="Failsafe")
        failsafe.pack(fill="x", pady=6)
        self.inline_entries(failsafe, [
            ("Max attempts", "ocr_max_attempts"),
            ("Max failures", "ocr_max_failures"),
            ("Popup settle (ms)", "ocr_popup_settle_delay_ms"),
            ("Retry delay (ms)", "ocr_retry_delay_ms"),
            ("Result delay (ms)", "ocr_result_delay_ms"),
        ])

        settings = ttk.LabelFrame(tab, text="Tesseract")
        settings.pack(fill="x", pady=6)
        self.path_row(settings, "tesseract.exe path", self.vars["ocr_tesseract_path"])

    def build_dungeon_tab(self) -> None:
        tab = self.create_scrollable_tab("Dungeon")
        self.vars["dungeon_enabled"] = tk.BooleanVar(value=True)
        self.vars["dungeon_role"] = tk.StringVar()
        self.vars["dungeon_drop_option"] = tk.StringVar()
        self.vars["dungeon_custom_coins"] = tk.StringVar()
        for key in [
            "dungeon_npc_image", "dungeon_finish_image", "dungeon_char_image", "dungeon_portal_image", "dungeon_confidence",
            "dungeon_playfield_x", "dungeon_playfield_y", "dungeon_playfield_w", "dungeon_playfield_h",
            "dungeon_minimap_x", "dungeon_minimap_y", "dungeon_minimap_w", "dungeon_minimap_h",
            "dungeon_home_x", "dungeon_home_y", "dungeon_tolerance_px", "dungeon_npc_offset_x",
            "dungeon_npc_offset_y", "dungeon_portal_offset_x", "dungeon_portal_offset_y",
            "dungeon_portal_x", "dungeon_portal_y", "dungeon_death_ok_x", "dungeon_death_ok_y",
            "dungeon_henesys_wait_after_exit_sec", "dungeon_return_home_every_ms",
        ]:
            self.vars[key] = tk.StringVar()
        self.vars["dungeon_dialog_steps"] = None

        flow = ttk.LabelFrame(tab, text="Dungeon flow")
        flow.pack(fill="x", pady=(0, 8))
        self.inline_entries(flow, [("Custom coins", "dungeon_custom_coins")])
        row = ttk.Frame(flow)
        row.pack(fill="x", padx=12, pady=8)
        ttk.Label(row, text="Role").pack(side="left", padx=(0, 6))
        ttk.Combobox(row, textvariable=self.vars["dungeon_role"], values=["Leader", "Leecher"], width=12, state="readonly").pack(side="left", padx=(0, 18))
        ttk.Label(row, text="Drops").pack(side="left", padx=(0, 6))
        ttk.Combobox(row, textvariable=self.vars["dungeon_drop_option"], values=["4 drops", "8 drops", "12 drops", "24 drops", "Custom Drops"], width=16, state="readonly").pack(side="left", padx=(0, 18))

        images = ttk.LabelFrame(tab, text="Images")
        images.pack(fill="x", pady=5)
        self.path_row(images, "NPC image", self.vars["dungeon_npc_image"])
        self.path_row(images, "Finish banner", self.vars["dungeon_finish_image"])
        self.path_row(images, "Purple portal image", self.vars["dungeon_portal_image"])
        self.inline_entries(images, [("Confidence", "dungeon_confidence")])

        playfield = ttk.LabelFrame(tab, text="Search area (optional)")
        playfield.pack(fill="x", pady=5)
        ttk.Label(
            playfield,
            text="Limits image search for character, finish banner, and portal. Leave W/H as 0 to search the full screen.",
            foreground="#9fb3c8",
            wraplength=760,
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.inline_entries(playfield, [
            ("X", "dungeon_playfield_x"), ("Y", "dungeon_playfield_y"),
            ("W", "dungeon_playfield_w"), ("H", "dungeon_playfield_h"),
        ])

        minimap = ttk.LabelFrame(tab, text="Minimap tracking")
        minimap.pack(fill="x", pady=5)
        ttk.Label(
            minimap,
            text="Set the full minimap box here. The bot tracks the small yellow character marker and uses Minimap Home X/Y as screen coordinates.",
            foreground="#9fb3c8",
            wraplength=760,
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self.inline_entries(minimap, [
            ("Minimap X", "dungeon_minimap_x"), ("Minimap Y", "dungeon_minimap_y"),
            ("Minimap W", "dungeon_minimap_w"), ("Minimap H", "dungeon_minimap_h"),
        ])

        pos = ttk.LabelFrame(tab, text="Minimap home and portal positions")
        pos.pack(fill="x", pady=5)
        self.inline_entries(pos, [
            ("Minimap Home X", "dungeon_home_x"), ("Minimap Home Y", "dungeon_home_y"), ("Tolerance px", "dungeon_tolerance_px"),
            ("NPC click X", "dungeon_npc_offset_x"), ("NPC click Y", "dungeon_npc_offset_y"),
            ("Portal offset X", "dungeon_portal_offset_x"), ("Portal offset Y", "dungeon_portal_offset_y"),
            ("Portal X", "dungeon_portal_x"), ("Portal Y", "dungeon_portal_y"),
            ("Death OK X", "dungeon_death_ok_x"), ("Death OK Y", "dungeon_death_ok_y"),
            ("Wait in Henesys (sec)", "dungeon_henesys_wait_after_exit_sec"),
            ("Check home every (ms)", "dungeon_return_home_every_ms"),
        ])

        steps = ttk.LabelFrame(tab, text="NPC dialog steps")
        steps.pack(fill="both", expand=True, pady=5)
        hint = "Syntax: wait:1 | press:enter | type:text | click:x,y"
        ttk.Label(steps, text=hint, foreground="#9fb3c8").pack(anchor="w", padx=8, pady=(6, 2))
        self.dialog_text = tk.Text(steps, height=7, bg=UI_PANEL_DARK, fg=UI_TEXT, insertbackground=UI_TEXT, relief="flat")
        self.dialog_text.pack(fill="both", expand=True, padx=8, pady=6)

    def build_command_tab(self) -> None:
        tab = self.create_scrollable_tab("Command")
        self.vars["command_enabled"] = tk.BooleanVar()
        self.vars["command_text"] = tk.StringVar()
        self.vars["command_every_sec"] = tk.StringVar()
        self.vars["command_step_delay_ms"] = tk.StringVar()
        ttk.Checkbutton(tab, text="Enable scheduled command", variable=self.vars["command_enabled"]).pack(anchor="w", pady=8)
        self.entry_row(tab, "Text to type", self.vars["command_text"], width=40)
        self.entry_row(tab, "Every seconds", self.vars["command_every_sec"], width=12)
        self.entry_row(tab, "Step delay ms", self.vars["command_step_delay_ms"], width=12)
        sequence = (
            "Sequence:\n"
            "1. Press Enter\n"
            "2. Type command text\n"
            "3. Press Enter again"
        )
        ttk.Label(tab, text=sequence, justify="left").pack(anchor="w", pady=16)

    def build_log_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab, text="Log")
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Activity Log", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Label(toolbar, text="Newest events appear at the bottom", style="Muted.TLabel").pack(side="left", padx=(12, 0))
        ttk.Button(toolbar, text="Clear", command=self.clear_log).pack(side="right")

        frame = ttk.Frame(tab, style="Card.TFrame", padding=10)
        frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            frame,
            bg=UI_PANEL_DARK,
            fg=UI_TEXT,
            insertbackground=UI_TEXT,
            relief="flat",
            borderwidth=0,
            font=("Cascadia Mono", 10),
            padx=10,
            pady=10,
            wrap="word",
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.log_text.tag_configure("time", foreground=UI_GREEN)
        self.log_text.tag_configure("start", foreground=UI_GREEN)
        self.log_text.tag_configure("stop", foreground=UI_RED)
        self.log_text.tag_configure("warning", foreground=UI_YELLOW)
        self.log_text.tag_configure("error", foreground=UI_RED)
        self.log_text.tag_configure("normal", foreground=UI_TEXT)

    def entry_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, width: int = 18) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=7)
        ttk.Label(frame, text=label, width=16).pack(side="left")
        ttk.Entry(frame, textvariable=variable, width=width).pack(side="left", fill="x", expand=True)

    def grid_entry(self, parent: ttk.Frame, row: int, col: int, label: str, variable: tk.StringVar, width: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, padx=8, pady=8)
        ttk.Entry(parent, textvariable=variable, width=width).grid(row=row, column=col + 1, padx=8, pady=8)

    def grid_combo(self, parent: ttk.Frame, row: int, col: int, label: str, variable: tk.StringVar, values: list[str], width: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, padx=8, pady=8)
        ttk.Combobox(parent, textvariable=variable, values=values, width=width).grid(row=row, column=col + 1, padx=8, pady=8)

    def combo_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[str], width: int = 18) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=7)
        ttk.Label(frame, text=label, width=16).pack(side="left")
        ttk.Combobox(frame, textvariable=variable, values=values, width=width).pack(side="left", fill="x", expand=True)

    def path_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=12, pady=8)
        ttk.Label(frame, text=label, width=22).pack(side="left")
        ttk.Entry(frame, textvariable=variable).pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Browse", command=lambda: self.pick_file(variable)).pack(side="left", padx=(6, 0))

    def inline_entries(self, parent: ttk.Frame, items: list[tuple[str, str]]) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=12, pady=8)
        max_pairs_per_row = 3
        for index, (label, key) in enumerate(items):
            row = index // max_pairs_per_row
            col = (index % max_pairs_per_row) * 2
            ttk.Label(frame, text=label).grid(row=row, column=col, padx=(0, 6), pady=5, sticky="w")
            ttk.Entry(frame, textvariable=self.vars[key], width=10).grid(row=row, column=col + 1, padx=(0, 18), pady=5, sticky="w")
        for col in range(max_pairs_per_row * 2):
            frame.columnconfigure(col, weight=0)

    def pick_file(self, variable: tk.StringVar) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images and executables", "*.png *.jpg *.jpeg *.bmp *.exe"), ("All files", "*.*")])
        if path:
            variable.set(path)

    def capture_mouse(self, keys: list[str], label: str) -> None:
        if pyautogui is None:
            messagebox.showerror("Missing dependency", "pyautogui is not installed.")
            return
        self.pending_mouse_capture = keys
        self.pending_mouse_label = label
        hotkey = self.vars.get("mouse_hotkey")
        hotkey_text = hotkey.get().upper() if hotkey else "F3"
        self.enqueue_log(f"{label} armed. Press {hotkey_text} to capture the current mouse position.")

    def capture_playfield_bottom_right(self) -> None:
        if pyautogui is None:
            messagebox.showerror("Missing dependency", "pyautogui is not installed.")
            return
        self.pending_mouse_capture = ["__playfield_bottom_right__"]
        self.pending_mouse_label = "Playfield bottom-right"
        hotkey = self.vars.get("mouse_hotkey")
        hotkey_text = hotkey.get().upper() if hotkey else "F3"
        self.enqueue_log(f"Playfield bottom-right armed. Press {hotkey_text} to calculate width and height.")

    def _capture_mouse_now(self, keys: Optional[list[str]] = None) -> None:
        if pyautogui is None:
            return
        x, y = pyautogui.position()
        self.show_cursor_coordinates(x, y)
        keys = keys or self.pending_mouse_capture
        if not keys:
            self.enqueue_log(f"Mouse position: {x}, {y}")
            return
        if keys == ["__playfield_bottom_right__"]:
            left = parse_int(self.vars["dungeon_playfield_x"].get(), 0)
            top = parse_int(self.vars["dungeon_playfield_y"].get(), 0)
            self.vars["dungeon_playfield_w"].set(str(max(0, x - left)))
            self.vars["dungeon_playfield_h"].set(str(max(0, y - top)))
            self.pending_mouse_capture = None
            self.pending_mouse_label = ""
            self.enqueue_log(f"Playfield size captured: {max(0, x - left)} x {max(0, y - top)}")
            return
        self.vars[keys[0]].set(str(x))
        self.vars[keys[1]].set(str(y))
        label = self.pending_mouse_label or "Mouse position"
        self.pending_mouse_capture = None
        self.pending_mouse_label = ""
        self.enqueue_log(f"{label} captured: {x}, {y}")

    def show_cursor_coordinates(self, x: int, y: int) -> None:
        bubble = tk.Toplevel(self)
        bubble.overrideredirect(True)
        bubble.attributes("-topmost", True)
        bubble.configure(bg=UI_CYAN)
        label = tk.Label(
            bubble,
            text=f"X {x}  Y {y}",
            bg=UI_PANEL_DARK,
            fg=UI_CYAN,
            font=("Cascadia Mono", 10, "bold"),
            padx=10,
            pady=5,
        )
        label.pack(padx=1, pady=1)
        bubble.geometry(f"+{x + 18}+{y + 18}")
        bubble.after(1300, bubble.destroy)

    def toggle_cursor_tracking(self) -> None:
        self.cursor_tracking_enabled = not self.cursor_tracking_enabled
        state = "ON" if self.cursor_tracking_enabled else "OFF"
        if hasattr(self, "cursor_tracking_var"):
            self.cursor_tracking_var.set(f"F3: {state}")
        if pyautogui is not None:
            x, y = pyautogui.position()
            self.show_cursor_coordinates(x, y)
        self.enqueue_log(f"Cursor position display: {state}")

    def update_cursor_position(self) -> None:
        if self.cursor_tracking_enabled and pyautogui is not None and hasattr(self, "cursor_x_var"):
            x, y = pyautogui.position()
            self.cursor_x_var.set(f"X: {x}")
            self.cursor_y_var.set(f"Y: {y}")
        self.after(120, self.update_cursor_position)

    def start_bot(self) -> None:
        try:
            cfg = self.read_config_from_ui()
            self.backend.start(cfg)
            self.started_at = time.monotonic()
            self.set_status("Active")
            self.tick_timer()
        except Exception as exc:
            messagebox.showerror("Cannot start bot", str(exc))
            self.enqueue_log("Start failed: " + str(exc))

    def stop_bot(self) -> None:
        self.backend.stop()
        self.set_status("Stopped")

    def set_status(self, value: str) -> None:
        self.status_var.set(value)
        if hasattr(self, "compact_status_var"):
            self.compact_status_var.set(value)

    def tick_timer(self) -> None:
        if not self.backend.running:
            return
        elapsed = int(time.monotonic() - getattr(self, "started_at", time.monotonic()))
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self.tick_timer)

    def hotkey_poll(self) -> None:
        try:
            start_key = normalize_key(self.vars["start_hotkey"].get())
            stop_key = normalize_key(self.vars["stop_hotkey"].get())
            mouse_key = normalize_key(self.vars["mouse_hotkey"].get())
            if start_key:
                self.check_hotkey(start_key, self.start_bot)
            if stop_key:
                self.check_hotkey(stop_key, self.stop_bot)
            if mouse_key:
                self.check_hotkey(mouse_key, self.toggle_cursor_tracking)
        except Exception as exc:
            self.enqueue_log(f"Hotkey polling error: {exc}")
        self.after(80, self.hotkey_poll)

    def check_hotkey(self, key: str, action: Callable[[], None]) -> None:
        pressed = is_hotkey_pressed(key)
        if pressed and key not in self.hotkey_latch:
            self.hotkey_latch.add(key)
            action()
        elif not pressed and key in self.hotkey_latch:
            self.hotkey_latch.remove(key)

    def enqueue_log(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{stamp}] {text}")

    def clear_log(self) -> None:
        self.log_text.delete("1.0", "end")
        self.log_lines.clear()
        self.update_compact_log()

    def log_tag_for(self, line: str) -> str:
        lower = line.lower()
        if "started" in lower or "captured" in lower or "detected" in lower:
            return "start"
        if "stopped" in lower:
            return "stop"
        if "not found" in lower or "no mouse capture" in lower or "missing" in lower:
            return "warning"
        if "error" in lower or "failed" in lower:
            return "error"
        return "normal"

    def drain_log(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_lines.append(line)
            self.log_lines = self.log_lines[-500:]
            self.insert_log_line(self.log_text, line)
            self.log_text.see("end")
            self.update_compact_log()
        self.after(100, self.drain_log)

    def insert_log_line(self, widget: tk.Text, line: str) -> None:
        time_end = line.find("]") + 1
        tag = self.log_tag_for(line)
        if time_end > 0:
            widget.insert("end", line[:time_end], "time")
            widget.insert("end", line[time_end:] + "\n", tag)
        else:
            widget.insert("end", line + "\n", tag)

    def update_compact_log(self) -> None:
        if not hasattr(self, "compact_log"):
            return
        self.compact_log.delete("1.0", "end")
        for line in self.log_lines[-3:]:
            self.insert_log_line(self.compact_log, line)
        self.compact_log.see("end")

    def read_config_from_ui(self) -> BotConfig:
        cfg = BotConfig()
        cfg.mode = self.vars["mode"].get()
        cfg.game_window = REQUIRED_GAME_WINDOW
        cfg.keyboard_layout = self.vars["keyboard_layout"].get()
        cfg.start_hotkey = self.vars["start_hotkey"].get()
        cfg.stop_hotkey = self.vars["stop_hotkey"].get()
        cfg.mouse_hotkey = self.vars["mouse_hotkey"].get()
        cfg.attack_enabled = self.vars["attack_enabled"].get()
        cfg.attack_key = self.vars["attack_key"].get()
        cfg.attack_delay_ms = parse_int(self.vars["attack_delay_ms"].get(), 250)
        cfg.command_enabled = self.vars["command_enabled"].get()
        cfg.command_text = self.vars["command_text"].get()
        cfg.command_every_sec = parse_int(self.vars["command_every_sec"].get(), 360)
        cfg.command_step_delay_ms = parse_int(self.vars["command_step_delay_ms"].get(), 250)
        cfg.skills = [
            SkillConfig(
                row["enabled"].get(),
                row["name"].get(),
                row["key"].get(),
                parse_int(row["interval_ms"].get(), 3000),
                parse_int(row["cast_pause_ms"].get(), 250),
                parse_int(row["taps"].get(), 1),
            )
            for row in self.skill_rows
        ]
        cfg.detectors = [
            DetectorConfig(
                row["enabled"].get(), row["name"].get(), row["mode"].get(), row["image"].get(),
                parse_float(row["confidence"].get(), 0.8), row["action"].get(),
                row["custom_key"].get(), parse_int(row["cooldown_ms"].get(), 1500)
            )
            for row in self.detector_rows
        ]
        cfg.ocr = OcrConfig(
            self.vars["ocr_enabled"].get(),
            self.vars["ocr_popup_image"].get(),
            parse_float(self.vars["ocr_popup_confidence"].get(), 0.75),
            self.vars["ocr_relative_to_popup"].get(),
            self.vars["ocr_cookbot_label_preset"].get(),
            parse_int(self.vars["ocr_check_interval_ms"].get(), 5000),
            parse_int(self.vars["ocr_region_x"].get(), 0),
            parse_int(self.vars["ocr_region_y"].get(), 0),
            parse_int(self.vars["ocr_region_w"].get(), 240),
            parse_int(self.vars["ocr_region_h"].get(), 32),
            parse_int(self.vars["ocr_input_x"].get(), 0),
            parse_int(self.vars["ocr_input_y"].get(), 0),
            parse_int(self.vars["ocr_result_x"].get(), 0),
            parse_int(self.vars["ocr_result_y"].get(), 0),
            parse_int(self.vars["ocr_result_w"].get(), 360),
            parse_int(self.vars["ocr_result_h"].get(), 90),
            parse_int(self.vars["ocr_max_attempts"].get(), 3),
            parse_int(self.vars["ocr_max_failures"].get(), 2),
            parse_int(self.vars["ocr_popup_settle_delay_ms"].get(), 3000),
            parse_int(self.vars["ocr_retry_delay_ms"].get(), 1500),
            parse_int(self.vars["ocr_result_delay_ms"].get(), 800),
            self.vars["ocr_tesseract_path"].get(),
        )
        cfg.dungeon = DungeonConfig(
            self.vars["mode"].get() == "Dungeon" or self.vars["dungeon_enabled"].get(),
            self.vars["dungeon_role"].get(),
            self.vars["dungeon_drop_option"].get(),
            parse_int(self.vars["dungeon_custom_coins"].get(), 1),
            self.vars["dungeon_npc_image"].get(),
            self.vars["dungeon_finish_image"].get(),
            self.vars["dungeon_char_image"].get(),
            self.vars["dungeon_portal_image"].get(),
            parse_float(self.vars["dungeon_confidence"].get(), 0.8),
            parse_int(self.vars["dungeon_playfield_x"].get(), 0),
            parse_int(self.vars["dungeon_playfield_y"].get(), 0),
            parse_int(self.vars["dungeon_playfield_w"].get(), 0),
            parse_int(self.vars["dungeon_playfield_h"].get(), 0),
            parse_int(self.vars["dungeon_minimap_x"].get(), 0),
            parse_int(self.vars["dungeon_minimap_y"].get(), 0),
            parse_int(self.vars["dungeon_minimap_w"].get(), 0),
            parse_int(self.vars["dungeon_minimap_h"].get(), 0),
            parse_int(self.vars["dungeon_home_x"].get(), 0),
            parse_int(self.vars["dungeon_home_y"].get(), 0),
            parse_int(self.vars["dungeon_tolerance_px"].get(), 12),
            parse_int(self.vars["dungeon_npc_offset_x"].get(), 10),
            parse_int(self.vars["dungeon_npc_offset_y"].get(), 10),
            parse_int(self.vars["dungeon_portal_offset_x"].get(), 0),
            parse_int(self.vars["dungeon_portal_offset_y"].get(), 0),
            parse_int(self.vars["dungeon_portal_x"].get(), 0),
            parse_int(self.vars["dungeon_portal_y"].get(), 0),
            parse_int(self.vars["dungeon_death_ok_x"].get(), 0),
            parse_int(self.vars["dungeon_death_ok_y"].get(), 0),
            parse_int(self.vars["dungeon_henesys_wait_after_exit_sec"].get(), 10),
            self.dialog_text.get("1.0", "end").strip(),
            parse_int(self.vars["dungeon_return_home_every_ms"].get(), 750),
        )
        return cfg

    def write_config_to_ui(self, cfg: BotConfig) -> None:
        self.vars["mode"].set(cfg.mode)
        self.vars["game_window"].set(REQUIRED_GAME_WINDOW)
        self.vars["keyboard_layout"].set(cfg.keyboard_layout)
        self.vars["start_hotkey"].set(cfg.start_hotkey)
        self.vars["stop_hotkey"].set(cfg.stop_hotkey)
        self.vars["mouse_hotkey"].set(cfg.mouse_hotkey)
        self.vars["attack_enabled"].set(cfg.attack_enabled)
        self.vars["attack_key"].set(cfg.attack_key)
        self.vars["attack_delay_ms"].set(str(cfg.attack_delay_ms))
        self.vars["command_enabled"].set(cfg.command_enabled)
        self.vars["command_text"].set(cfg.command_text)
        self.vars["command_every_sec"].set(str(cfg.command_every_sec))
        self.vars["command_step_delay_ms"].set(str(cfg.command_step_delay_ms))
        for row, skill in zip(self.skill_rows, cfg.skills):
            row["enabled"].set(skill.enabled)
            row["name"].set(skill.name)
            row["key"].set(skill.key)
            row["interval_ms"].set(str(skill.interval_ms))
            row["cast_pause_ms"].set(str(skill.cast_pause_ms))
            row["taps"].set(str(skill.taps))
        for row, detector in zip(self.detector_rows, cfg.detectors):
            row["enabled"].set(detector.enabled)
            row["name"].set(detector.name)
            row["mode"].set(detector.mode)
            row["image"].set(resolve_template_path(detector.image))
            row["confidence"].set(str(detector.confidence))
            row["action"].set(detector.action)
            row["custom_key"].set(detector.custom_key)
            row["cooldown_ms"].set(str(detector.cooldown_ms))
        ocr = cfg.ocr
        self.vars["ocr_enabled"].set(ocr.enabled)
        self.vars["ocr_popup_image"].set(resolve_template_path(ocr.popup_image))
        self.vars["ocr_popup_confidence"].set(str(ocr.popup_confidence))
        self.vars["ocr_relative_to_popup"].set(ocr.relative_to_popup)
        self.vars["ocr_cookbot_label_preset"].set(ocr.cookbot_label_preset)
        self.vars["ocr_check_interval_ms"].set(str(ocr.check_interval_ms))
        self.vars["ocr_region_x"].set(str(ocr.region_x))
        self.vars["ocr_region_y"].set(str(ocr.region_y))
        self.vars["ocr_region_w"].set(str(ocr.region_w))
        self.vars["ocr_region_h"].set(str(ocr.region_h))
        self.vars["ocr_input_x"].set(str(ocr.input_x))
        self.vars["ocr_input_y"].set(str(ocr.input_y))
        self.vars["ocr_result_x"].set(str(ocr.result_x))
        self.vars["ocr_result_y"].set(str(ocr.result_y))
        self.vars["ocr_result_w"].set(str(ocr.result_w))
        self.vars["ocr_result_h"].set(str(ocr.result_h))
        self.vars["ocr_max_attempts"].set(str(ocr.max_attempts))
        self.vars["ocr_max_failures"].set(str(ocr.max_failures))
        self.vars["ocr_popup_settle_delay_ms"].set(str(ocr.popup_settle_delay_ms))
        self.vars["ocr_retry_delay_ms"].set(str(ocr.retry_delay_ms))
        self.vars["ocr_result_delay_ms"].set(str(ocr.result_delay_ms))
        self.vars["ocr_tesseract_path"].set(ocr.tesseract_path)
        dungeon = cfg.dungeon
        self.vars["dungeon_enabled"].set(dungeon.enabled)
        self.vars["dungeon_role"].set(dungeon.role)
        self.vars["dungeon_drop_option"].set(dungeon.drop_option)
        self.vars["dungeon_custom_coins"].set(str(dungeon.custom_coins))
        self.vars["dungeon_npc_image"].set(resolve_template_path(dungeon.npc_image))
        self.vars["dungeon_finish_image"].set(resolve_template_path(dungeon.finish_image))
        self.vars["dungeon_char_image"].set(resolve_template_path(dungeon.char_image))
        self.vars["dungeon_portal_image"].set(resolve_template_path(dungeon.portal_image))
        self.vars["dungeon_confidence"].set(str(dungeon.confidence))
        self.vars["dungeon_playfield_x"].set(str(dungeon.playfield_x))
        self.vars["dungeon_playfield_y"].set(str(dungeon.playfield_y))
        self.vars["dungeon_playfield_w"].set(str(dungeon.playfield_w))
        self.vars["dungeon_playfield_h"].set(str(dungeon.playfield_h))
        self.vars["dungeon_minimap_x"].set(str(dungeon.minimap_x))
        self.vars["dungeon_minimap_y"].set(str(dungeon.minimap_y))
        self.vars["dungeon_minimap_w"].set(str(dungeon.minimap_w))
        self.vars["dungeon_minimap_h"].set(str(dungeon.minimap_h))
        self.vars["dungeon_home_x"].set(str(dungeon.home_x))
        self.vars["dungeon_home_y"].set(str(dungeon.home_y))
        self.vars["dungeon_tolerance_px"].set(str(dungeon.tolerance_px))
        self.vars["dungeon_npc_offset_x"].set(str(dungeon.npc_offset_x))
        self.vars["dungeon_npc_offset_y"].set(str(dungeon.npc_offset_y))
        self.vars["dungeon_portal_offset_x"].set(str(dungeon.portal_offset_x))
        self.vars["dungeon_portal_offset_y"].set(str(dungeon.portal_offset_y))
        self.vars["dungeon_portal_x"].set(str(dungeon.portal_x))
        self.vars["dungeon_portal_y"].set(str(dungeon.portal_y))
        self.vars["dungeon_death_ok_x"].set(str(dungeon.death_ok_x))
        self.vars["dungeon_death_ok_y"].set(str(dungeon.death_ok_y))
        self.vars["dungeon_henesys_wait_after_exit_sec"].set(str(dungeon.henesys_wait_after_exit_sec))
        self.vars["dungeon_return_home_every_ms"].set(str(dungeon.return_home_every_ms))
        self.dialog_text.delete("1.0", "end")
        dialog_steps = "" if dungeon.dialog_steps.strip() == LEGACY_DUNGEON_DIALOG_STEPS else dungeon.dialog_steps
        self.dialog_text.insert("1.0", dialog_steps)
        self.on_mode_changed()

    def save_config_dialog(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="meowmeowbot_config.json")
        if path:
            self.save_config(Path(path))

    def load_config_dialog(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            self.load_config(Path(path))

    def save_config(self, path: Path) -> None:
        cfg = self.read_config_from_ui()
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(asdict(cfg), handle, indent=2)
        self.enqueue_log(f"Config saved: {path}")

    def load_config(self, path: Path, quiet: bool = False) -> None:
        if not path.exists():
            self.write_config_to_ui(default_config())
            return
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        cfg = self.config_from_dict(raw)
        self.write_config_to_ui(cfg)
        if not quiet:
            self.enqueue_log(f"Config loaded: {path}")

    def config_from_dict(self, raw: dict[str, Any]) -> BotConfig:
        cfg = default_config()
        for key in ["mode", "keyboard_layout", "start_hotkey", "stop_hotkey", "mouse_hotkey", "attack_enabled", "attack_key", "attack_delay_ms", "command_enabled", "command_text", "command_every_sec", "command_step_delay_ms"]:
            if key in raw:
                setattr(cfg, key, raw[key])
        cfg.game_window = REQUIRED_GAME_WINDOW
        cfg.skills = []
        for item in raw.get("skills", asdict(cfg)["skills"]):
            default_taps = 2 if str(item.get("name", "")).lower() == "buff" else 1
            merged = {"cast_pause_ms": 250, "taps": default_taps, **item}
            cfg.skills.append(SkillConfig(**merged))
        cfg.detectors = []
        for item in raw.get("detectors", asdict(cfg)["detectors"]):
            merged = {"mode": "Farming", **item}
            cfg.detectors.append(DetectorConfig(**merged))
        ocr_raw = {**asdict(cfg)["ocr"], **raw.get("ocr", {})}
        ocr_raw.setdefault("cookbot_label_preset", True)
        cfg.ocr = OcrConfig(**ocr_raw)
        dungeon_raw = {**asdict(cfg)["dungeon"], **raw.get("dungeon", {})}
        if str(dungeon_raw.get("dialog_steps", "")).strip() == LEGACY_DUNGEON_DIALOG_STEPS:
            dungeon_raw["dialog_steps"] = ""
        cfg.dungeon = DungeonConfig(**dungeon_raw)
        return cfg


def main() -> None:
    app = MapleBotApp()
    app.mainloop()


if __name__ == "__main__":
    main()
