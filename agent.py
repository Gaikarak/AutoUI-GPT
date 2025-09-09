# main_agent.py

import logging
import time
import os
from instruction_parser import parse_instruction_with_llm
from action_executor import execute_action
from screen_parser import get_ui_elements, capture_screen
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ---------------- Logging ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join(os.getcwd(), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ---------------- Main Loop ---------------- #
def main():
    print("🖥️  Computer Use Agent")
    print(f" Screenshots will be saved in: {SCREENSHOT_DIR}\n")
    logger.info("Agent started")

    while True:
        try:
            instruction = input("Instruction ('exit' to quit): ").strip()
            if instruction.lower() == "exit":
                print("Exiting agent.")
                logger.info("Agent stopped by user")
                break
            if not instruction:
                continue

            logger.info(f"User Instruction: {instruction}")
            actions = parse_instruction_with_llm(instruction)
            if not actions:
                print("Failed to parse instruction")
                continue

            for idx, action in enumerate(actions, start=1):
                action_type = action.get("action", "")
                target = action.get("target", "")
                print(f"Step {idx}/{len(actions)}: {action_type} on '{target}'")

                ui_elements = []

                # Add delay and capture screenshot for open/navigate/click
                if action_type in ["click", "open", "navigate"]:
                    time.sleep(3)  # allow UI to update / page load
                    screenshot_path = os.path.join(
                        SCREENSHOT_DIR, f"step_{idx}_{action_type}_{target.replace(' ', '_')}.png"
                    )
                    capture_screen(screenshot_path)
                    ui_elements = get_ui_elements(screenshot_path)

                # Execute the action
                success = execute_action(action, ui_elements)

                if success:
                    print(f" {action_type} ✅")
                    if action_type in ["open", "navigate"]:
                        time.sleep(1)  # additional wait for UI to settle
                else:
                    print(f" {action_type} ❌")
                    break

            print("=" * 60)

        except KeyboardInterrupt:
            print("\nExiting agent.")
            logger.info("Agent stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
