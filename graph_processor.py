"""Overall agent."""
import json
from typing import TypedDict, Literal
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from pathlib import Path
from config import get_config
from langchain_core.messages import ToolMessage
from triage import triage_input
from schemas import State


from PIL import Image
import io
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver 

from dotenv import load_dotenv
load_dotenv()

def route_after_triage(
    state: State,
    #TODO: add draft_response
) -> Literal["save_statistics_node", "notify", "summarize_email_node"]:
    if state["triage"].response == "no":
        return "save_statistics_node"
    elif state["triage"].response == "notify":
        return "notify"
    elif state["triage"].response == "summarize":
        return "summarize_email_node"
    else:
        raise ValueError



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

def notify(state: State):
    print("\n\n\n>>>>> notify", state)
    pass


class ConfigSchema(TypedDict):
    db_id: int
    model: str


def save_statistics_node(state: State):
    print("\n\n\n>>>>> statistics_node", state)
    pass

def mail_action_node(state: State):
    print("\n\n\n>>>>> mail_action_node", state)
    pass

def summarize_email_node(state: State):
    print("\n\n\n>>>>> summarize_email_node", state)
    pass

graph_builder = StateGraph(State, config_schema=ConfigSchema)
graph_builder.set_entry_point("triage_input")
graph_builder.add_node(triage_input)
graph_builder.add_node(summarize_email_node)
graph_builder.add_node(mail_action_node)
graph_builder.add_node(notify)
graph_builder.add_node(save_statistics_node)

graph_builder.add_conditional_edges("triage_input", route_after_triage)
graph_builder.add_edge("summarize_email_node", "save_statistics_node")
graph_builder.add_edge("notify", "save_statistics_node")
graph_builder.add_edge("save_statistics_node", "mail_action_node")
graph_builder.add_edge("mail_action_node", END)



sqlite_conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
store = SqliteSaver(sqlite_conn)
graph_processor = graph_builder.compile(store=store)




'''

graph_builder = StateGraph(State, config_schema=ConfigSchema)
graph_builder.add_node(human_node)
graph_builder.add_node(triage_input)
graph_builder.add_node(draft_response)
graph_builder.add_node(send_message)
graph_builder.add_node(rewrite)
graph_builder.add_node(mark_as_read_node)
graph_builder.add_node(send_email_draft)
graph_builder.add_node(send_email_node)
graph_builder.add_node(bad_tool_name)
graph_builder.add_node(notify)
graph_builder.add_node(send_cal_invite_node)
graph_builder.add_node(send_cal_invite)
graph_builder.add_conditional_edges("triage_input", route_after_triage)
graph_builder.set_entry_point("triage_input")
graph_builder.add_conditional_edges("draft_response", take_action)
graph_builder.add_edge("send_message", "human_node")
graph_builder.add_edge("send_cal_invite", "human_node")
graph_builder.add_node(find_meeting_time)
graph_builder.add_edge("find_meeting_time", "draft_response")
graph_builder.add_edge("bad_tool_name", "draft_response")
graph_builder.add_edge("send_cal_invite_node", "draft_response")
graph_builder.add_edge("send_email_node", "mark_as_read_node")
graph_builder.add_edge("rewrite", "send_email_draft")
graph_builder.add_edge("send_email_draft", "human_node")
graph_builder.add_edge("mark_as_read_node", END)
graph_builder.add_edge("notify", "human_node")
graph_builder.add_conditional_edges("human_node", enter_after_human)
graph_processor = graph_builder.compile()"""
'''
