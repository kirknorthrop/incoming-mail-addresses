#!/usr/bin/python

import argparse
import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

from clint.textui import progress

# Parse the command-line arguments (e.g. --noauth_local_webserver)
parser = argparse.ArgumentParser(parents=[argparser])
flags = parser.parse_args()

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes
# for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
  credentials = run_flow(flow, STORAGE, flags, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)

# Retrieve a page of emails
messages = gmail_service.users().messages().list(userId='me').execute()

email_addresses = {}

# Collect and print emails
while messages['messages']:
    for message in progress.bar(messages['messages']):
        message_data = gmail_service.users().messages().get(id=message['id'], userId='me', format='metadata').execute()
        for header in message_data['payload']['headers']:
            if header['name'] == 'Delivered-To':
                email_addresses[header['value']] = email_addresses[header['value']] + 1 if email_addresses.get(header['value'], False) else 1
                continue
    next_page_token = messages.get('nextPageToken')
    if next_page_token:
        messages = gmail_service.users().messages().list(userId='me', pageToken=next_page_token).execute()

print email_addresses
