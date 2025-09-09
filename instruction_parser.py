import json
import requests
import re
import logging
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You turn natural language into deterministic UI automation steps.
Return ONLY a JSON array of step objects. Each object can have keys:
- action: one of [click, type, scroll, open, navigate, hotkey, wait, press]
- target: optional text describing UI element (e.g., "address bar", "search", "youtube")
- text: optional text to type
- keys: for hotkey (e.g., "ctrl+l")

Rules:
- Split compound instructions into multiple ordered steps.
- Prefer explicit steps for common flows. Examples:
  "open chrome type youtube then search despacito" =>
  [
    {"action":"open","target":"chrome"},
    {"action":"hotkey","keys":"ctrl+l"},
    {"action":"type","text":"youtube.com"},
    {"action":"press","target":"enter"},
    {"action":"click","target":"search"},
    {"action":"type","text":"despacito"},
    {"action":"press","target":"enter"}
  ]
- Return ONLY JSON, no explanations.
"""

def parse_instruction_with_llm(instruction):
    """Parse user instruction using Groq LLM API."""
    user_message = f"Parse this instruction: '{instruction}'"

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        resp = requests.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=data, timeout=15)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json_from_response(content)
            if parsed:
                return parsed
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")

    return parse_instruction_fallback(instruction)

def extract_json_from_response(content):
    try:
        result = json.loads(content)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError:
        matches = re.findall(r'\{[^{}]*"action"[^{}]*\}', content)
        results = []
        for m in matches:
            try:
                results.append(json.loads(m))
            except:
                continue
        return results if results else None

def _normalize_site(text: str) -> str:
    t = text.strip()
    if t and "." not in t and " " not in t:
        return t + ".com"
    return t

def parse_instruction_fallback(instruction):
    """Rule-based parser for common compound commands."""
    raw = instruction
    instruction_lower = instruction.lower()
    steps = []

    # YouTube special flow
    if "youtube" in instruction_lower:
        steps.append({"action": "navigate", "target": "youtube.com"})
        steps.append({"action": "wait"})  # wait for page load
        # focus search bar
        steps.append({"action": "click", "target": "search"})
        # type search query if exists
        if "search for" in instruction_lower:
            query = instruction_lower.split("search for",1)[1].split("and play")[0].strip().strip('"')
            if query:
                steps.append({"action": "type", "text": query})
                steps.append({"action": "press", "target": "enter"})
        return steps

    # Desktop folder creation flow
    if "create folder" in instruction_lower:
        steps.append({"action": "navigate", "target": "desktop"})
        steps.append({"action": "hotkey", "keys": "ctrl+shift+n"})
        if "name it" in instruction_lower:
            folder_name = instruction_lower.split("name it",1)[1].strip()
            steps.append({"action": "type", "text": folder_name})
            steps.append({"action": "press", "target": "enter"})
        return steps

    # Generic fallbacks
    if instruction_lower.startswith("open"):
        target = raw[5:].strip()
        steps.append({"action": "open", "target": target})
        return steps
    if instruction_lower.startswith("click"):
        steps.append({"action": "click", "target": raw[6:].strip()})
        return steps
    if instruction_lower.startswith("type"):
        steps.append({"action": "type", "text": raw[5:].strip()})
        return steps
    if instruction_lower.startswith("press"):
        steps.append({"action": "press", "target": raw[6:].strip()})
        return steps

    steps.append({"action": "unknown", "target": raw})
    return steps

def parse_instruction(instruction):
    """Main parsing function."""
    return parse_instruction_with_llm(instruction)
