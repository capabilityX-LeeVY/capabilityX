import requests
import os
import time
import argparse
import sys
import json

#WEBEX_TOKEN = os.getenv("WEBEX_TOKEN")
#ROOM_ID = os.getenv("ROOM_ID")  # or hardcode the room ID string
BEAR_TOKEN = "NWE0ZjBhZjEtNDUxZS00ZDNkLThhOGItMjcwNjUwMjFlNWZkMDI2NTY0MmQtY2Nl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
#ROOM_ID = "7d6b04f0-ff44-11f0-a678-4559f92c6a95"  # or hardcode the room ID string
ROOM_ID = "25429490-2e39-11f1-a9e8-75e20e753063"

def parse_args():
    parser = argparse.ArgumentParser(description="Pocess Run Test scripts Argument")
    parser.add_argument('-m', '--message', required=False, help="Message,e.g Hello!")
    parser.add_argument('-mf', '--message-file', required=False, default=None,
                        help="Path to a UTF-8 text file containing the message")
    parser.add_argument('-f', '--file', required=False, default=None,
                        help="File path to upload (optional)")
    args = parser.parse_args()

    return args

def sendMessageToTeams(message):

    #roomId = "7d6b04f0-ff44-11f0-a678-4559f92c6a95"
    roomId = ROOM_ID
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {BEAR_TOKEN}'''
            }
    data = {"roomId": roomId, "text": "", "markdown": "%s" % (message)}
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
        if req.status_code == 200:
            print(f"Notify message bot succeeded. with room ID: ({roomId})")
            # Return message ID for thread support
            response_data = req.json()
            return response_data.get('id')
        else:
            print(f"Notify message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
            return None
    except Exception as e:
        print(f"Notify message bot failed: {e}")
        return None

def sendFileToTeams(file_path, room_id=ROOM_ID):
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
        'Authorization': f'''Bearer {BEAR_TOKEN}'''
    }

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return None
    file_size = os.path.getsize(file_path)
    if file_size <= 0:
        print(f"File is empty: {file_path}")
        return None

    data = {
        "roomId": room_id,
        "text": "CiscoSpark logs archive"
    }

    try:
        with open(file_path, 'rb') as f:
            files = [
                (
                    'files',
                    (os.path.basename(file_path), f, 'application/x-7z-compressed')
                )
            ]
            req = requests.post(sparkapi, data=data, files=files, headers=headers, timeout=60)
        if req.status_code == 200:
            print(f"File upload succeeded. room ID: ({room_id})")
            message_id = req.json().get('id')
            try:
                os.remove(file_path)
                print(f"Deleted local file: {file_path}")
            except Exception as e:
                print(f"Failed to delete local file: {file_path} - {e}")
            return message_id
        else:
            print(f"File upload failed, status code : {req.status_code} - {req.text} with room ID: {room_id}")
            return None
    except Exception as e:
        print(f"File upload failed: {e}")
        return None
        
if __name__ == "__main__":
    
    args = parse_args()
    if args.message_file:
        with open(args.message_file, "r", encoding="utf-8", errors="replace") as handle:
            message = handle.read()
    else:
        message = args.message
    if not message:
        raise ValueError("Message is required via --message or --message-file")
    file_path = args.file

    sendMessageToTeams(message)
    if file_path:
        sendFileToTeams(file_path)