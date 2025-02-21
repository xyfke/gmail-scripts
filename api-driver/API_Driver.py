import os.path
import json
import time
import re
import datetime

# specify type hints
from typing import IO
from collections.abc import Callable

# Libraries used for connection
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

output_path = "output/"


def extract_basic_info(service, messages : dict, output_file : IO, error_file : IO) -> None:
    """Parse message and extract basic information (date, to, from, subject, attachments) to output file

    Args:
        messages (dict): message object obtained from gmail API request
        output_file (IO): output file object
        error_file (IO): error file object
    """
    for message_info in messages:
        m_id = message_info["id"]
        mail = service.users().messages().get(userId='me', id=m_id).execute()

        try:
            fr = re.findall(r"\<(.*?)\>", mail['payload']['headers'][6]['value'])[0]
            to= re.findall(r"\<(.*?)\>", mail['payload']['headers'][7]['value'])[0]
            subject = mail['payload']['headers'][5]['value']
            date = datetime.strptime(mail['payload']['headers'][1]['value'], '%a, %d %b %Y %H:%M:%S %z')
            filename_arr = []
            name_or_ssn = None

            # Parse attachment portion
            for part in mail['payload']['parts']:
                if ("attachmentId" in part['body']):
                    filename_arr.append(part["filename"])
                    if name_or_ssn is None:
                        if "Copy" in part['filename']:
                            name_or_ssn = part['filename'].split(" Copy ")[0]
                        elif "W2" in part['filename']:
                            name_or_ssn = part['filename'].split("W2")[0].strip()

            filename = "\t".join(filename_arr)

            print("{}\t{}\t{}\t{}\t{}".format(date, subject, fr, to, filename), file=output_file)
        except:
            print(m_id, file=error_file)


def get_message_queries(service, query : str, filename : str, mark_complete : bool, parse_func : Callable) -> None:
    """ Retrieve a list of emails from given query

    Args:
        service (_type_): api service
        query (str): email query
        filename (str): name of file to store results
        mark_complete (bool): whether or not to add column mark_complete
        parse_func (Callable) : the parsing function
    """

    result = open(output_path + filename, "a")
    error_log = open(output_path + "error.txt", "a")

    page_token = ""    # first token
    count = 0       # count number of emails

    while page_token is not None:

        results = service.users().messages().list(userId='me', q=query, pageToken = page_token).execute()
        messages = results.get("message", [])

        count += len(messages)
        print(len(messages))

        parse_func(service, messages, result, error_log)

        if ("nextPageToken" in results):
            page_token = results["nextPageToken"]
        else:
            page_token = None

        print("Next token: " + str(page_token))
        print()
        time.sleep(60)

    result.close()
    error_log.close()
        

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
        #get_messages(service)

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