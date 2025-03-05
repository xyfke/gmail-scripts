import os.path
import json
import time
import re
from datetime import datetime
import base64
import email

# specify type hints
from typing import IO
from collections.abc import Callable

# Gettting the main body of the email
from bs4 import BeautifulSoup

# Assist with translation
import asyncio
from googletrans import Translator, constants
from pprint import pprint



output_path = "../data/w2-EIN/outputs/"
w2_path = "../data/w2/outputs/"
label_path = "../data/labels/label.txt"
recipients = set()

exclude = ["kimberlyf@canadianexecutivesearch.com", "alicia@arrowworkforce.com", "areti@canadianexecutivesearch.com", 
           "jessica@canadianexecutivesearch.com", "soumela@arrowworkforce.com", "info@arrowworkforce.com"]

def get_labels(service) -> list:
    list_labels = []

    if os.path.isfile(os.path.realpath(label_path)):
        label_file = open(os.path.realpath(label_path), "r")
        for label in label_file:
            list_labels.append(label.strip())
        label_file.close()
    else:
        label_file = open(os.path.realpath(label_path), "a")
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return
        #print("Labels:")
        for label in labels:
            list_labels.append(label['name'])
            print("{}\t{}".format(label['name'], label["id"]), file=label_file)

        label_file.close()

    return list_labels


def extractHeaders(headers : list) -> dict:
    """ Extract message header information

    Args:
        headers (list): a list of (name, value) pairs of header content

    Returns:
        dict: a dictionary of contents in (name, value) pair
    """
    header_dict = {}

    for header in headers:
        header_dict[header["name"]] = header["value"]

    return header_dict

def extract_basic_info(service, messages : list, output_file : IO, error_file : IO) -> None:
    """Parse message and extract basic information (date, to, from, subject, attachments) to output file

    Args:
        messages (list): message object obtained from gmail API request
        output_file (IO): output file object
        error_file (IO): error file object
    """
    for message in messages:
        m_id = message["id"]
        mail = service.users().messages().get(userId='me', id=m_id).execute()

        try:
            header_dict = extractHeaders(mail['payload']['headers'])
            fr = re.findall(r"\<(.*?)\>", header_dict['From'])[0]

            try:
                # Some to may not have name
                to= re.findall(r"\<(.*?)\>", header_dict['To'])[0]
            except:
                to = header_dict['To']

            if (to in recipients):
                continue

            recipients.add(to)
            subject = header_dict['Subject']
            date = datetime.strptime(header_dict['Date'], '%a, %d %b %Y %H:%M:%S %z')
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
            print(m_id, file=error_file)
            #print(json.dumps(mail, sort_keys=True, indent=4), file=test)
            #print(header_dict)
            #break
    
    #test.close()

def get_body_before_gmail_reply_date(msg):
    body_before_gmail_reply = msg
    # regex for date format like "On Thu, Mar 24, 2011 at 3:51 PM"
    matching_string_obj = re.search(r"\w+\s+\w+[,]\s+\w+\s+\d+[,]\s+\d+\s+\w+\s+\d+[:]\d+\s+\w+.*", msg)
    if matching_string_obj:
        # split on that match, group() returns full matched string
        body_before_gmail_reply_list = msg.split(matching_string_obj.group())
        # string before the regex match, so the body of the email
        body_before_gmail_reply = body_before_gmail_reply_list[0]
    
    return re.sub(r'http\S+', '', body_before_gmail_reply)

CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});') 

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

async def trans(original):
    translator = Translator()
    translation = await translator.translate(original)
    return translation.text

