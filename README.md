# email-sorter
This program will attempt to sort emails into 3 categories: Important, Spam and misc. (It will create a misc label if it doesn't exist). It will move the message from inbox to the appropriate label. An existing limitation is that this will remove all users' labels, and by extension all automated email goes to spam.

An AI agent that watches your Gmail inbox and sorts new emails into Important, Spam and misc using GPT-4o-mini. It reads the sender, subject, body and supported attachments (text, JSON and images) to decide. Requires an OpenAI API key.

Video to setup: https://youtu.be/nQgCgQTdooM

To use:
1. Go to console.cloud.google.com and create a project. 
2. Enable the gmail API in APIs & Services 
3. Go to the OAuth consent screen and fill in the app name, user type, and the required emails.
5. Add the email you will be using the sorter on.
6. Go to Credentials and click credentials. Choose OAuth Client ID. Choose Desktop app and create.
7. Click download json and save the file as credentials.json.
8. Create a .env file, and onto it type: OPENAI_API_KEY = <key>
9. Do pip install -r requirements.txt (you may want to make a venv for this)
10. To run: just run python/python3 agent.py in the command line. You may be asked to login if you are running the program for the first time.
11. To try it without changing your inbox, run python/python3 agent.py --dry-run instead (see below).

There is a dry run mode, which can be run by adding the --dry-run flag. It will not move the email but show where the email would be sorted to by printing Would move ... -> ... 

This program will attempt to sort emails into 3 categories: Important, Spam and misc. (It will create a misc label if it doesn't exist). It will move the message from the inbox to the appropriate label. Any labels you have already added to an email are kept. Routine automated emails such as receipts and notifications go to misc, while scams, phishing and bulk marketing go to spam.

