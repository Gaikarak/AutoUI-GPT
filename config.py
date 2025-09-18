# config.py - Configuration for Computer Use Agent
import os
# Groq API Configuration
GROQ_API_KEY = ""
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = ""

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# OmniServer Configuration
OMNISERVER_BASE_URL = "http://localhost:8000"
OMNISERVER_PARSE_PATH = "/parse"
SOM_CONFIDENCE_THRESHOLD = 0.3
SOM_IOU_THRESHOLD = 0.5
SOM_MAX_DETECTIONS = 100
ENABLE_CAPTION_MODEL = True
CAPTION_BOX_EXPAND_PX = 5
OCR_MIN_TEXT_SIZE = 10

