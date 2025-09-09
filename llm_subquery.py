# llm_subquery_agent.py

import time
import os
from instruction_parser import parse_instruction_with_llm
from action_executor import execute_action
from screen_parser import capture_screen, get_ui_elements

def execute_subquery(subquery: str, screenshot_dir: str, idx: int):
    """
    Executes a single subquery using OmniParser + LLM guidance.
    """
    while True:
        # 1️⃣ Capture fresh screenshot for current UI state
        screenshot_path = capture_screen(os.path.join(screenshot_dir, f"step_{idx}.png"))
        ui_elements = get_ui_elements(screenshot_path)

        # 2️⃣ Ask LLM for next actions in this subquery
        actions = parse_instruction_with_llm(subquery)
        if not actions:
            print(f"No actions returned for subquery: {subquery}")
            break

        # 3️⃣ Execute each action
        subquery_complete = True
        for action in actions:
            success = execute_action(action, ui_elements)
            if not success:
                print(f"Action failed: {action}, retrying subquery...")
                subquery_complete = False
                time.sleep(0.5)
                break  # retry subquery

        # 4️⃣ Exit loop if subquery completed successfully
        if subquery_complete:
            break


def execute_instruction(instruction: str, screenshot_dir: str = "screenshots"):
    """
    High-level function to execute a full instruction.
    Splits into subqueries using LLM, then executes each sequentially.
    """
    # Ensure screenshot directory exists
    os.makedirs(screenshot_dir, exist_ok=True)

    # 1️⃣ Use LLM to split instruction into subqueries
    subqueries = parse_instruction_with_llm(instruction)

    if not subqueries:
        print("Failed to parse instruction into subqueries.")
        return

    # If LLM returns flat actions, wrap them as a single subquery
    if isinstance(subqueries, list) and all(isinstance(x, dict) for x in subqueries):
        subqueries = [instruction]

    # 2️⃣ Execute each subquery sequentially
    for idx, subquery in enumerate(subqueries, start=1):
        print(f"Executing subquery {idx}/{len(subqueries)}: {subquery}")
        execute_subquery(subquery, screenshot_dir, idx)

    print("✅ Instruction completed successfully.")
