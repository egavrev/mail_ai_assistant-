"""Overall agent."""
import json
from typing import TypedDict, Literal
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from pathlib import Path
from config import get_config
from langchain_core.messages import ToolMessage
from triage import triage_input
from summarize import summarize_email
from notify import notify_user
from schemas import State
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

from PIL import Image
import io
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver 

from dotenv import load_dotenv
load_dotenv()

class EmailSummary(BaseModel):
    """Summary of an email."""
    summary: str = Field(description="A concise summary of the email content")
    key_points: list[str] = Field(description="List of key points from the email")
    action_items: list[str] = Field(description="List of any action items or tasks mentioned in the email")

class ConfigSchema(TypedDict):
    model: str

def summarize_email_node(state: State, config: dict, store: SqliteSaver):
    print("\n\n\n>>>>> summarize_email_node", state["email"]["subject"])
    return summarize_email(state, config, store)

def notify_node(state: State, config: dict, store: SqliteSaver):
    print("\n\n\n>>>>> notify_node", state["email"]["subject"])
    return notify_user(state, config, store)

def route_after_triage(
    state: State,
) -> Literal["summarize_email_node", "save_statistics_node", "notify_node", END]:
    """Route to the next node based on the triage result."""
    if state["triage"].response == "summarize":
        return "summarize_email_node"
    elif state["triage"].response == "notify":
        return "notify_node"
    elif state["triage"].response == "no":
        return "save_statistics_node"
    else:
        return END

def save_statistics_node(state: State):
    """Save statistics about the email."""
    print("\n\n\n>>>>> save_statistics_node")
    return {"messages": [HumanMessage(content="Statistics saved.")]}

def route_after_summarize(state: State) -> Literal["save_statistics_node", END]:
    """Route after summarization."""
    return "save_statistics_node"

def route_after_notify(state: State) -> Literal["save_statistics_node", END]:
    """Route after notification."""
    return "save_statistics_node"

def take_action(
    state: State,
) -> Literal[
    "send_message",
    "rewrite",
    "mark_as_read_node",
    "find_meeting_time",
    "send_cal_invite",
    "bad_tool_name",
]:
    prediction = state["messages"][-1]
    if len(prediction.tool_calls) != 1:
        raise ValueError
    tool_call = prediction.tool_calls[0]
    if tool_call["name"] == "Question":
        return "send_message"
    elif tool_call["name"] == "ResponseEmailDraft":
        return "rewrite"
    elif tool_call["name"] == "Ignore":
        return "mark_as_read_node"
    elif tool_call["name"] == "MeetingAssistant":
        return "find_meeting_time"
    elif tool_call["name"] == "SendCalendarInvite":
        return "send_cal_invite"
    else:
        return "bad_tool_name"

def bad_tool_name(state: State):
    tool_call = state["messages"][-1].tool_calls[0]
    message = f"Could not find tool with name `{tool_call['name']}`. Make sure you are calling one of the allowed tools!"
    last_message = state["messages"][-1]
    last_message.tool_calls[0]["name"] = last_message.tool_calls[0]["name"].replace(
        ":", ""
    )
    return {
        "messages": [
            last_message,
            ToolMessage(content=message, tool_call_id=tool_call["id"]),
        ]
    }



# Create the store first
sqlite_conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
store = SqliteSaver(sqlite_conn)

# Build the graph
graph_builder = StateGraph(State,  config_schema=ConfigSchema)

# Add all nodes with their required parameters
graph_builder.add_node("triage_input", lambda state, config: triage_input(state, config, store))
graph_builder.add_node("summarize_email_node", lambda state, config: summarize_email_node(state, config, store))
graph_builder.add_node("notify_node", lambda state, config: notify_node(state, config, store))
graph_builder.add_node("save_statistics_node", save_statistics_node)

# Set the entry point
graph_builder.set_entry_point("triage_input")

# Add edges
graph_builder.add_conditional_edges(
    "triage_input",
    route_after_triage,
    {
        "summarize_email_node": "summarize_email_node",
        "notify_node": "notify_node",
        "save_statistics_node": "save_statistics_node",
        END: END,
    }
)

# Add direct edges to save_statistics_node
graph_builder.add_edge("summarize_email_node", "save_statistics_node")
graph_builder.add_edge("notify_node", "save_statistics_node")
graph_builder.add_edge("save_statistics_node", END)

# Compile the graph
graph_processor = graph_builder.compile(interrupt_after=["notify_node"])
