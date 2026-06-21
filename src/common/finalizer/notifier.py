from tools.MessageBot import BotMessage
from config.global_settings import settings
from typing import Optional
from rs_sdk.utils.control_db import ControlDB

def notify_messageBot(report_url: str, owner: Optional[str]=None, execution_result: Optional[str]=None, jira_open_count: Optional[int]=None):
    """
    Send a simple markdown notification message (original method)
    
    Args:
        report_url: URL to the detailed report
        owner: Optional owner information (deprecated, use jira_open_count instead)
        execution_result: Optional execution result
        jira_open_count: Optional count of open Jira issues
    """
    # Build simple list format message
    lines = [
        f"📑 **All outputs are ready, view them** [here]({report_url})",
        f"- **OS:** {settings.device_os}",
        f"- **Computer:** {settings.device_name}",
        f"- **App Version:** {settings.appVersion}",
        f"- **Total Visited Controls:** {len(ControlDB().fetch_control_history())}",
    ]
    
    if settings.workflow:
        lines.append(f"- **Work Flow:** {settings.workflow}")
    if settings.test_suite:
        lines.append(f"- **Test Suite:** {settings.test_suite}")
    if execution_result:
        lines.append(f"- **Execution Result:** {execution_result}")
    if jira_open_count is not None:
        jira_url = "https://jira-eng-gpk2.cisco.com/jira/issues/?filter=97032&jql=(labels%20in%20(WebexRegressSheild)%20or%20%22Epic%20Link%22%20%3D%20SPARK-559755)%20and%20status%20in%20(%22In%20Progress%22%2C%20New%2C%20Backlog%2C%20Ready)"
        lines.append(f"- **Jira:** [{jira_open_count} Open Issues]({jira_url})")
    elif owner:  # Fallback to owner if jira_open_count not provided
        lines.append(f"- **Owner:** {owner}")
    
    bot_message = "\n".join(lines)
    BotMessage.sendMessageToTeams(bot_message)

