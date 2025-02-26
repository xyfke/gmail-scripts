# Gmail Scripts

## Requirements

- Setup gmail project and enable gmail API
- Generate authentication tokens

## Goal

The motivation behind this project is to generate a summary of the requests received by the [w2@arrowworkforce.com](w2@arroworkforce.com) email. In addition, we also want to capture how effectively are the requests being handled (What has been done, what is still in progress).

## Limitations

The gmail API has token limit per minute for each user and project. Since we do not have multiple users working on the same project, we will just use the token limit per user as to how many requests we can make. The user limit is **15,000 tokens / minute**

The three main objects that we will be accessing from the gmail API will be **messages**, **threads**, and **drafts**. Below list the number of tokens required per request:

- messages.list: 5 tokens
- messages.get: 5 tokens

- threads.list: 10 tokens
- threads.get: 10 tokens

- drafts.create: 10 tokens

We overcome this restriction by using a sleep timer which pauses the execution of the program by a minute before continuing on.

A thread typically consists of one or more related messages. Both threads and messages are searchable using query formats. The syntax of searching is displayed in this [table](https://support.google.com/mail/answer/7190).

## Queries

A series of API requests are made to accomplish the goal behind this piece of work.

### Query From the w2 email

Query: `in:sent has:attachment after:2025/01/30`

This query returns all sent files with an attachment after January 30, 2025. The assumption we make is that all sent messages with an attachment correspond to a reply to the W2 requests received.

With the API response of this query, we can extract the date, sender, receiver, subject, and attachment names. Upon further parsing, we can find out the name of the SSN and name of the worker from the naming of the attachment.

**Observation**: It turns out that there are a series of W2s which require fixing. Additoinal task: recreate the W2s and automate the sending process

---

### Query From related email

Query: `has:attachment from:<other>@email.com after:2025/01/30`

This query extracts all of the attachments and SSN sent from alicia's email.

<b>Incomplete: The python extractor is not extracting correctly</b>

---

### Query of Label Cannot-Locate

Query: `label:cannot-locate`

This query captures a summary of what was not found

---

### Query of Label Additional-Inquiry

Query: `label:additional-inquiry`

This query captures a summary of follow-up requests from the W2s that has been sent out.

## Additional Task

This section covers additional tasks which is a result of queries made above.

### Auto draft W2s that require resending

The corrected W2s needs to be resent to the temp. Autodraft all of the emails and send by hand just for quick review before sending.

## References

Usage limits breakdown: https://developers.google.com/gmail/api/reference/quota

Gmail API Pydoc: https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/index.html

Gmail API quick access guides: https://developers.google.com/gmail/api/guides
