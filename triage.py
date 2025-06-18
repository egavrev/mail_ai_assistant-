"""Agent responsible for triaging the email, can either ignore it, try to respond, or notify user."""

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import RemoveMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from schemas import (
    State,
    RespondTo,
)
#from fewshot import get_few_shot_examples
from config import get_config


triage_prompt = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.

{background}. 

{name} gets lots of emails. Your job is to categorize the below email to triage them properly.

Emails that are not worth responding to:
{triage_no}

Emails that are worth to summarize:
{summarize_email}

There are also other things that {name} should know about, but don't require an email response. For these, you should notify {name} (using the `notify` response). Examples of this include:
{triage_notify}

For emails not worth responding to, respond `no`. For something where {name} should respond over email, respond `email`. If it's important to notify {name}, but no email is required, respond `notify`. \

If unsure, opt to `notify` {name} - you will learn from this in the future.

{fewshotexamples}

Please determine how to handle the below email thread:

From: {author}
To: {to}
Subject: {subject}

{email_thread}"""

#TODO: make it async and add store
def triage_input(state: State, config: RunnableConfig, store: SqliteSaver):
    model = config["configurable"].get("model", "gpt-4o")
    llm = ChatOpenAI(model=model, temperature=0)
    print("state", state["email"]["from_email"])
    #examples = await get_few_shot_examples(state["email"], store, config)
    #TODO: add fewshot examples link iht store
    examples = ""
    prompt_config = get_config(config)
    input_message = triage_prompt.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        to=state["email"].get("to_email", ""),
        subject=state["email"]["subject"],
        fewshotexamples=examples,
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        background=prompt_config["background"],
        triage_no=prompt_config["triage_no"],
        summarize_email=prompt_config["summarize_email"],
        triage_notify=prompt_config["triage_notify"],
    )
    model = llm.with_structured_output(RespondTo).bind(
        tool_choice={"type": "function", "function": {"name": "RespondTo"}}
    )
    response =  model.invoke(input_message)
    print("response", response)
    if len(state["messages"]) > 0:
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"]]
        return {"triage": response, "messages": delete_messages}
    else:
        return {"triage": response}
