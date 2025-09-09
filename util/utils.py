import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
import easyocr
import cv2
import numpy as np
from PIL import Image
import base64
import time
import subprocess
import pyautogui
from pywinauto.application import Application
from pywinauto.findwindows import find_window
from pywinauto.controls.win32_controls import ButtonWrapper, EditWrapper
import psutil
import threading
from typing import Dict, List, Optional, Tuple, Any

def get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence"):
    """Get Florence model and processor, handling custom configuration."""
    try:
        # For Florence models, we need to handle the custom configuration
        if "florence" in model_name.lower():
            # Load model directly without AutoTokenizer
            model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path, 
                trust_remote_code=True, 
                torch_dtype=torch.float32
            )
            model.eval()
            
            # Fix missing attributes for compatibility
            if not hasattr(model, '_supports_sdpa'):
                model._supports_sdpa = False
            if not hasattr(model, 'supports_sdpa'):
                model.supports_sdpa = False
            
            # Create a simple tokenizer wrapper or use a compatible one
            # For now, we'll return the model without tokenizer
            return {"model": model, "tokenizer": None}
        else:
            # Standard approach for other models
            tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(model_name_or_path, trust_remote_code=True, torch_dtype=torch.float32)
            model.eval()
            return {"tokenizer": tokenizer, "model": model}
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
        # Return None to indicate failure
        return None

def check_ocr_box(image_input, display_img=False, output_bb_format='xyxy', goal_filtering=None, easyocr_args=None, use_paddleocr=True):
    """Basic OCR text extraction with bounding boxes."""
    try:
        # Convert PIL image to OpenCV format
        if isinstance(image_input, Image.Image):
            image_cv = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        else:
            image_cv = image_input
        
        # Use EasyOCR for text detection
        reader = easyocr.Reader(['en'])
        results = reader.readtext(image_cv)
        
        # Extract text and bounding boxes
        text_list = []
        bbox_list = []
        
        for (bbox, text, confidence) in results:
            if confidence > 0.5 and text.strip():
                text_list.append(text.strip())
                
                # Convert bbox format
                if output_bb_format == 'xyxy':
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    bbox_xyxy = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    bbox_list.append(bbox_xyxy)
                else:
                    bbox_list.append(bbox)
        
        return (text_list, bbox_list), False  # Return tuple and is_goal_filtered flag
        
    except Exception as e:
        print(f"⚠️ OCR error: {e}")
        return ([], []), False

def check_ocr_box(element):
    bbox = element.get("bbox", [])
    return len(bbox) == 4 and all(isinstance(x, (int, float)) for x in bbox)

def get_yolo_model(model_path=None):
    """Get YOLO model for icon detection."""
    try:
        # Try to import YOLO dependencies
        from ultralytics import YOLO
        if model_path and os.path.exists(model_path):
            return YOLO(model_path)
        else:
            # Return a dummy model or raise error
            raise FileNotFoundError(f"YOLO model not found at {model_path}")
    except ImportError:
        raise NotImplementedError("YOLO model support not implemented. Install ultralytics: pip install ultralytics")
    except Exception as e:
        raise NotImplementedError(f"YOLO model support not available: {e}")

def get_som_labeled_img(image_input, yolo_model, BOX_TRESHOLD=0.05, output_coord_in_ratio=True, ocr_bbox=None, draw_bbox_config=None, caption_model_processor=None, ocr_text=None, iou_threshold=0.1, imgsz=640):
    """Basic SOM labeling implementation using YOLO and OCR results."""
    try:
        # Convert PIL image to OpenCV format
        if isinstance(image_input, Image.Image):
            image_cv = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        else:
            image_cv = image_input
        
        # Get YOLO predictions
        results = yolo_model(image_cv, conf=BOX_TRESHOLD, iou=iou_threshold, imgsz=imgsz)
        
        # Extract detected objects
        parsed_content_list = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Create element
                    element = {
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "confidence": float(confidence),
                        "class_id": class_id,
                        "type": "icon",
                        "text": f"Object {class_id}"
                    }
                    
                    # Add OCR text if available
                    if ocr_text and len(ocr_text) > 0:
                        # Find closest OCR text to this box
                        box_center = [(x1 + x2) / 2, (y1 + y2) / 2]
                        closest_text = ""
                        min_distance = float('inf')
                        
                        for i, bbox in enumerate(ocr_bbox):
                            if i < len(ocr_text):
                                ocr_center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
                                distance = ((box_center[0] - ocr_center[0]) ** 2 + (box_center[1] - ocr_center[1]) ** 2) ** 0.5
                                if distance < min_distance:
                                    min_distance = distance
                                    closest_text = ocr_text[i]
                        
                        if closest_text:
                            element["text"] = closest_text
                    
                    parsed_content_list.append(element)
        
        # Create a simple labeled image (just return the original for now)
        _, buffer = cv2.imencode('.jpg', image_cv)
        labeled_img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Return results
        return labeled_img_base64, [], parsed_content_list
        
    except Exception as e:
        print(f"⚠️ SOM labeling error: {e}")
        # Return empty results
        return "", [], []

