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



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

output_path = "output/"

def extractHeaders(headers : list):
    header_dict = {}

    for header in headers:
        header_dict[header["name"]] = header["value"]

    return header_dict


def extract_basic_info(service, messages : dict, output_file : IO, error_file : IO) -> None:
    """Parse message and extract basic information (date, to, from, subject, attachments) to output file

    Args:
        messages (dict): message object obtained from gmail API request
        output_file (IO): output file object
        error_file (IO): error file object
    """
    #test = open("test.txt", "a")
    for message in messages:
        m_id = message["id"]
        mail = service.users().messages().get(userId='me', id=m_id).execute()

        try:
            header_dict = extractHeaders(mail['payload']['headers'])
            fr = re.findall(r"\<(.*?)\>", header_dict['From'])[0]
            try:
                to= re.findall(r"\<(.*?)\>", header_dict['To'])[0]
            except:
                to = header_dict['To']
            subject = header_dict['Subject']
            date = datetime.strptime(header_dict['Date'], '%a, %d %b %Y %H:%M:%S %z')
            #subject, date, to = "", "", ""
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

            print("{}\t{}\t{}\t{}\t{}\t{}".format(date, subject, fr, to, name_or_ssn, filename), file=output_file)
        except:
            print(m_id, file=test)
            #print(json.dumps(mail, sort_keys=True, indent=4), file=test)
            #print(header_dict)
            #break
    
    #test.close()


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
    print("Date\tSubject\tFrom\tTo\tName or SSN\tFilenames", file=result)

    page_token = ""    # first token
    count = 0       # count number of emails

    while page_token is not None:

        results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        messages = results.get('messages', [])

        count += len(messages)

        parse_func(service, messages, result, error_log)

        if ("nextPageToken" in results):
            page_token = results["nextPageToken"]
        else:
            page_token = None

        print("Next token: " + str(page_token))
        print(len(messages))
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
        query = "in:sent has:attachment after:2025/01/30"
        get_message_queries(service, query, "w2_summary.csv", False, extract_basic_info)
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


connect_service()