def notify_messageBot_card(report_url: str, execution_result: Optional[str]=None, jira_open_count: Optional[int]=None, 
                          llm_failures: Optional[int]=None, nav_failures: Optional[int]=None, focus_ring_failures: Optional[int]=None,
                          screen_reader_failures: Optional[int]=None,
                          roomId="c0af0ac0-772f-11ef-9431-6382b932281b"):
    """
    Send a beautiful Adaptive Card notification
    
    Args:
        report_url: URL to the detailed report
        execution_result: Optional execution result
        jira_open_count: Optional count of open Jira issues
        llm_failures: Optional count of LLM failures
        nav_failures: Optional count of navigation failures
        focus_ring_failures: Optional count of focus ring failures
        screen_reader_failures: Optional count of screen reader failures
    """
    from common.handler.settingsHandler import DynamicConfig
    from config.paths import SETTINGS_PATH
    local_settings = DynamicConfig(SETTINGS_PATH)
    # Determine status color and emoji based on execution result
    status_color = "good"
    status_emoji = "✅"
    if execution_result:
        if "FAIL" in execution_result.upper():
            status_color = "attention"
            status_emoji = "❌"
        elif "PASS" in execution_result.upper():
            status_color = "good"
            status_emoji = "✅"
        else:
            status_color = "default"
            status_emoji = "ℹ️"
    
    # Create Adaptive Card
    card_content = {
        "type": "AdaptiveCard",
        "version": "1.2",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"🚀 **AI Test Execution Report** {status_emoji}",
                                        "size": "large",
                                        "weight": "bolder",
                                        "color": "accent",
                                        "spacing": "none",
                                        "horizontalAlignment": "Center"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": "✨ Automated analysis completed",
                                        "size": "small",
                                        "color": "accent",
                                        "spacing": "none",
                                        "horizontalAlignment": "Center"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "type": "Container",
                "style": "default",
                "spacing": "medium",
                "items": [
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "🖥️ OS:",
                                "value": f"{settings.device_os}"
                            },
                            {
                                "title": "💻 Computer:",
                                "value": f"{settings.device_name}"
                            },
                            {
                                "title": "📦 App Version:",
                                "value": f"{local_settings.get('appVersion')}"
                            },
                            {
                                "title": "👣 Traversed #:",
                                "value": f"{len(ControlDB().fetch_control_history())}"
                            }
                        ]
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "View Report",
                "url": report_url,
                "style": "positive"
            },
            {
                "type": "Action.OpenUrl",
                "title": "Go to WRS Platform",
                "url": "https://wrs.qa.webex.com/",
                "style": "positive"
            }
        ]
    }
    
    # Add Jira button if jira_open_count is provided
    # if jira_open_count is not None:
    #     jira_url = "https://jira-eng-gpk2.cisco.com/jira/issues/?filter=97032&jql=(labels%20in%20(WebexRegressSheild)%20or%20%22Epic%20Link%22%20%3D%20SPARK-559755)%20and%20status%20in%20(%22In%20Progress%22%2C%20New%2C%20Backlog%2C%20Ready)"
    #     # Insert Jira button in the middle position
    #     card_content["actions"].insert(1, {
    #         "type": "Action.OpenUrl",
    #         "title": "View Issues",
    #         "url": jira_url,
    #         "style": "positive"
    #     })
    
    # Add optional facts
    additional_facts = []
    if local_settings.installOptions and local_settings.installOptions.qtversion:
        additional_facts.append({
            "title": "📟 Qt Version:",
            "value": f"{local_settings.installOptions.qtversion}"
        })
        
    if settings.workflow:
        additional_facts.append({
            "title": "⚡ Work Flow:",
            "value": f"{settings.workflow}"
        })
    
    if settings.test_suite:
        additional_facts.append({
            "title": "📋 Test Suite:",
            "value": f"{settings.test_suite}"
        })
    if settings.test_batch:
        additional_facts.append({
            "title": "📦 Test Batch:",
            "value": f"{settings.test_batch}"
        })
    if settings.test_case:
        additional_facts.append({
            "title": "🧪 Test Case:",
            "value": f"{settings.test_case}"
        })
    
    # Add Jira information if provided
    # if jira_open_count is not None:
    #     additional_facts.append({
    #         "title": "🔧 Jira:",
    #         "value": f"{jira_open_count} Open Issues"
    #     })
    
    # Add failure statistics if provided
    if llm_failures is not None or nav_failures is not None or focus_ring_failures is not None or screen_reader_failures is not None:
        failure_details = []
        if llm_failures is not None:
            failure_details.append(f"AI: {llm_failures}")
        if nav_failures is not None:
            failure_details.append(f"Nav: {nav_failures}")
        if focus_ring_failures is not None:
            failure_details.append(f"FR: {focus_ring_failures}")
        if screen_reader_failures is not None:
            failure_details.append(f"SR: {screen_reader_failures}")
        
        additional_facts.append({
            "title": "📊 Failures:",
            "value": " | ".join(failure_details)
        })
    
    # Add additional facts to the card
    card_content["body"][1]["items"][0]["facts"].extend(additional_facts)
    
    # Add execution result as a separate highlighted container if present
    if execution_result:
        result_color = "good" if "PASS" in execution_result.upper() else "attention" if "FAIL" in execution_result.upper() else "warning"
        result_icon = "✅" if "PASS" in execution_result.upper() else "❌" if "FAIL" in execution_result.upper() else "ℹ️"
        
        # Build detailed failure breakdown if any failures exist
        failure_breakdown_items = []
        if "FAIL" in execution_result.upper() and (llm_failures or nav_failures or focus_ring_failures or screen_reader_failures):
            failure_breakdown = []
            if llm_failures and llm_failures > 0:
                failure_breakdown.append(f"🤖 AI Check: {llm_failures}")
            if nav_failures and nav_failures > 0:
                failure_breakdown.append(f"🎯 Navigation: {nav_failures}")
            if focus_ring_failures and focus_ring_failures > 0:
                failure_breakdown.append(f"🔍 Focus Ring: {focus_ring_failures}")
            if screen_reader_failures and screen_reader_failures > 0:
                failure_breakdown.append(f"🔊 Screen Reader: {screen_reader_failures}")
            
            if failure_breakdown:
                failure_breakdown_items.append({
                    "type": "TextBlock",
                    "text": " • ".join(failure_breakdown),
                    "size": "small",
                    "color": "attention",
                    "spacing": "small",
                    "wrap": True
                })
        
        result_container_items = [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": result_icon,
                                "size": "medium",
                                "spacing": "none"
                            }
                        ]
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"**Execution Result:** {execution_result}",
                                "size": "medium",
                                "weight": "bolder",
                                "spacing": "none"
                            }
                        ]
                    }
                ]
            }
        ]
        
        # Add failure breakdown if exists
        result_container_items.extend(failure_breakdown_items)
        
        result_container = {
            "type": "Container",
            "style": result_color,
            "spacing": "medium",
            "items": result_container_items
        }
        card_content["body"].append(result_container)
    
    context_texts = []
    if settings.device_name:
        context_texts.append(f"💻 Computer: {settings.device_name}")
    if settings.workflow:
        context_texts.append(f"⚡ Work Flow: {settings.workflow}")
    if settings.test_suite:
        context_texts.append(f"📋 Test Suite: {settings.test_suite}")
    message_text = " | ".join(context_texts) if context_texts else None
    if message_text:
        BotMessage.sendCardToTeams(card_content, roomId, text=message_text)
    else:
        BotMessage.sendCardToTeams(card_content, roomId)