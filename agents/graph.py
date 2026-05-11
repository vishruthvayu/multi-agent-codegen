from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts import *
from states import *
from tools import *

from langgraph.constants import END
from langgraph.graph import StateGraph
from langchain.agents import create_agent

from langchain_core.globals import set_verbose, set_debug

import re
import time

load_dotenv()

set_debug(False)
set_verbose(False)

# =========================
# MODELS
# =========================

planner_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
)

architect_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
)

coder_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_output_tokens=1500,
    thinking_budget=0,
)

# =========================
# TOOLS
# =========================

coder_tools = [
    read_file,
    write_file,
    edit_file,
    list_file,
    get_current_directory,
    run_cmd,
]

# =========================
# AGENT
# =========================

react_agent = create_agent(
    model=coder_llm,
    tools=coder_tools,
)

# =========================
# RETRY WRAPPER
# =========================

def safe_agent_invoke(agent, payload, retries=3):
    for i in range(retries):
        try:
            return agent.invoke(
                payload,
                config={"recursion_limit": 15}
            )

        except Exception as e:
            error_text = str(e)

            if "RESOURCE_EXHAUSTED" in error_text:
                wait = 60
                match = re.search(r'"retryDelay":\s*"(\d+)s"', error_text)
                if match:
                    wait = int(match.group(1)) + 5

                print(f"\n[Rate limited] Waiting {wait}s before retry {i+1}/{retries}...")
                time.sleep(wait)
                continue

            wait = min(2 ** i, 10)
            print(f"\n[Retry {i+1}/{retries}] Waiting {wait}s...")
            print(error_text[:300])
            time.sleep(wait)

    raise Exception("Max retries exceeded")

# =========================
# PLANNER
# =========================

def planner_agent(state: dict) -> dict:
    user_prompt = state.get("user_prompt")

    resp = planner_llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )

    if resp is None:
        raise ValueError("planner response is None")

    return {"plan": resp}

# =========================
# ARCHITECT
# =========================

def architect_agent(state: dict) -> dict:
    plan: Plan = state.get("plan")

    resp = architect_llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan)
    )

    if resp is None:
        raise ValueError("architect response is None")

    resp.plan = plan

    return {"task_plan": resp}

# =========================
# CODER
# =========================

def coder_agent(state: dict) -> dict:

    coder_state: CoderState = state.get("coder_state")

    if coder_state is None:
        coder_state = CoderState(
            task_plan=state["task_plan"],
            current_step_idx=0,
        )

    steps = coder_state.task_plan.implementation_steps

    if coder_state.current_step_idx >= len(steps):
        return {
            "coder_state": coder_state,
            "status": "DONE",
        }

    current_task = steps[coder_state.current_step_idx]

    print("\n==============================")
    print(f"STEP: {coder_state.current_step_idx + 1}/{len(steps)}")
    print(f"FILE: {current_task.filepath}")
    print("==============================\n")

    system_prompt = coder_prompt()

    project_files = "\n".join([step.filepath for step in steps])

    # collect already written files for cross-file context
    written_files = []
    for step in steps[:coder_state.current_step_idx]:
        content = read_file.invoke(step.filepath)
        if content:
            written_files.append(f"=== {step.filepath} ===\n{content[:1000]}")

    existing_context = "\n\n".join(written_files) if written_files else "None yet."

    user_prompt = f"""
PROJECT FILES:
{project_files}

ALREADY WRITTEN FILES (read carefully before writing anything):
{existing_context}

CURRENT TASK:
{current_task.task_description}

TARGET FILE:
{current_task.filepath}

INSTRUCTIONS:
- Read ALREADY WRITTEN FILES above carefully before writing
- Every getElementById in JS MUST exist as an id in HTML
- Every querySelector in JS MUST exist as a class or id in HTML
- If writing JS, cross-check every DOM selector against the HTML
- If writing HTML, include ALL ids and classes that JS will need
- Use edit_file for modifications to existing files
- Use write_file for new files
- Build production-quality code
- Ensure generated code is runnable
- Ensure HTML/CSS/JS selectors are consistent across all files
- Ensure API calls are valid
"""

    time.sleep(1)

    safe_agent_invoke(
        react_agent,
        {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        },
    )

    # =========================
    # VALIDATION
    # =========================

    validation = run_cmd.invoke("find . -name '*.js' -exec node --check {} +")

    print("\n==============================")
    print("VALIDATION")
    print(validation)
    print("==============================\n")

    coder_state.current_step_idx += 1

    return {"coder_state": coder_state}

# =========================
# GRAPH
# =========================

graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")

graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {
        "END": END,
        "coder": "coder",
    },
)

graph.set_entry_point("planner")

agent = graph.compile()

# =========================
# MAIN
# =========================

if __name__ == "__main__":

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
- animated weather cards
- loading and error states
- dark gradient background
- polished professional design

Use only vanilla html css and javascript.
Keep the project to a maximum of 3 files.
"""
        },
        {
            "recursion_limit": 25
        },
    )

    print("\nFINAL STATE:\n")
    print(result)