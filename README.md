# multi-agent-codegen

A multi-agent code generation system built with LangGraph that automatically plans, architects, and generates production-quality web projects from a single text prompt.

## How It Works

The system uses 3 specialized AI agents that run in sequence:

```
User Prompt → Planner → Architect → Coder → Generated Project
```

- **Planner** (Llama 3.1 8B via Groq) — converts the user prompt into a structured project plan with features, tech stack, and file list
- **Architect** (Llama 3.3 70B via Groq) — breaks the plan into ordered implementation tasks, one per file
- **Coder** (Gemini 2.5 Flash via Google AI) — implements each file using a ReAct agent with file system tools, with cross-file context to ensure consistency

## Tech Stack

- Python 3.12
- LangGraph
- LangChain
- ChatGroq (Llama models)
- ChatGoogleGenerativeAI (Gemini)
- Pydantic

## Project Structure

```
multi-agent-codegen/
├── agents/
│   ├── graph.py        # Main LangGraph pipeline and agent logic
│   ├── prompts.py      # Prompt functions for all 3 agents
│   ├── states.py       # Pydantic state models
│   └── tools.py        # File system and shell tools for the coder agent
├── generated_project/  # Output directory for generated files
├── .env                # API keys (not committed)
└── pyproject.toml
```

## Setup

1. Clone the repo

```bash
git clone https://github.com/yourusername/multi-agent-codegen.git
cd multi-agent-codegen
```

2. Install dependencies

```bash
uv sync
```

3. Create a `.env` file with your API keys

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_ai_studio_api_key
```

4. Create the output directory

```bash
mkdir generated_project
```

5. Run the agent

```bash
uv run agents/graph.py
```

## Usage

Edit the `user_prompt` at the bottom of `agents/graph.py`:

```python
result = agent.invoke(
    {
        "user_prompt": """
Build a modern responsive weather dashboard using html css and javascript.

Requirements:
- use OpenWeatherMap API
- search weather by city name
- display temperature humidity wind speed and weather condition
- modern glassmorphism UI
- responsive layout

Use only vanilla html css and javascript.
Keep the project to a maximum of 3 files.
"""
    },
    {"recursion_limit": 25},
)
```

Then run:

```bash
uv run agents/graph.py
```

Generated files will appear in `generated_project/`.

## Tools Available to the Coder Agent

| Tool                    | Description                                  |
| ----------------------- | -------------------------------------------- |
| `write_file`            | Creates a new file with content              |
| `edit_file`             | Surgically replaces text in an existing file |
| `read_file`             | Reads a file for inspection                  |
| `list_file`             | Lists all files in the project directory     |
| `get_current_directory` | Returns the project root path                |
| `run_cmd`               | Executes a shell command                     |

## Features

- Automatic retry on rate limits with delay parsing from API response
- Cross-file context injection so JS selectors always match HTML ids
- DOM consistency validation before each file is finalized
- JS syntax validation using `node --check` after each step
- Safe path enforcement to prevent writes outside `generated_project/`

## API Keys

- **Groq** — free at [console.groq.com](https://console.groq.com)
- **Google AI Studio** — free at [aistudio.google.com](https://aistudio.google.com)

## Notes

- Gemini 2.5 Flash free tier allows 20 requests/day. For longer projects use `gemini-2.0-flash` which allows 1500 requests/day.
- Generated project files are not committed to the repo. Add `generated_project/*` to `.gitignore`.
- Always create the `generated_project/` directory before running.

## Example Output

Given a prompt to build a weather dashboard, the system generates:

```
generated_project/
├── index.html    # Semantic HTML with glassmorphism UI
├── styles.css    # Responsive CSS with dark gradient background
└── script.js     # Vanilla JS with OpenWeatherMap API integration
```
