from dotenv import load_dotenv
from langchain_groq import ChatGroq
from prompts import *
from states import *
from tools import *
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.globals import set_verbose, set_debug
import time

load_dotenv()
set_debug(False)
set_verbose(False)

# llm = ChatGroq(model="openai/gpt-oss-120b")
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=2000,
)

# user_prompt = "Create a simple calculator web application"

def planner_agent(state: dict)->dict:
    user_prompt = state.get("user_prompt")
    resp =  llm.with_structured_output(Plan).invoke(planner_prompt(user_prompt))
    if resp is None:
        raise ValueError("planner response is None")
    return {"plan": resp}

def architect_agent(state:dict)->dict:
    plan: Plan = state.get("plan")
    resp = llm.with_structured_output(TaskPlan).invoke(architect_prompt(plan))
    if resp is None:
        raise ValueError("architect response is None")
    resp.plan = plan
    return {"task_plan": resp}

def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]

    system_prompt = coder_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Operation: {current_task.operation}\n"
        "Use read_file(path) to read any existing files you need for context.\n"
        "Use write_file(path, content, mode) to save your changes.\n"
        "For large files, first use mode='overwrite' then use mode='append' for additional chunks."
        "If operation is 'append', you MUST use mode='append'.\n"
        "If operation is 'overwrite', you MUST use mode='overwrite'.\n"
    )

    coder_tools = [read_file,write_file,list_file,get_current_directory,run_cmd,]
    react_agent = create_react_agent(llm, coder_tools)
    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]},config={"recursion_limit": 5})
    time.sleep(5)

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph = StateGraph(dict)

graph.add_node("planner",planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder",coder_agent)

graph.add_edge("planner","architect")
graph.add_edge("architect","coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")

agent = graph.compile()
# Build a colourful modern todo app in html css and js
if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a minimal todo app in html css and js"},
                          {"recursion_limit": 100})
    print("Final State:", result)
