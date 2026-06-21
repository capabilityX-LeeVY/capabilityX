"""
GPT Control Matcher
===================

Uses GPT to intelligently match controls when exact/fuzzy matching fails.
Analyzes current window controls and finds the best match for the target control.
"""

import json
import uiautomation as auto
from typing import Optional, List, Dict, Tuple
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

# Try to import GPT client
GPT_AVAILABLE = False
try:
    from agent.openai_config import get_client, DEPLOYMENT_NAME
    GPT_AVAILABLE = True
    LOGGER_DEBUG("GPT control matching is available")
except ImportError as e:
    LOGGER_DEBUG(f"GPT control matching unavailable: {e}")
except Exception as e:
    LOGGER_DEBUG(f"GPT control matching unavailable: {e}")


class GPTControlMatcher:
    """
    Uses GPT to intelligently match controls when traditional methods fail.
    """
    
    def __init__(self):
        """Initialize GPT control matcher."""
        self.client = None
        if GPT_AVAILABLE:
            try:
                self.client = get_client()
                LOGGER_INFO("GPT control matcher initialized")
            except Exception as e:
                LOGGER_ERROR(f"Failed to initialize GPT client: {e}")
                self.client = None
    
    def _get_window_controls(self, parent: Optional[auto.Control] = None, max_depth: int = 10) -> List[Dict]:
        """
        Get all controls in the current window with their properties.
        
        Args:
            parent: Parent control to search from (if None, uses root)
            max_depth: Maximum depth to search (default: 10)
            
        Returns:
            List of control dictionaries with name, type, and other properties
        """
        controls = []
        
        try:
            # If no parent provided, try to get the active window
            if parent is None:
                parent = auto.GetFocusedControl()
                if parent:
                    # Get the top-level window
                    while parent.GetParentControl():
                        parent_window = parent.GetParentControl()
                        if parent_window.ControlType == auto.ControlType.WindowControl:
                            parent = parent_window
                            break
                        parent = parent_window
            
            if not parent:
                LOGGER_WARNING("No parent control found for GPT matching")
                return []
            
            # Check if this is RegressShield's own window - exclude it from control search
            window_name = parent.Name if parent.Name else ""
            if "RegressShield" in window_name or "ChatRegressShieldGUI" in window_name:
                LOGGER_WARNING(f"⚠️ Skipping RegressShield's own window: '{window_name}'")
                LOGGER_WARNING("   This prevents matching controls in the tool's GUI instead of target application")
                return []
            
            # Get all descendants up to max_depth
            LOGGER_INFO(f"🔍 Collecting controls from window: '{parent.Name}'")
            LOGGER_INFO(f"   Window Type: {parent.ControlTypeName}")
            LOGGER_INFO(f"   Window ID: {parent.AutomationId if parent.AutomationId else 'N/A'}")
            LOGGER_INFO(f"   Search Depth: {max_depth} levels")
            LOGGER_DEBUG(f"Collecting controls from: {parent.Name} (Type: {parent.ControlTypeName})")
            
            def collect_controls(control, depth=0):
                if depth > max_depth:
                    return
                
                try:
                    # Add control info
                    control_info = {
                        "name": control.Name,
                        "type": control.ControlTypeName,
                        "automation_id": control.AutomationId,
                        "class_name": control.ClassName,
                        "depth": depth
                    }
                    
                    # Only add controls with names (more useful for matching)
                    if control.Name and control.Name.strip():
                        controls.append(control_info)
                        
                        # Also add stripped version if different (for better matching)
                        stripped_name = control.Name.strip()
                        if stripped_name != control.Name:
                            stripped_info = control_info.copy()
                            stripped_info["name"] = stripped_name
                            stripped_info["is_stripped"] = True
                            controls.append(stripped_info)
                    
                    # Recursively collect children
                    children = control.GetChildren()
                    for child in children:
                        collect_controls(child, depth + 1)
                        
                except Exception as e:
                    LOGGER_DEBUG(f"Error collecting control at depth {depth}: {e}")
            
            collect_controls(parent)
            LOGGER_INFO(f"Collected {len(controls)} controls for GPT analysis")
            
            # Print all collected control names for review
            if controls:
                LOGGER_INFO("📋 Collected control names:")
                for i, ctrl in enumerate(controls, 1):
                    name = ctrl['name']
                    # Check if this is a stripped version
                    is_stripped = ctrl.get('is_stripped', False)
                    # Mark controls with leading/trailing spaces
                    has_spaces = name != name.strip()
                    
                    name_display = repr(name) if has_spaces else name
                    marker = " [stripped variant]" if is_stripped else ""
                    marker += " ⚠️ [has spaces]" if has_spaces and not is_stripped else ""
                    
                    LOGGER_INFO(f"  [{i}] Name: {name_display} | Type: {ctrl['type']} | ID: {ctrl.get('automation_id', 'N/A')}{marker}")
            else:
                LOGGER_WARNING("No controls collected from window")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to collect window controls: {e}")
        
        return controls
    
    def _build_gpt_prompt(self, target_control: str, available_controls: List[Dict]) -> str:
        """
        Build GPT prompt for control matching.
        
        Args:
            target_control: Name of the control we're looking for
            available_controls: List of controls currently available
            
        Returns:
            Formatted prompt string
        """
        controls_text = "\n".join([
            f"{i+1}. Name: '{ctrl['name']}' | Type: {ctrl['type']} | ID: {ctrl.get('automation_id', 'N/A')}"
            for i, ctrl in enumerate(available_controls)
        ])
        
        prompt = f"""You are a UI control matching expert. I'm trying to locate a control but the exact name doesn't match.

TARGET CONTROL (what I'm looking for):
"{target_control}"

AVAILABLE CONTROLS (currently visible in the window):
{controls_text}

TASK:
1. Analyze the target control name and understand what UI element it represents
2. Look through the available controls and find the BEST MATCH
3. The match might have slightly different text (e.g., "2 of 8" vs "2 of 6", different states like "selected" vs "collapsed")
4. Consider the control type and context

IMPORTANT:
- If the target is a Tree item with "X of Y", match controls with same base name and level but different "X of Y" values
- Ignore state differences (selected, collapsed, expanded, etc.) when matching
- Focus on the core control name and type

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "match_found": true/false,
    "matched_control_name": "exact name from the available controls list" or null,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this is the best match"
}}

Only return the JSON, no other text.
"""
        return prompt
    
    def find_best_match(self, target_control: str, parent: Optional[auto.Control] = None) -> Optional[Tuple[str, float]]:
        """
        Use GPT to find the best matching control.
        
        Args:
            target_control: Name of the control to find
            parent: Parent control to search within
            
        Returns:
            Tuple of (matched_control_name, confidence) or None if no match
        """
        if not self.client:
            LOGGER_WARNING("GPT client not available for control matching")
            return None
        
        try:
            LOGGER_INFO("🤖 Using GPT to find best control match...")
            
            # Get all available controls
            available_controls = self._get_window_controls(parent)
            
            if not available_controls:
                LOGGER_WARNING("No controls found for GPT analysis")
                return None
            
            # Build prompt
            prompt = self._build_gpt_prompt(target_control, available_controls)
            
            LOGGER_INFO("🎯 Sending analysis request to GPT...")
            LOGGER_DEBUG(f"Target control: '{target_control}'")
            
            # Call GPT
            LOGGER_DEBUG("Sending request to GPT...")
            response = self.client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UI control matching expert. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            if not response_text:
                LOGGER_WARNING("GPT returned empty response")
                return None
            
            response_text = response_text.strip()
            LOGGER_DEBUG(f"GPT response: {response_text}")
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Log GPT analysis result
            LOGGER_INFO("📊 GPT Analysis Result:")
            LOGGER_INFO(f"  Match Found: {result.get('match_found', False)}")
            LOGGER_INFO(f"  Matched Control: {result.get('matched_control_name', 'N/A')}")
            LOGGER_INFO(f"  Confidence: {result.get('confidence', 0.0):.2f}")
            LOGGER_INFO(f"  Reasoning: {result.get('reasoning', 'N/A')}")
            
            if result.get("match_found") and result.get("matched_control_name"):
                confidence = result.get("confidence", 0.0)
                matched_name = result["matched_control_name"]
                reasoning = result.get("reasoning", "No reasoning provided")
                
                LOGGER_INFO(f"✅ GPT found match: '{matched_name}' (confidence: {confidence:.2f})")
                LOGGER_INFO(f"💡 Reasoning: {reasoning}")
                
                return (matched_name, confidence)
            else:
                LOGGER_INFO("❌ GPT did not find a suitable match")
                if not result.get("match_found"):
                    LOGGER_INFO("💡 GPT could not find a matching control in the available list")
                return None
                
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"Failed to parse GPT response as JSON: {e}")
            LOGGER_ERROR(f"Response text: {response_text}")
            return None
        except Exception as e:
            LOGGER_ERROR(f"GPT control matching failed: {e}")
            return None


# Global instance
_gpt_matcher = None

def get_gpt_matcher() -> Optional[GPTControlMatcher]:
    """Get or create global GPT matcher instance."""
    global _gpt_matcher
    if _gpt_matcher is None and GPT_AVAILABLE:
        _gpt_matcher = GPTControlMatcher()
    return _gpt_matcher
