import base64
import mimetypes
import os
from typing import IO

from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

from googleapiclient.discovery import build

pdf_location = r"C:\Users\Accounting Admin\Documents\fafa-github\gmail-scripts\data\w2\outputs\pdfs"


def create_draft(service, input : str):
    """
    Based on the input text file, process each entries in the file to create gmail drafts for review
    prior to send.
    Args:
        service (Any): Google service tool to connect to gmail API
        input (str): path of text file with temp name, email and flag indicating how many W2s they have
    """

    emps = open(os.path.realpath(input), "r")
    log = open(os.path.realpath("../data/w2/draft_log.txt"), "a")

    count = 0

    for line in emps:
        name, email, has_two = line.strip().split("\t")
        draft_message(service, name, email, has_two, log)
        count += 1
    
    log.close()


def draft_message(service, name : str, email : str, has_two : str, log : IO):
    """
    Based on the input text file, process each entries in the file to create gmail drafts for review
    prior to send.
    Args:
        service (Any): Google service tool to connect to gmail API
        name (str): name of temp
        email (str): corresponding email
        has_two (str): whether or not there's two W2 files
        log (IO): file object of log file
    """

    # construct message header
    mime_message = MIMEMultipart("alternative")
    mime_message['To'] = email
    mime_message['From'] = "w2@arrowworkforce.com"
    mime_message['Subject'] = "W2 - " + name

    # message content
    html = """
    <p>
    Hello, <br><br>
    Please disregard previous W2s received from this email address and refer to the W2 forms attached in this email for your tax reporting.
    <br><br>
    Kindest Regards,<br>
    <span><strong style="color: rgb(68, 114, 196);">Accounting Department</strong></span> <br>
    <span>Arrow Group of Companies</span> <br>
    <span><a href="http://www.arrowworkforce.com/" target="_blank" style="color: blue;">www.arrowworkforce.com</a></span> <br>
    <span><strong style="color: rgb(8, 97, 173);">FOR WHEN IT MATTERS</strong></span></p>
    """

    part_html = MIMEText(html, "html")
    mime_message.attach(part_html)

    # Attempt to add attachment
    # If it fails, then make a note in the log file, but the draft will still be created for manually adding
    try:
        f1 = pdf_location + "\\" + name + " W2.pdf"
        with open(f1, "rb") as fi:
            part = MIMEApplication(fi.read(), Name=os.path.basename(f1))
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f1)
            mime_message.attach(part)

        if has_two == "TRUE":
            f2 = pdf_location + "\\" + name + " W2 (1).pdf"
            with open(f1, "rb") as fi:
                part = MIMEApplication(fi.read(), Name=os.path.basename(f2))
                part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f2)
                mime_message.attach(part)
    except:
        print(name + ": Missing attachments", file=log)

    # send draft create to gmail API
    encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
    create_draft_request_body = {"message": {"raw": encoded_message}}
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body=create_draft_request_body)
        .execute()
    )

    # print to log indicating draft and message id
    print(f'{name} Draft id: {draft["id"]}\tDraft message: {draft["message"]}', file=log)
    print(name) # process tracking
    


    
