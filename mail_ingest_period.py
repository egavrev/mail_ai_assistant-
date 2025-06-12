import argparse
import asyncio
from typing import Optional
#from graph_processor import graph_processor
from mail_processor import fetch_emails

import uuid
import hashlib
import datetime



#####
# This script is used to ingest emails from a given email address for a given period of time.
# period is defining in days
def main(
    start_date: datetime.datetime = datetime.datetime.now() - datetime.timedelta(days=30),
    end_date: datetime.datetime = datetime.datetime.now(),
    gmail_token: Optional[str] = None,
    gmail_secret: Optional[str] = None,
    email_address: Optional[str] = None,
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
        #TODO 2: add graph call
        #result = await graph_processor.ainvoke(email)
        recent_email = thread_info["metadata"].get("email_id")
        if recent_email == email["id"]:
            if early:
                break
            else:
                if rerun:
                    pass
                else:
                    continue

        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start-date",
        type=datetime.datetime,
        default=datetime.datetime.now() - datetime.timedelta(days=30),
        help="The start date to ingest emails from in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date",
        type=datetime.datetime,
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

    args = parser.parse_args()
    main(
        start_date=args.start_date,
        end_date=args.end_date,
        gmail_token=args.gmail_token,
        gmail_secret=args.gmail_secret,
        email_address=args.email_address,
    )
