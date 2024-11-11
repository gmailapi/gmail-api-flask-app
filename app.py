from flask import Flask, redirect, url_for, session, request, render_template
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.oauth2.credentials
import os
import secrets

app = Flask(__name__)
secret_key = secrets.token_hex(16)
app.secret_key = secret_key  # Replace with your secret key

# Define the scopes and redirect URI for the Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/authorize')
def authorize():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    flow.redirect_uri = REDIRECT_URI
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    flow.redirect_uri = REDIRECT_URI
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    session['credentials'] = flow.credentials_to_dict()
    return redirect(url_for('index'))  # Redirect to home after successful auth

@app.route('/get_emails', methods=['POST'])
def get_emails():
    if 'credentials' not in session:
        return redirect('authorize')

    sender_email = request.form['sender_email']
    user_email = request.form['user_email']

    # Build the Gmail API client
    creds = google.oauth2.credentials.Credentials(**session['credentials'])
    service = build('gmail', 'v1', credentials=creds)

    # Query the Gmail API to fetch emails from the specific sender
    query = f'from:{sender_email}'
    results = service.users().messages().list(userId=user_email, q=query).execute()
    messages = results.get('messages', [])

    emails_content = []
    for message in messages:
        msg = service.users().messages().get(userId=user_email, id=message['id']).execute()
        email_content = msg['snippet']  # Get a snippet of the email
        emails_content.append(email_content)

    session['credentials'] = creds.to_json()  # Save updated credentials

    return render_template('emails.html', sender_email=sender_email, emails=emails_content)

if __name__ == '__main__':
    app.run(debug=True)
