import os.path
import json
import time
import re
from datetime import datetime

# specify type hints
from typing import IO
from collections.abc import Callable

# Libraries used for connection
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import API_Search
import API_Message


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.readonly"]

output_path = "output/"

def connect_service():
    """
    Create a connection to the perform queries in obtaining information from 
    gmail account
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        # Track all attachments coming rom w2 email
        #query = "in:sent has:attachment after:2025/01/30"
        #API_Search.get_message_queries(service, query, "w2_summary.csv", False, API_Search.extract_basic_info)

        API_Message.create_draft(service, r"../data/w2-EIN/inputs/send_list.txt")

        #get_message_debug(service)


        #results = service.users().labels().list(userId="me").execute()
        #labels = results.get("labels", [])

        #if not labels:
        #  print("No labels found.")
        #  return
        #print("Labels:")
        #for label in labels:
        #  print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


connect_service()