# AutoUI-GPT

**AutoUI-GPT** is an AI-powered desktop automation agent that turns natural language instructions into actionable UI tasks. It allows you to control applications, navigate folders, type, click, scroll, and execute system commands automatically on Windows, leveraging the power of LLMs (Groq API or other supported models) combined with OmniParser for UI element detection.

---

## Features

- Execute multi-step instructions like:  
  `"Go to Desktop, open Notepad, type 'Hello World'"`.
- Supports common actions:
  - `click`, `type`, `scroll`, `open`, `navigate`, `hotkey`, `press`, `wait`.
- Recognizes OS folders (Desktop, Downloads, Documents) and websites.
- Uses **OmniParser** to detect UI elements from screenshots.
- LLM-powered reasoning to split compound instructions into ordered steps.
- Rule-based fallback for offline or failed LLM parsing.
- Logs all actions and saves screenshots of executed steps.

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Gaikarak/AutoUI-GPT.git
cd AutoUI-GPT/ui-agent
Create a Python virtual environment and install dependencies:

python -m venv omni_env
.\omni_env\Scripts\activate
pip install -r requirements.txt


Ensure OmniParser server is running:

cd ../omniparserserver
python omniparserserver.py


Configure config.py with your Groq API key and desired model:

GROQ_API_KEY = "your_api_key_here"
GROQ_MODEL = "llama3-8b-8192"
OMNISERVER_BASE_URL = "http://localhost:8000"

Usage
python main_agent.py


Type instructions in natural language. Example:

Go to Desktop, open Notepad, type 'Hello World'

Open Chrome, type YouTube.com, search 'Lo-fi music'

Screenshots and logs are saved in the screenshots/ directory.

Dependencies

Python 3.11+

pyautogui

requests

Pillow (PIL)

OmniParser server

Groq API account (for LLM parsing)

Contributing

Contributions and improvements are welcome! Please fork the repo and submit a pull request.

License

MIT License

AutoUI-GPT bridges the gap between human instructions and desktop automation, making repetitive tasks smarter and faster.


This `README.md` is **GitHub-ready**, concise, and highlights all key points about the project.  

If you want, I can also **add a “Project Structure” section** to show all files and their roles for better clarity. This helps anyone who clones your repo understand the workflow immediately.  

Do you want me to add that?

You said:
give in 1 file format detailed and in contribute can add increasing the accuracy for the llm and also making the whole desktop automated
ChatGPT said:

Here’s an updated single-file README.md for your AutoUI-GPT repository with detailed info, including an enhanced Contributing section reflecting LLM improvements and full desktop automation:

# AutoUI-GPT

**AutoUI-GPT** is an AI-powered desktop automation agent that converts natural language instructions into actionable UI tasks. It allows you to control applications, navigate folders, type, click, scroll, and execute system commands automatically on Windows, leveraging LLMs (Groq API or other supported models) combined with OmniParser for UI element detection.

---

## Features

- Execute multi-step instructions such as:  
  `"Go to Desktop, open Notepad, type 'Hello World'"`.
- Supports core actions:
  - `click`, `type`, `scroll`, `open`, `navigate`, `hotkey`, `press`, `wait`.
- Recognizes Windows folders (Desktop, Downloads, Documents) and websites.
- Uses **OmniParser** to detect UI elements from screenshots.
- LLM-powered reasoning splits compound instructions into ordered steps.
- Rule-based fallback for offline or failed LLM parsing.
- Logs all actions and saves screenshots of executed steps for review.

---

## Project Structure



ui-agent/
├─ main_agent.py # Entry point, handles instructions and execution loop
├─ instruction_parser.py # Converts natural language to UI actions using LLM
├─ action_executor.py # Executes parsed actions on the desktop
├─ screen_parser.py # Captures screen and detects UI elements via OmniServer
├─ config.py # Configuration: API keys, OmniServer URL, thresholds
├─ requirements.txt # Python dependencies
├─ agent.log # Log file of executed instructions
├─ screenshots/ # Saves screenshots of UI steps


---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Gaikarak/AutoUI-GPT.git
cd AutoUI-GPT/ui-agent


Create a Python virtual environment and install dependencies:

python -m venv omni_env
.\omni_env\Scripts\activate
pip install -r requirements.txt


Ensure OmniParser server is running:

cd ../omniparserserver
python omniparserserver.py


Configure config.py with your Groq API key and desired model:

GROQ_API_KEY = "your_api_key_here"
GROQ_MODEL = "llama3-8b-8192"
OMNISERVER_BASE_URL = "http://localhost:8000"

Usage

Run the agent:

python main_agent.py


Type instructions in natural language. Example instructions:

Go to Desktop, open Notepad, type 'Hello World'

Open Chrome, type YouTube.com, search 'Lo-fi music'

Screenshots and logs are saved in the screenshots/ directory.

Contributing

We welcome contributions to AutoUI-GPT! Some areas you can help improve:

Increase LLM parsing accuracy for complex multi-step instructions.

Add support for full desktop automation, including more apps and advanced workflows.

Improve UI element detection and handling for dynamic applications.

Optimize performance and reduce execution latency.

Please fork the repository and submit a pull request with your changes.

Dependencies

Python 3.11+

pyautogui

requests

Pillow (PIL)

OmniParser server

Groq API account (for LLM parsing)
