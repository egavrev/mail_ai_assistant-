import argparse
import asyncio
from typing import Optional
from graph_processor import graph_processor
from mail_processor import fetch_emails

import uuid
import hashlib
import datetime
from datetime import datetime as dt
import json
from pathlib import Path
from PIL import Image
import io


from langfuse.langchain import CallbackHandler

from db_manager import update_email_metadata # init_db should be called once at app startup
 
from langfuse import get_client
 
langfuse = get_client()

if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


langfuse_handler = CallbackHandler()

_ROOT = Path(__file__).parent.absolute()

def parse_date(date_str):
    try:
        return dt.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        raise argparse.ArgumentTypeError(f'Invalid date format. Please use YYYY-MM-DD format: {e}')


#####
# This script is used to ingest emails from a given email address for a given period of time.
# period is defining in days
def main(
    start_date: datetime.datetime = datetime.datetime.now() - datetime.timedelta(days=30),
    end_date: datetime.datetime = datetime.datetime.now(),
    gmail_token: Optional[str] = None,
    gmail_secret: Optional[str] = None,
    email_address: Optional[str] = None,
    save_graph: bool = False,
):
   
    
    #TODO 1: revuild fetch_group_emails to fetch emails for a given period
    for email in fetch_emails(
        email_address,
        start_date=start_date,
        end_date=end_date,
        gmail_token=gmail_token,
        gmail_secret=gmail_secret,
    ):
        thread_id = str(
            uuid.UUID(hex=hashlib.md5(email["thread_id"].encode("UTF-8")).hexdigest())
        )
        result =  graph_processor.invoke({"email":email}, config={"callbacks": [langfuse_handler]})
        
        

        if save_graph:
            _ROOT = Path(__file__).parent.absolute()
            png_bytes = graph_processor.get_graph(xray=True).draw_mermaid_png()
            img = Image.open(io.BytesIO(png_bytes))
            img.save(str(_ROOT / "graph.png"))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=datetime.datetime.now() - datetime.timedelta(days=30),
        help="The start date to ingest emails from in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=datetime.datetime.now(),
        help="The end date to ingest emails to in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--gmail-token",
        type=str,
        default=None,
        help="The token to use in communicating with the Gmail API.",
    )
    parser.add_argument(
        "--gmail-secret",
        type=str,
        default=None,
        help="The creds to use in communicating with the Gmail API.",
    )
    parser.add_argument(
        "--email-address",
        type=str,
        default=None,
        help="The email address to use to fetch emails from",
    )
    parser.add_argument(
        "--save-graph",
        type=bool,
        default=False,
        help="Whether to save the graph image to a file",
    )

    #call for update_email_metadata
    parser.add_argument(
        "--update-email-metadata",
        type=bool,
        default=False,
        help="Whether to update the email metadata",
    )
    
    args = parser.parse_args()
    main(
        start_date=args.start_date,
        end_date=args.end_date,
        gmail_token=args.gmail_token,
        gmail_secret=args.gmail_secret,
        email_address=args.email_address,
        save_graph=args.save_graph,
    )
