import argparse
import base64
import html
import re
import time
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
import create_services

load_dotenv()

class DecideAction(BaseModel):
    response: Literal["important","spam","misc"]


class auto_sorting_agent:
    def __init__(self,dry_run=False):
        self.__dry_run = dry_run #Only print decisions, don't change anything in the inbox
        self.__service = create_services.create_service("gmail","v1")
        self.__results = []
        self.__misc_label_id = ""
        self.__failed_ids = set() #Messages that errored, skipped so we don't keep paying for them
        self.__done_ids = set() #Messages already decided on. In dry run they stay in the inbox, so without this they'd be sent to the AI every loop
        lookback = 24*60*60 if dry_run else 120 #Dry run looks at the last day so there's something to show straight away
        self.__last_check = int(time.time()) - lookback
        self.__protected_labels = ["SENT", "DRAFTS", "UNREAD", "TRASH","UNREAD"] #These labels can't be removed. (set by google, I added unread on there so it remains unread for the user.
        self.__client = OpenAI()
        self.run_agent()

        
    def extract_body_text(self,message):
        headers = {header["name"].lower(): header["value"] for header in message["payload"].get("headers",[])}
        body = self.extract_body_logic_recurse({"text":"",
                                                "html":"",
                                                "attachment_ID": []},message["payload"])
        if not body["text"].strip() and body["html"]: #HTML only email, use the HTML with tags stripped
            body["text"] = self.html_to_text(body["html"])
        body["from"] = headers.get("from","")
        body["subject"] = headers.get("subject","")
        return body

    def html_to_text(self,html_text):
        html_text = re.sub(r"(?is)<(style|script|head)\b.*?</\1>", " ", html_text) #Remove css/js, not readable text
        html_text = re.sub(r"(?s)<[^>]+>", " ", html_text) #Remove the remaining tags
        return re.sub(r"\s+", " ", html.unescape(html_text)).strip() #Turn &amp; etc into characters and tidy whitespace

    def extract_body_logic_recurse(self,body,mime_message):
        mime_body = mime_message.get("body",{})
        message_type = mime_message.get("mimeType","")
        if "attachmentId" in mime_body: #Check for big attachments sent in a mime message
            body["attachment_ID"].append({
            "id": mime_body["attachmentId"],
            "filename": mime_message.get("filename", ""),
            "file_type": message_type
        }) 

        elif "data" in mime_body: #Not big message nor container
            data = mime_body.get("data")
            if message_type == "text/plain": #Text, just decode
                body["text"] += base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif message_type == "text/html": #Keep HTML aside, only used if there's no plain text version
                body["html"] += base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            else: #Inline images and other data, store the string
                body["attachment_ID"].append({
                "data": data,
                "filename": mime_message.get("filename", ""),
                "file_type": message_type
            })

        if "parts" in mime_message: #recurse through tree
            for part in mime_message["parts"]:
                self.extract_body_logic_recurse(body,part)
        return body

    def get_attachment_from_id(self,attachment_dict,message_ID):
        if "data" in attachment_dict: #Inline data, already in the message so no need to fetch
            data = base64.urlsafe_b64decode(attachment_dict["data"])
        else: #Big attachment, fetch it by ID
            attachment = self.__service.users().messages().attachments().get(userId="me",messageId=message_ID,id=attachment_dict["id"]).execute()
            data = base64.urlsafe_b64decode(attachment.get("data", ""))
        file_type = attachment_dict["file_type"]
        if file_type == "text/plain": #Figure out what to do with attachment
            return {
                "type": "text",
                "text": data.decode("utf-8", errors="replace")
            }
        elif file_type.startswith("image/"):
            return {
                    "type": "image_url", 
                    "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
            }}
        elif attachment_dict.get("filename", "").endswith(".json"):
            return {
                    "type": "text",
                    "text": f"--- Attached JSON File ({attachment_dict.get('filename', '')}) ---\n{data.decode('utf-8')}"
                }
        else:
            return {
                "type": "text",
                "text": "UNSUPPORTED FORMAT"
            }

    def get_files_for_AI(self,body,message_ID):
        files = [{"type": "text",
                  "text": f"From: {body['from']}\nSubject: {body['subject']}"}] #Sender and subject first, usually the best clues
        if body.get("text",""):
            files.append({"type": "text",
                          "text": body["text"]})
        for attachment_dict in body["attachment_ID"]:
            files.append(self.get_attachment_from_id(attachment_dict, message_ID))
        return files

    def decide_action(self,inputs):
        completion = self.__client.beta.chat.completions.parse(
            model = "gpt-4o-mini",
            messages = [{"role": "system", "content": "Your goal is determine where the email should be moved to. Respond with spam if you believe you got an automated message,"
            " important if the message is important and misc for anything else."},
                        {"role": "user", "content": inputs}],
            response_format = DecideAction, #Restrict its output so it can only respond with important/spam/misc
            temperature=0 #its sorting so 0 makes it more optimised
        )
        decision = completion.choices[0].message.parsed.response
        return decision

    def move_message(self,message_id,decision):
        labels = {
            "important" : "IMPORTANT",
            "spam": "SPAM",
            "misc": self.__misc_label_id
        }   
        new_label = labels[decision]
        message_labels_to_remove = self.__service.users().messages().get(userId="me",id=message_id).execute().get("labelIds",[])
        message_labels_to_remove = [label for label in message_labels_to_remove if label not in self.__protected_labels and label != new_label]
        change_labels = {
            "removeLabelIds": message_labels_to_remove,
            "addLabelIds": [new_label]
        }
        self.__service.users().messages().modify(userId="me",id=message_id,body=change_labels).execute()


    def check_labels(self): #Check if we made a misc label, if not make one.
        labels = self.__service.users().labels().list(userId="me").execute().get("labels",[])
        for label in labels:
            if label["name"] == "misc":
                self.__misc_label_id = label["id"]
                return
        label = {
            "name": "misc",
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        
        misc_label = self.__service.users().labels().create(userId="me",body=label).execute()
        self.__misc_label_id = misc_label["id"]
        return

    def run_agent(self):
        if self.__dry_run:
            print("Dry run: emails will not be moved and no labels will be created")
        else:
            self.check_labels()
        while True:
            try:
                check_start = int(time.time())
                query = f"is:inbox after:{self.__last_check}" #Everything since the last check, so nothing is missed however long a pass takes
                self.__results = self.__service.users().messages().list(userId="me",q=query).execute()
                self.__last_check = check_start - 60 #Only move forward once listing worked. 60s overlap in case Gmail is slow to index new emails
                #self.__results = self.__service.users().messages().list(userId="me",q="is:unread").execute()
                if self.__results:
                    message_dicts = self.__results.get("messages",[])
                    print(len(message_dicts))
                    for message_dict in message_dicts:
                        if message_dict["id"] in self.__failed_ids or message_dict["id"] in self.__done_ids: #Already handled, don't pay again
                            continue
                        try: #Handle each email separately so one failure doesn't skip the rest
                            message = self.__service.users().messages().get(
                                userId="me",
                                id=message_dict["id"],
                                format="full"
                            ).execute()
                            content = self.extract_body_text(message)
                            files_for_ai = self.get_files_for_AI(content, message_dict["id"])
                            decision = self.decide_action(files_for_ai)
                            if self.__dry_run:
                                print(f"Would move \"{content['subject']}\" ({content['from']}) -> {decision}")
                            else:
                                self.move_message(message_dict["id"],decision)
                                print(f"Moved \"{content['subject']}\" ({content['from']}) -> {decision}")
                            self.__done_ids.add(message_dict["id"])
                        except Exception as e:
                            self.__failed_ids.add(message_dict["id"])
                            print("Failed on message", message_dict["id"], ":", e)
            except Exception as e: #Listing messages failed, try again next loop
                print(e)
            print("No emails currently")
            time.sleep(100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sort new Gmail inbox emails into important, spam and misc using an AI model.")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen to each email without moving anything")
    args = parser.parse_args()
    agent = auto_sorting_agent(dry_run=args.dry_run)