class AutomationManager:
    """Comprehensive automation manager for handling various applications and interactions."""
    
    def __init__(self):
        self.active_apps = {}
        self.browser_driver = None
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.5  # Small delay between actions
        
    def open_application(self, app_name: str, app_path: str = None, wait_time: int = 3) -> bool:
        """Open an application by name or path."""
        try:
            if app_path and os.path.exists(app_path):
                # Use specific path
                app = Application().start(app_path)
            else:
                # Try common applications
                common_apps = {
                    'notepad': 'notepad.exe',
                    'calculator': 'calc.exe',
                    'paint': 'mspaint.exe',
                    'wordpad': 'wordpad.exe',
                    'explorer': 'explorer.exe',
                    'chrome': 'chrome.exe',
                    'firefox': 'firefox.exe',
                    'edge': 'msedge.exe'
                }
                
                if app_name.lower() in common_apps:
                    app = Application().start(common_apps[app_name.lower()])
                else:
                    # Try to start by name
                    app = Application().start(app_name)
            
            time.sleep(wait_time)
            self.active_apps[app_name] = app
            return True
            
        except Exception as e:
            print(f"❌ Failed to open {app_name}: {e}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """Close an application."""
        try:
            if app_name in self.active_apps:
                self.active_apps[app_name].kill()
                del self.active_apps[app_name]
                return True
            else:
                # Try to find and kill by process name
                for proc in psutil.process_iter(['pid', 'name']):
                    if app_name.lower() in proc.info['name'].lower():
                        proc.kill()
                        return True
                return False
        except Exception as e:
            print(f"❌ Failed to close {app_name}: {e}")
            return False
    
    def click_element(self, x: int, y: int, button: str = 'left', clicks: int = 1) -> bool:
        """Click at specific coordinates."""
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
            return True
        except Exception as e:
            print(f"❌ Failed to click at ({x}, {y}): {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.1) -> bool:
        """Type text with optional interval between characters."""
        try:
            pyautogui.write(text, interval=interval)
            return True
        except Exception as e:
            print(f"❌ Failed to type text: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a specific key."""
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            print(f"❌ Failed to press key {key}: {e}")
            return False
    
    def hotkey(self, *keys) -> bool:
        """Press a combination of keys."""
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            print(f"❌ Failed to press hotkey {keys}: {e}")
            return False
    
    def find_and_click_text(self, text: str, confidence: float = 0.8) -> bool:
        """Find text on screen and click it using OCR."""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Use OCR to find text
            reader = easyocr.Reader(['en'])
            results = reader.readtext(screenshot_cv)
            
            for (bbox, detected_text, conf) in results:
                if text.lower() in detected_text.lower() and conf >= confidence:
                    # Calculate center of bounding box
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    center_x = int(sum(x_coords) / len(x_coords))
                    center_y = int(sum(y_coords) / len(y_coords))
                    
                    # Click on the text
                    pyautogui.click(center_x, center_y)
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to find and click text '{text}': {e}")
            return False
    
    def wait_for_element(self, timeout: int = 10, condition_func=None) -> bool:
        """Wait for an element to appear on screen."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func and condition_func():
                return True
            time.sleep(0.5)
        return False
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get current screen information."""
        try:
            screen_width, screen_height = pyautogui.size()
            mouse_x, mouse_y = pyautogui.position()
            
            return {
                'screen_width': screen_width,
                'screen_height': screen_height,
                'mouse_x': mouse_x,
                'mouse_y': mouse_y
            }
        except Exception as e:
            print(f"❌ Failed to get screen info: {e}")
            return {}
    
    def take_screenshot(self, region: Tuple[int, int, int, int] = None) -> Optional[str]:
        """Take a screenshot and return as base64 string."""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to base64
            import io
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None
    
    def scroll(self, x: int, y: int, clicks: int = 3) -> bool:
        """Scroll at specific coordinates."""
        try:
            pyautogui.scroll(clicks, x=x, y=y)
            return True
        except Exception as e:
            print(f"❌ Failed to scroll at ({x}, {y}): {e}")
            return False
    
    def drag_and_drop(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> bool:
        """Drag and drop from one position to another."""
        try:
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button='left')
            return True
        except Exception as e:
            print(f"❌ Failed to drag and drop: {e}")
            return False

# Browser Automation Functions
def setup_browser_automation(browser_type: str = 'chrome') -> Optional[Any]:
    """Setup browser automation with Selenium."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        if browser_type.lower() == 'chrome':
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # options.add_argument('--headless')  # Uncomment for headless mode
            
            driver = webdriver.Chrome(options=options)
            return driver
        else:
            print(f"❌ Browser type {browser_type} not supported")
            return None
            
    except ImportError:
        print("❌ Selenium not installed. Install with: pip install selenium")
        return None
    except Exception as e:
        print(f"❌ Failed to setup browser automation: {e}")
        return None

def browser_automation_actions(driver, action: str, **kwargs) -> bool:
    """Perform browser automation actions."""
    try:
        if action == 'navigate':
            driver.get(kwargs.get('url', ''))
        elif action == 'click_element':
            from selenium.webdriver.common.by import By
            element = driver.find_element(By.CSS_SELECTOR, kwargs.get('selector', ''))
            element.click()
        elif action == 'type_text':
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            element = driver.find_element(By.CSS_SELECTOR, kwargs.get('selector', ''))
            element.clear()
            element.send_keys(kwargs.get('text', ''))
        elif action == 'submit_form':
            from selenium.webdriver.common.keys import Keys
            element = driver.find_element(By.CSS_SELECTOR, kwargs.get('selector', ''))
            element.send_keys(Keys.RETURN)
        else:
            print(f"❌ Unknown browser action: {action}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Browser automation failed: {e}")
        return False

# Application-specific automation functions
def automate_notepad(text: str = "Hello from automation!") -> bool:
    """Automate Notepad operations."""
    try:
        automation = AutomationManager()
        
        # Open Notepad
        if not automation.open_application('notepad'):
            return False
        
        time.sleep(2)
        
        # Type text
        automation.type_text(text)
        
        # Save file (Ctrl+S)
        automation.hotkey('ctrl', 's')
        time.sleep(1)
        
        # Press Enter to confirm save
        automation.press_key('enter')
        
        return True
        
    except Exception as e:
        print(f"❌ Notepad automation failed: {e}")
        return False

def automate_calculator(operation: str = "2+2=") -> bool:
    """Automate Calculator operations."""
    try:
        automation = AutomationManager()
        
        # Open Calculator
        if not automation.open_application('calculator'):
            return False
        
        time.sleep(2)
        
        # Type the operation
        automation.type_text(operation)
        
        return True
        
    except Exception as e:
        print(f"❌ Calculator automation failed: {e}")
        return False

def automate_browser_search(search_term: str = "Python automation") -> bool:
    """Automate browser search."""
    try:
        driver = setup_browser_automation()
        if not driver:
            return False
        
        # Navigate to Google
        browser_automation_actions(driver, 'navigate', url='https://www.google.com')
        time.sleep(2)
        
        # Type search term
        browser_automation_actions(driver, 'type_text', 
                                 selector='input[name="q"]', 
                                 text=search_term)
        
        # Submit search
        browser_automation_actions(driver, 'submit_form', 
                                 selector='input[name="q"]')
        
        time.sleep(3)
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Browser automation failed: {e}")
        return False

# Utility functions for automation
def list_running_applications() -> List[str]:
    """List currently running applications."""
    try:
        running_apps = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                running_apps.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return list(set(running_apps))
    except Exception as e:
        print(f"❌ Failed to list applications: {e}")
        return []

def get_window_info(window_title: str = None) -> Dict[str, Any]:
    """Get information about a specific window."""
    try:
        if window_title:
            window = find_window(title=window_title)
            return {
                'title': window.window_text(),
                'rect': window.rectangle(),
                'visible': window.is_visible(),
                'enabled': window.is_enabled()
            }
        else:
            # Return info about all visible windows
            windows = []
            for window in find_window():
                try:
                    windows.append({
                        'title': window.window_text(),
                        'rect': window.rectangle(),
                        'visible': window.is_visible(),
                        'enabled': window.is_enabled()
                    })
                except:
                    pass
            return {'windows': windows}
    except Exception as e:
        print(f"❌ Failed to get window info: {e}")
        return {}
