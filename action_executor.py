import pyautogui
import time
import os
import subprocess
import webbrowser
from typing import Any, Dict, List, Optional, Tuple
from difflib import get_close_matches

# Optional: for window activation
try:
    import pygetwindow as gw
except:
    gw = None

# ---------------- Helper functions ---------------- #

def _center_of_bbox(bbox: Any) -> Optional[Tuple[int, int]]:
    try:
        screen_w, screen_h = pyautogui.size()
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            if 0 <= x1 <= 1 and 0 <= x2 <= 1:
                x1 *= screen_w
                x2 *= screen_w
            if 0 <= y1 <= 1 and 0 <= y2 <= 1:
                y1 *= screen_h
                y2 *= screen_h
            return int((x1 + x2) / 2), int((y1 + y2) / 2)
        if isinstance(bbox, dict) and {"left","top","right","bottom"}.issubset(bbox.keys()):
            x1, y1, x2, y2 = bbox["left"], bbox["top"], bbox["right"], bbox["bottom"]
            if 0 <= x1 <= 1 and 0 <= x2 <= 1:
                x1 *= screen_w
                x2 *= screen_w
            if 0 <= y1 <= 1 and 0 <= y2 <= 1:
                y1 *= screen_h
                y2 *= screen_h
            return int((x1+x2)/2), int((y1+y2)/2)
    except:
        return None
    return None

def find_element_bbox(ui_elements: List[Dict[str, Any]], target_text: str) -> Optional[Any]:
    if not ui_elements or not target_text:
        return None
    target_lower = target_text.lower()
    candidates = []
    for el in ui_elements:
        text = (el.get("text") or "").strip()
        if not text:
            continue
        if target_lower in text.lower() or get_close_matches(target_lower, [text.lower()], n=1, cutoff=0.6):
            candidates.append(el)
    if not candidates:
        return None
    return candidates[0].get("bbox")

# ---------------- Action functions ---------------- #

def open_application(name: str) -> bool:
    paths = {
        "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                   "chrome.exe"],
        "notepad": ["notepad.exe"],
        "explorer": ["explorer.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"]
    }
    for exe in paths.get(name.lower(), [name]):
        try:
            if os.path.isfile(exe) or exe.endswith(".exe"):
                subprocess.Popen([exe])
            else:
                os.startfile(exe)
            time.sleep(1)
            return True
        except:
            continue
    pyautogui.hotkey("win")
    time.sleep(0.5)
    pyautogui.write(name)
    pyautogui.press("enter")
    time.sleep(1)
    return True

def open_folder(name: str) -> bool:
    folders = {
        "desktop": os.path.expanduser("~/Desktop"),
        "documents": os.path.expanduser("~/Documents"),
        "downloads": os.path.expanduser("~/Downloads")
    }
    path = folders.get(name.lower(), name)
    if os.path.exists(path):
        os.startfile(path)
        return True
    return False

def execute_action(action_data: Dict[str, Any], ui_elements: List[Dict[str, Any]] = None) -> bool:
    action = action_data.get("action")
    target = action_data.get("target", "")
    text = action_data.get("text", "")
    keys = action_data.get("keys", "")

    if action == "click":
        if not target or not ui_elements:
            return False
        bbox = find_element_bbox(ui_elements, target)
        if not bbox:
            return False
        center = _center_of_bbox(bbox)
        if not center:
            return False
        time.sleep(0.5)
        pyautogui.click(center[0], center[1])
        return True

    if action == "type":
        if target.lower() in ["address bar", "url bar"]:
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)
        pyautogui.write(text, interval=0.05)
        return True

    if action == "scroll":
        direction = -300 if target.lower() == "down" else 300
        pyautogui.scroll(direction)
        return True

    if action == "open":
        return open_application(target)

    if action == "navigate":
        if open_folder(target):
            return True

        url = target
        if not url.startswith("http"):
            url = "https://" + target

        webbrowser.open(url)

        # Ensure Enter pressed after typing URL
        time.sleep(0.5)
        pyautogui.press("enter")

        # Wait for page load
        time.sleep(5)  # adjust depending on internet speed

        # Activate browser window
        if gw:
            windows = gw.getWindowsWithTitle(target.split("//")[-1].split(".")[0].capitalize())
            if windows:
                win = windows[0]
                win.restore()
                win.activate()
                time.sleep(1)

        return True

    if action == "hotkey" and keys:
        key_list = [k.strip() for k in keys.replace("+", " ").split()]
        pyautogui.hotkey(*key_list)
        return True

    if action == "wait":
        time.sleep(2)
        return True

    return False
