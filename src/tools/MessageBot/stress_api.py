import requests

def send_message_to_webex(token, room_id, markdown_message):
    """
    Sends a message to a Webex bot space.

    Parameters:
    - token: str, authorization token for the Webex bot
    - room_id: str, ID of the Webex room
    - markdown_message: str, the message to send in markdown format

    Returns:
    - str: Success or error message
    """
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "roomId": room_id,
        "markdown": markdown_message
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return "Message sent successfully!"
        else:
            return f"Failed to send message. Status code: {response.status_code}\nResponse: {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"





# Your bot token and room details
bot_token = "YTk3MGM2NzEtODAzNi00MGVlLTg2NzItYjliMGY0MzY5ZDE4NDYyMzY0YWItZWY2_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vNGQzYzI0MzAtOTJmMy0xMWVmLTkzNzYtNDNmMGYwMjA1OTBm"
#markdown_message = "<@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com audio=off video=on send_reactions=on with 10 ucf_api duration 3"

markdown_message = "<@personEmail:awebexbot@webex.bot> join fullmode18@appletestci.webex.com audio=off video=on send_reactions=on send_chat=on with 10 ucf_api duration 3"

# Call the function
print('=============================================================')
result = send_message_to_webex(bot_token, room_id, markdown_message)
print(result)
print('=============================================================')

