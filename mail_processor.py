import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, TypedDict
import os

from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64

logger = logging.getLogger(__name__)
_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]
_ROOT = Path(__file__).parent.absolute()
_PORT = 54191
_SECRETS_DIR = _ROOT / ".secrets"
_SECRETS_PATH = str(_SECRETS_DIR / "secrets.json")
_TOKEN_PATH = str(_SECRETS_DIR / "token.json")

from dotenv import load_dotenv
load_dotenv()

class EmailData(TypedDict):
    id: str
    thread_id: str
    from_email: str
    subject: str
    page_content: str
    send_time: str
    to_email: str


def get_credentials(
    gmail_token: str | None = None, gmail_secret: str | None = None
) -> Credentials:
    creds = None
    _SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    gmail_token = gmail_token or os.getenv("GMAIL_TOKEN")
    if gmail_token:
        with open(_TOKEN_PATH, "w") as token:
            token.write(gmail_token)
    gmail_secret = gmail_secret or os.getenv("GMAIL_SECRET")
    if gmail_secret:
        with open(_SECRETS_PATH, "w") as secret:
            secret.write(gmail_secret)
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH)

    if not creds or not creds.valid or not creds.has_scopes(_SCOPES):
        if (
            creds
            and creds.expired
            and creds.refresh_token
            and creds.has_scopes(_SCOPES)
        ):
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(_SECRETS_PATH, _SCOPES)
            creds = flow.run_local_server(port=_PORT)
        with open(_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return creds


def extract_message_part(msg):
    """Recursively walk through the email parts to find message body."""
    if msg["mimeType"] == "text/plain":
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    elif msg["mimeType"] == "text/html":
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    if "parts" in msg:
        for part in msg["parts"]:
            body = extract_message_part(part)
            if body:
                return body
    return "No message body available."


def parse_time(send_time: str):
    try:
        parsed_time = parser.parse(send_time)
        return parsed_time
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error parsing time: {send_time} - {e}")


def fetch_emails(
    to_email,
    start_date: datetime,
    end_date: datetime,
    gmail_token: str | None = None,
    gmail_secret: str | None = None,
) -> Iterable[EmailData]:
    print("Token path :=>", _TOKEN_PATH)
    print("Secrets path :=>", _SECRETS_PATH)
    creds = get_credentials(gmail_token, gmail_secret)
    print("creds", creds)

    print("start_date", start_date)
    print("end_date", end_date)
    print("gmail_token", gmail_token)
    print("gmail_secret", gmail_secret)
    print("to_email", to_email)

    service = build("gmail", "v1", credentials=creds)
    after = int(start_date.timestamp())
    before = int(end_date.timestamp())

    query = f"(to:{to_email} OR from:{to_email}) after:{after} before:{before}"
    messages = []
    nextPageToken = None
    # Fetch messages matching the query
    while True:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=nextPageToken)
            .execute()
        )
        if "messages" in results:
            messages.extend(results["messages"])
        nextPageToken = results.get("nextPageToken")
        if not nextPageToken:
            break

    count = 0
    for message in messages:
        try:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            thread_id = msg["threadId"]
            payload = msg["payload"]
            headers = payload.get("headers")
            # Get the thread details
            thread = service.users().threads().get(userId="me", id=thread_id).execute()
            messages_in_thread = thread["messages"]
            # Check the last message in the thread
            last_message = messages_in_thread[-1]
            last_headers = last_message["payload"]["headers"]
            from_header = next(
                header["value"] for header in last_headers if header["name"] == "From"
            )
            last_from_header = next(
                header["value"]
                for header in last_message["payload"].get("headers")
                if header["name"] == "From"
            )
            if to_email in last_from_header:
                yield {
                    "id": message["id"],
                    "thread_id": message["threadId"],
                    "user_respond": True,
                }
            # Check if the last message was from you and if the current message is the last in the thread
            if to_email not in from_header and message["id"] == last_message["id"]:
                subject = next(
                    header["value"] for header in headers if header["name"] == "Subject"
                )
                from_email = next(
                    (header["value"] for header in headers if header["name"] == "From"),
                    "",
                ).strip()
                _to_email = next(
                    (header["value"] for header in headers if header["name"] == "To"),
                    "",
                ).strip()
                if reply_to := next(
                    (
                        header["value"]
                        for header in headers
                        if header["name"] == "Reply-To"
                    ),
                    "",
                ).strip():
                    from_email = reply_to
                send_time = next(
                    header["value"] for header in headers if header["name"] == "Date"
                )
                # Only process emails that are less than an hour old
                parsed_time = parse_time(send_time)
                body = extract_message_part(payload)
                yield {
                    "from_email": from_email,
                    "to_email": _to_email,
                    "subject": subject,
                    "page_content": body,
                    "id": message["id"],
                    "thread_id": message["threadId"],
                    "send_time": parsed_time.isoformat(),
                }
                count += 1
        except Exception:
            logger.info(f"Failed on {message}")

    logger.info(f"Found {count} emails.")


def mark_as_read(
    message_id,
    gmail_token: str | None = None,
    gmail_secret: str | None = None,
):
    creds = get_credentials(gmail_token, gmail_secret)

    service = build("gmail", "v1", credentials=creds)
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()



def format_datetime_with_timezone(dt_str, timezone="US/Pacific"):
    """
    Formats a datetime string with the specified timezone.

    Args:
    dt_str: The datetime string to format.
    timezone: The timezone to use for formatting.

    Returns:
    A formatted datetime string with the timezone abbreviation.
    """
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    tz = pytz.timezone(timezone)
    dt = dt.astimezone(tz)
    return dt.strftime("%Y-%m-%d %I:%M %p %Z")


def print_events(events):
    """
    Prints the events in a human-readable format.

    Args:
    events: List of events to print.
    """
    if not events:
        return "No events found for this day."

    result = ""

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        summary = event.get("summary", "No Title")

        if "T" in start:  # Only format if it's a datetime
            start = format_datetime_with_timezone(start)
            end = format_datetime_with_timezone(end)

        result += f"Event: {summary}\n"
        result += f"Starts: {start}\n"
        result += f"Ends: {end}\n"
        result += "-" * 40 + "\n"
    return result

