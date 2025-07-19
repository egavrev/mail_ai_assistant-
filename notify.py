from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.checkpoint.sqlite import SqliteSaver
from schemas import State
from config import get_config

class NotificationMessage(BaseModel):
    message: str = Field(description="Notification message for the user")
    suggestion: str = Field(description="Suggested action for the user")
    sent: bool = Field(description="Whether this notification was sent to the user", default=False)

def notify_user(state: State, config: RunnableConfig, store: SqliteSaver):
    """Generate a notification message for the user and record it in the store."""
    prompt_config = get_config(config)
    email = state["email"]
    message = (
        f"Attention required: You received an email from {email['from_email']} with subject '{email['subject']}'. "
        f"The assistant is unsure how you should react. Please review the email and decide on the appropriate action."
    )
    suggestion = "Please check the email and decide if you want to reply, ignore, or take another action."
    notification = NotificationMessage(message=message, suggestion=suggestion, sent=False)

    # Save to checkpoint store in a new namespace
    write_config = {"configurable": {"thread_id": state["email"]["id"], "checkpoint_ns": "email_notifications"}}
    checkpoint = {
        "v": 2,
        "ts": email["send_time"],
        "id": email["id"],
        "state": state,
    }
   
    store.put(
            write_config,
            checkpoint,
            notification.dict(),
            {email["id"]: notification.dict()}
        )

    # Update the email_notification table in the database
    from db_manager import update_email_notification
    update_email_notification(
        email_data=email,
        notification_status="none",
        notification_reason=message,
        action_to_take=None
    )

    return {
        "notification": notification,
        "messages": [ToolMessage(
            content=message,
            tool_call_id="notify"
        )]
    } 