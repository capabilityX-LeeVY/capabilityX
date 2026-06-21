import requests
import json
from common.utils.featureToggle import FeatureToggle
from config.paths import FEATURE_TOGGLE_CONFIG_PATH 
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

BEAR_TOKEN = "NWE0ZjBhZjEtNDUxZS00ZDNkLThhOGItMjcwNjUwMjFlNWZkMDI2NTY0MmQtY2Nl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"

def sendMessageToTeams(message,roomId ="c0af0ac0-772f-11ef-9431-6382b932281b"):
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    if FeatureToggle.isEnabled("messageBot") == False:
        return None
        
    if roomId is None:
        return None
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {BEAR_TOKEN}'''
            }
    data = {"roomId": roomId, "text": "", "markdown": "%s" % (message)}
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
        if req.status_code == 200:
            LOGGER_INFO(f"Notify message bot succeeded. with room ID: ({roomId})")
            # Return message ID for thread support
            response_data = req.json()
            return response_data.get('id')
        else:
            LOGGER_ERROR(f"Notify message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
            return None
    except Exception as e:
        LOGGER_ERROR(f"Notify message bot failed: {e}")
        return None

def sendMessageToPerson(emailaddress, message):
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    if FeatureToggle.isEnabled("messageBot") == False:
        return None
    
    if emailaddress is None:
        return
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {BEAR_TOKEN}'''
            }
    data = {"toPersonEmail": emailaddress, "text": "", "markdown": "%s" % (message)}
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
        if req.status_code == 200:
            LOGGER_INFO(f"Notify message bot succeeded. with person email: ({emailaddress})")
        else:
            LOGGER_ERROR(f"Notify message bot failed, status code : {req.status_code} - {req.text} with person email: {emailaddress}")
    except Exception as e:
        LOGGER_ERROR(f"Notify message bot failed: {e}")

def sendMessageInThread(message, roomId, parentId):
    """
    Send a message as a reply in a thread
    
    Args:
        message: The message content (markdown format)
        roomId: Room ID where the thread exists
        parentId: Parent message ID to reply to
        
    Returns:
        str: Message ID if successful, None otherwise
    """
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    if FeatureToggle.isEnabled("messageBot") == False:
        return None
    
    if roomId is None or parentId is None:
        LOGGER_ERROR("roomId and parentId are required for thread messages")
        return None
        
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': f'''Bearer {BEAR_TOKEN}'''
    }
    
    data = {
        "roomId": roomId,
        "parentId": parentId,
        "text": "",
        "markdown": message
    }
    
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers=headers)
        if req.status_code == 200:
            LOGGER_INFO(f"Thread message sent successfully to room ID: ({roomId}), parent: ({parentId})")
            response_data = req.json()
            return response_data.get('id')
        else:
            LOGGER_ERROR(f"Thread message failed, status code: {req.status_code} - {req.text}")
            return None
    except Exception as e:
        LOGGER_ERROR(f"Thread message failed: {e}")
        return None

def sendCardToTeams(card_content, roomId="c0af0ac0-772f-11ef-9431-6382b932281b", parentId=None, text=None):
    """
    Send Adaptive Card to Webex Teams
    
    Args:
        card_content: The Adaptive Card content (dict)
        roomId: Room ID to send the card to
        parentId: Optional parent message ID for thread support (not applicable for cards with attachments)
    """
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    if FeatureToggle.isEnabled("messageBot") == False:
        return None
        
    if roomId is None:
        return None
        
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': f'''Bearer {BEAR_TOKEN}'''
    }
    
    fallback_text = text if text else "Test Execution Report - please update your client to see the full card"
    
    # Construct the payload for Adaptive Card with fallback text
    data = {
        "roomId": roomId,
        "text": fallback_text,
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card_content
        }]
    }
    
    # Note: parentId cannot be used with attachments due to Webex API limitation
    # Cards with attachments cannot be sent as thread replies
    
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers=headers)
        if req.status_code == 200:
            LOGGER_INFO(f"Notify card message bot succeeded. with room ID: ({roomId})")
            return True
        else:
            LOGGER_ERROR(f"Notify card message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
            return False
    except Exception as e:
        LOGGER_ERROR(f"Notify card message bot failed: {e}")
        return False

def sendCardToPerson(emailaddress, card_content):
    """
    Send Adaptive Card to a specific person
    
    Args:
        emailaddress: Email address of the recipient
        card_content: The Adaptive Card content (dict)
    """
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    if FeatureToggle.isEnabled("messageBot") == False:
        return None
    
    if emailaddress is None:
        return
        
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': f'''Bearer {BEAR_TOKEN}'''
    }
    
    # Construct the payload for Adaptive Card with fallback text
    data = {
        "toPersonEmail": emailaddress,
        "text": "Test Execution Report - please update your client to see the full card",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card_content
        }]
    }
    
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers=headers)
        if req.status_code == 200:
            LOGGER_INFO(f"Notify card message bot succeeded. with person email: ({emailaddress})")
            return True
        else:
            LOGGER_ERROR(f"Notify card message bot failed, status code : {req.status_code} - {req.text} with person email: {emailaddress}")
            return False
    except Exception as e:
        LOGGER_ERROR(f"Notify card message bot failed: {e}")
        return False


if __name__ == "__main__":
    # Test regular message
    #sendMessageToPerson("jianphu2@cisco.com","nice to meet you")
    #sendMessageToTeams("Hi <@personEmail:jianphu2@cisco.com|Bobby>, I am a bot to notification messages about RegressShield")
    
    # Test Adaptive Card
    sample_card = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "style": "good",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "📑 Test Execution Report",
                        "size": "large",
                        "weight": "bolder"
                    },
                    {
                        "type": "TextBlock",
                        "text": "All outputs are ready for review",
                        "size": "medium",
                        "spacing": "small"
                    }
                ]
            },
            {
                "type": "FactSet",
                "facts": [
                    {
                        "title": "OS:",
                        "value": "Windows 11 24H2"
                    },
                    {
                        "title": "Computer:",
                        "value": "Dell-XPS15"
                    },
                    {
                        "title": "Result:",
                        "value": "PASSED"
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "View Report",
                "url": "https://example.com"
            }
        ]
    }
    
    # Uncomment to test card
    #sendCardToTeams(sample_card)