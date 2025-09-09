import requests
import base64
import logging
import pyautogui
from config import (
    OMNISERVER_BASE_URL,
    OMNISERVER_PARSE_PATH,
    SOM_CONFIDENCE_THRESHOLD,
    SOM_IOU_THRESHOLD,
    SOM_MAX_DETECTIONS,
    ENABLE_CAPTION_MODEL,
    CAPTION_BOX_EXPAND_PX,
    OCR_MIN_TEXT_SIZE,
)
import time

logger = logging.getLogger(__name__)
OMNISERVER_URL = f"{OMNISERVER_BASE_URL}{OMNISERVER_PARSE_PATH}"

def capture_screen(output_path: str):
    screenshot = pyautogui.screenshot()
    screenshot.save(output_path)
    logger.info(f"Screenshot saved: {output_path}")
    return output_path

def get_ui_elements(screenshot_path: str):
    try:
        with open(screenshot_path, "rb") as f:
            img_bytes = f.read()
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        data = {
            "base64_image": base64_image,
            "use_caption_model": ENABLE_CAPTION_MODEL,
            "som_conf_thres": SOM_CONFIDENCE_THRESHOLD,
            "som_iou_thres": SOM_IOU_THRESHOLD,
            "som_max_det": SOM_MAX_DETECTIONS,
            "caption_expand_px": CAPTION_BOX_EXPAND_PX,
            "ocr_min_text_size": OCR_MIN_TEXT_SIZE,
        }
        resp = requests.post(OMNISERVER_URL, json=data, timeout=45)
        if resp.status_code != 200:
            logger.error(f"OmniServer error {resp.status_code}: {resp.text}")
            return []
        payload = resp.json()
        elements = payload.get("parsed_content_list", [])
        logger.info(f"OmniServer extracted {len(elements)} elements")
        normalized = []
        for el in elements:
            text = el.get("text") or el.get("caption") or el.get("content") or ""
            bbox = el.get("bbox")
            if bbox and len(bbox) == 4:
                normalized.append({
                    "text": text.strip(),
                    "bbox": bbox,
                    "type": el.get("type"),
                    "interactivity": el.get("interactivity", False)
                })
        return normalized
    except Exception as e:
        logger.error(f"Failed to contact OmniServer: {e}")
        return []