def extract_thread_info(service, threads : list, output_file : IO, error_file : IO) -> None:
    """Go through each thread and create a summary of informaiton

    Args:
        service (_type_): Used to make additional API calls with each message
        threads (list): a list of threads to process
        output_file (IO): the summary file
        error_file (IO): any error that arises
    """
    #print("THREAD")
    # process content of each thread
    for thread in threads:
        tdata = service.users().threads().get(userId='me', id=thread['id']).execute()

        msg_str = ""
        to, fr = "", ""
        subject = ""
        date = ""

        completed = False

        #print(json.dumps(tdata, sort_keys=True, indent=4), file=error_file)
        #exit(0)

        # process message within each thread
        for message in tdata['messages']:

            #try:
            headers = extractHeaders(message['payload']['headers'])
            if (headers['From'] == "\"W2 .\" <w2@arrowworkforce.com>"):
                continue

            if ("Label_6457202177257884186" in message['labelIds']) or ("Label_1" in message['labelIds']):
                completed = True
            
            try:
                fr = re.findall(r"\<(.*?)\>", headers['From'])[0]
            except:
                fr = headers["From"]
            try:
                # Some to may not have name
                to= re.findall(r"\<(.*?)\>", headers['To'])[0]
            except:
                to = headers['To']

            if (fr in recipients) and (fr not in exclude):
                continue

            try:
                subject = headers['Subject']
            except:
                subject = ""

            try:
                date = datetime.strptime(headers['Date'], '%a, %d %b %Y %H:%M:%S %z')
            except:
                date = headers['Date']

            parse = []

            if 'parts' in message['payload']:
                parse = message['payload']['parts']
            else:
                parse = [message['payload']]

            for parts in parse:
                if (parts['mimeType'] == 'text/plain'):
                    sub_msg = parts['body'].get('data', "")
                    decoded = base64.urlsafe_b64decode(sub_msg).decode("utf-8").replace('\r\n', '&CHAR(10)')
                    msg_str += get_body_before_gmail_reply_date(decoded)
                    #print(decoded)
                elif (parts['mimeType'] == 'text/html'):
                    sub_msg = parts['body'].get('data', "")
                    #decoded = cleanhtml(base64.urlsafe_b64decode(sub_msg).decode().replace('\r\n', ' '))
                    v = base64.urlsafe_b64decode(sub_msg).decode()
                    soup = BeautifulSoup(v, features="html.parser")
                    # kill all script and style elements
                    #print(v, file=error_file)
                    for script in soup(["script", "style", "class", "id", "name"]):
                        script.decompose()    # rip it out

                    # get text
                    text = soup.stripped_strings
                    joined = ' '.join(text).encode('ascii', 'ignore').decode("utf-8").replace('\r\n', '&CHAR(10)')
                    msg_str += joined

            print(json.dumps(message, sort_keys=True, indent=4), file=error_file)

        english = asyncio.run(trans(msg_str))
        print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(date, completed, fr, to, subject, msg_str, english), file=output_file)
        recipients.add(fr)
            #except:
                #print(json.dumps(message, sort_keys=True, indent=4), file=error_file)
                #exit(0)



def get_thread_queries(service, query : str, summary : str, mark_complete : bool, parse_func : Callable) -> None:
    """ Retrieve and process each thread in the query

    Args:
        service (_type_): Google API services
        query (str): email query
        filename (str): name of file to store results
        mark_complete (bool): whether or not to add column mark_complete
        parse_func (Callable) : the parsing function
    """
    #print("THREAD")
    result = open(os.path.realpath(w2_path + summary), "a", encoding="utf-8")
    error_log = open(os.path.realpath(w2_path + "error.txt"), "a")
    print("Date\tCompleted\tFrom\tTo\tSubject\tContent", file=result)

    page_token = ""
    count = 0
    recipients = set()

    # get all thread under query
    while page_token is not None:
        results = service.users().threads().list(userId='me', q=query, pageToken=page_token).execute()
        threads = results.get('threads', [])
        
        count += len(threads)
        parse_func(service, threads, result, error_log)
        #print(len(threads))

        if ("nextPageToken" in results):
            page_token = results["nextPageToken"]
        else:
            page_token = None

        print("Next token: " + str(page_token))
        print(len(threads))
        print()
        time.sleep(60)

        

    result.close()
    error_log.close()
            




def get_message_queries(service, query : str, filename : str, mark_complete : bool, parse_func : Callable) -> None:
    """ Retrieve a list of emails from given query

    Args:
        service (_type_): api service
        query (str): email query
        filename (str): name of file to store results
        mark_complete (bool): whether or not to add column mark_complete
        parse_func (Callable) : the parsing function
    """
    recipients = set()

    result = open(os.path.realpath(output_path + filename), "a")
    error_log = open(os.path.realpath(output_path + "error.txt"), "a")
    print("Date\tSubject\tFrom\tTo\tName or SSN\tFilenames", file=result)

    page_token = ""    # first token
    count = 0       # count number of emails

    while page_token is not None:

        results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        messages = results.get('messages', [])

        count += len(messages)

        parse_func(service, messages, result, error_log)

        # check to see if there are additional messages
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
     