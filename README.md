<img width="1742" height="691" alt="image" src="https://github.com/user-attachments/assets/7d158ba5-35c5-41ac-a6d9-abb6694a28fa" /><img width="619" height="278" alt="image" src="https://github.com/user-attachments/assets/5ffb175f-36ba-4feb-b9c9-94a5e59d5f88" /># email-sorter
This program will attempt to sort emails into 3 categories: Important, Spam and misc. (It will create a misc label if it doesn't exist). It will move the message from inbox to the appropriate label. An existing limitation is that this will remove all users' labels, and by extension all automated email goes to spam.

An AI agent that watches your Gmail inbox and sorts new emails into Important, Spam and misc using GPT-4o-mini. It reads the sender, subject, body and supported attachments (text, JSON and images) to decide. Requires an OpenAI API key.

To use:
1. Go to console.cloud.google.com and create a project. <img width="774" height="781" alt="image" src="https://github.com/user-attachments/assets/a4554b88-6e92-4620-b52a-52f1dc8046d2" />
2. Enable the gmail API in APIs & Services #
<img width="619" height="278" alt="image" src="https://github.com/user-attachments/assets/4f546db3-e77f-400e-aacd-b2dfd4aec4aa" /> <img width="1742" height="691" alt="image" src="https://github.com/user-attachments/assets/aea93f7b-d425-49e9-98f6-f9d2e32ee39d" /> <img width="1190" height="673" alt="image" src="https://github.com/user-attachments/assets/50cf22e9-87dd-493d-959d-50e0f04c6380" /> <img width="1126" height="788" alt="image" src="https://github.com/user-attachments/assets/d6e05b0e-f7a4-4e86-bdc4-914733bcecf7" />

3. Go to the OAuth consent screen and fill in the app name, user type, and the required emails.
5. Add the email you will be using the sorter on.
6. Go to Credentials and click credentials. Choose OAuth Client ID. Choose Desktop app and create.
7. Click download json and save the file as credentials.json.
8. Create a .env file, and paste an API key.
9. Do pip install -r requirements.txt (you may want to make a venv for this)
10. To run: just run python/python3 agent.py in the command line. You may be asked to login if you are running the program for the first time.
11. To try it without changing your inbox, run python/python3 agent.py --dry-run instead (see below).

There is a dry run mode, which can be run by adding the --dry-run flag. It will not move the email but show where the email would be sorted to by printing Would move ... -> ... 

This program will attempt to sort emails into 3 categories: Important, Spam and misc. (It will create a misc label if it doesn't exist). It will move the message from the inbox to the appropriate label. Any labels you have already added to an email are kept. Routine automated emails such as receipts and notifications go to misc, while scams, phishing and bulk marketing go to spam.

