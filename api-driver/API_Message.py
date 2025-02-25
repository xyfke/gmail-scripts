import base64
import mimetypes
import os

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


def create_draft(service, input):

    emps = open(os.path.realpath(input), "r")
    log = open(os.path.realpath("../data/w2/draft_log.txt"), "a")

    count = 0

    for line in emps:
        name, email, has_two = line.strip().split("\t")
        draft_message(service, name, email, has_two, log)
        count += 1
    
    log.close()


def draft_message(service, name, email, has_two, log):
    mime_message = MIMEMultipart("alternative")

    mime_message['To'] = email
    mime_message['From'] = "w2@arrowworkforce.com"
    mime_message['Subject'] = "W2 - " + name

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

    #f = r"C:\Users\Accounting Admin\Documents\fafa-github\gmail-scripts\data\w2\outputs\pdfs\Abimael Martinez W2 (1).pdf"
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


    encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
    create_draft_request_body = {"message": {"raw": encoded_message}}

    draft = (
        service.users()
        .drafts()
        .create(userId="me", body=create_draft_request_body)
        .execute()
    )

    print(f'{name} Draft id: {draft["id"]}\tDraft message: {draft["message"]}', file=log)
    print(name)
    


    
