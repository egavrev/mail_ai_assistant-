"""Agent responsible for summarizing emails using GPT-4."""

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
import json
from langgraph.checkpoint.sqlite import SqliteSaver

from schemas import State
from config import get_config

class EmailSummary(BaseModel):
    """Summary of an email."""
    summary: str = Field(description="A concise summary of the email content")
    key_points: list[str] = Field(description="List of key points from the email")
    action_items: list[str] = Field(description="List of any action items or tasks mentioned in the email")

summarize_prompt = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.

{background}

Your task is to create a comprehensive summary of the email that will help {name} quickly understand its contents and any required actions. Please:

1. Create a concise summary of the main message
2. Extract key points that {name} should be aware of
3. Identify any action items or tasks that require attention

Please analyze the following email:

From: {author}
To: {to}
Subject: {subject}

{email_thread}"""

def summarize_email(state: State, config: RunnableConfig, store: SqliteSaver):
    """Summarize the email content using GPT-4."""
    model = config["configurable"].get("model", "gpt-4")
    llm = ChatOpenAI(model=model, temperature=0)
    
    prompt_config = get_config(config)
    input_message = summarize_prompt.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        to=state["email"].get("to_email", ""),
        subject=state["email"]["subject"],
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        background=prompt_config["background"]
    )
    
    model = llm.with_structured_output(EmailSummary, method="function_calling")
    summary = model.invoke(input_message)
    
    # Save to checkpoint store
    #write_config = {"configurable": {"thread_id": "1", "checkpoint_ns": "email_summaries"}}
    #try:
    write_config = {"configurable": {"thread_id": state["email"]["id"], "checkpoint_ns": "email_summaries"}}
    checkpoint = {
        "v": 2,
        "ts": state["email"]["send_time"],
        "id": state["email"]["id"]
    }
   
    store.put(
            write_config,
            checkpoint,
            summary.dict(),
            {state["email"]["id"]: summary.dict()}
        )
    #except Exception as e:
     #   print(f"Warning: Failed to save summary to store: {e}")
    
    return {
        "summary": summary,
        "messages": [ToolMessage(
            content=f"Email summarized successfully. Key points: {', '.join(summary.key_points)}",
            tool_call_id="summary"
        )]
    } 