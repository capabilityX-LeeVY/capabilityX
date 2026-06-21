import argparse
import json
import os
import requests

BEAR_TOKEN = "NWE0ZjBhZjEtNDUxZS00ZDNkLThhOGItMjcwNjUwMjFlNWZkMDI2NTY0MmQtY2Nl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
# ROOM_ID = "7d6b04f0-ff44-11f0-a678-4559f92c6a95"
ROOM_ID = "25429490-2e39-11f1-a9e8-75e20e753063"


def parse_args():
    parser = argparse.ArgumentParser(description="Send an Adaptive Card to Webex")
    parser.add_argument("--card-file", required=True, help="Path to Adaptive Card JSON file")
    parser.add_argument("--room-id", default=ROOM_ID, help="Webex room ID")
    parser.add_argument("--token", default=BEAR_TOKEN, help="Webex bot token")
    parser.add_argument("--fallback-text", default="Test Running Status", help="Fallback text")
    return parser.parse_args()


def send_adaptive_card(card, room_id, token, fallback_text):
    sparkapi = "https://webexapis.com/v1/messages"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "roomId": room_id,
        "text": fallback_text,
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }
    response = requests.post(sparkapi, data=json.dumps(payload), headers=headers, timeout=30)
    if response.status_code == 200:
        print(f"Adaptive card sent to room {room_id}.")
        return 0
    print(f"Send failed: {response.status_code} - {response.text}")
    return 1


def main():
    args = parse_args()
    if not os.path.isfile(args.card_file):
        raise FileNotFoundError(args.card_file)
    with open(args.card_file, "r", encoding="utf-8") as handle:
        card = json.load(handle)
    raise_on_error = send_adaptive_card(
        card=card,
        room_id=args.room_id,
        token=args.token,
        fallback_text=args.fallback_text,
    )
    raise SystemExit(raise_on_error)


if __name__ == "__main__":
    main()
