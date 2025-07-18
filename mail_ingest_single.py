import argparse
import asyncio
from typing import Optional
from graph_processor import graph_processor
from mail_processor import fetch_emails
from email_data import email_summarize, email_notify
from db_manager import init_db
import uuid
import hashlib
import datetime
from datetime import datetime as dt
import json
from pathlib import Path
from PIL import Image
import io


from langfuse.langchain import CallbackHandler
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
def main():
    #result = graph_processor.invoke({"email": email_summarize}, config={"callbacks": [langfuse_handler]})
    #init_db()
    result = graph_processor.invoke({"email": email_notify}, config={"callbacks": [langfuse_handler]})
        

        



main()
