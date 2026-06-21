"""
API Action Strategy

This module contains the ApiActionStrategy for API call actions.
"""

from typing import Dict, Any, Optional
import json
import os
import requests
import time
from pathlib import Path
from core.strategies.action_strategy import ActionStrategy
from core.managers.agent_node_manager import agent_node_manager
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING
from config.paths import API_CONFIG_PATH


class ApiActionStrategy(ActionStrategy):
    """API call action strategy with agent node support"""
    
    def __init__(self):
        self.api_config = self._load_api_config()
        self.node_manager = agent_node_manager
    
    def _load_api_config(self) -> Dict[str, Any]:
        """Load API configuration from JSON file"""
        try:
            # Use centralized path configuration
            with open(API_CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except Exception as e:
            LOGGER_ERROR(f"Failed to load API config: {e}")
            return {}
    
    def _resolve_template_variables(self, template: Any, parameters: Dict[str, Any]) -> Any:
        """Resolve template variables like {{variable}} in configuration"""
        if isinstance(template, str):
            # Replace template variables
            result = template
            for key, value in parameters.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        elif isinstance(template, dict):
            resolved = {}
            for k, v in template.items():
                resolved_value = self._resolve_template_variables(v, parameters)
                if isinstance(resolved_value, str) and resolved_value.startswith("{{") and resolved_value.endswith("}}"):
                    continue
                resolved[k] = resolved_value
            return resolved
        elif isinstance(template, list):
            return [self._resolve_template_variables(item, parameters) for item in template]
        else:
            return template
    
    def execute(self, ctrl_action: Dict[str, Any], execution_context, dependencies: Dict[str, Any]) -> str:
        """
        Execute API call based on configuration with agent node support
        
        Args:
            ctrl_action: Action configuration from YAML
            execution_context: Execution context
            dependencies: Dependencies and variables
            
        Returns:
            str: Result of API call
        """
        api_name = ctrl_action.get("value", "")
        parameters = ctrl_action.get("parameters", {})
        
        # Get agent node with priority: Action level > Parameters level > API config level
        agent_node = ctrl_action.get("agent_node")  # Priority 1: Action级别 (推荐方式)
        if not agent_node:
            agent_node = parameters.get("agent_node")  # Priority 2: Parameters级别 (备选方式)
        
        if not api_name:
            LOGGER_ERROR("API name not specified in action")
            return "ERROR: API name not specified"
        
        # Get API configuration
        api_config = self.api_config.get(api_name)
        if not api_config:
            LOGGER_ERROR(f"API configuration not found for: {api_name}")
            return f"ERROR: API configuration not found for {api_name}"
        
        # Priority 3: Check API config level if not specified in action or parameters
        if not agent_node and "agent_node" in api_config:
            agent_node = api_config["agent_node"]  # API配置默认值
        
        try:
            # Auto-discover agent when agent_node is "auto" or starts with "auto_"
            agent_base_url = ctrl_action.get("agent_base_url")
            if not agent_base_url and agent_node and (agent_node == "auto" or agent_node.startswith("auto_")):
                group = agent_node[5:] if agent_node.startswith("auto_") else "default"
                tag = group if group != "default" else None
                if not hasattr(self, '_auto_agent_urls'):
                    self._auto_agent_urls = {}
                if group not in self._auto_agent_urls:
                    url = self.node_manager.discover_dynamic_agent(tag=tag)
                    if url is None:
                        LOGGER_WARNING(f"No live agent found for group '{group}', falling back to localhost")
                        url = "http://localhost:9909"
                    self._auto_agent_urls[group] = url
                    LOGGER_INFO(f"Sticky auto agent '{group}' → {url}")
                agent_base_url = self._auto_agent_urls[group]

            # Get node configuration and base URL
            if agent_base_url:
                base_url = agent_base_url
            else:
                base_url = self.node_manager.get_base_url(agent_node)
            timeout_multiplier = self.node_manager.get_timeout_multiplier(agent_node) if not agent_base_url else 1.0
            retry_count = self.node_manager.get_retry_count(agent_node) if not agent_base_url else 3
            
            # Add base_url to parameters for template resolution
            resolved_parameters = {**parameters, "base_url": base_url}
            
            # Log node information
            if agent_node:
                node_config = self.node_manager.get_node_config(agent_node)
                if node_config:
                    LOGGER_INFO(f"Using agent node: {agent_node} ({node_config.get('name', 'Unknown')})")
                    LOGGER_INFO(f"Environment: {node_config.get('environment', 'Unknown')}")
            else:
                LOGGER_INFO("Using default agent node")
            
            # Resolve template variables in configuration
            resolved_config = self._resolve_template_variables(api_config, resolved_parameters)
            
            # Extract configuration
            url = resolved_config.get("url")
            method = resolved_config.get("method", "GET").upper()
            headers = resolved_config.get("headers", {})
            body = resolved_config.get("body")
            expected_status = resolved_config.get("expected_status", 200)
            base_timeout = resolved_config.get("timeout", 30)
            
            # Merge additional parameters into body for dynamic API calls
            # Skip internal keys like base_url, agent_node
            if body and isinstance(body, dict):
                skip_keys = {'base_url', 'agent_node'}
                for key, value in parameters.items():
                    if key not in skip_keys and key not in body:
                        body[key] = value
            
            # Apply timeout multiplier
            timeout = int(base_timeout * timeout_multiplier)
            
            LOGGER_INFO(f"Executing API call: {api_name}")
            LOGGER_INFO(f"URL: {url}")
            LOGGER_INFO(f"Method: {method}")
            LOGGER_INFO(f"Request body: {body}")
            LOGGER_INFO(f"Timeout: {timeout}s (base: {base_timeout}s, multiplier: {timeout_multiplier})")
            
            # Retry logic
            last_exception = None
            for attempt in range(retry_count):
                try:
                    # Make API call
                    start_time = time.time()
                    
                    if method in ["POST", "PUT", "PATCH"] and body:
                        response = requests.request(
                            method=method,
                            url=url,
                            headers=headers,
                            json=body,
                            timeout=timeout
                        )
                    else:
                        response = requests.request(
                            method=method,
                            url=url,
                            headers=headers,
                            timeout=timeout
                        )
                    
                    duration = time.time() - start_time
                    
                    # Log response
                    LOGGER_INFO(f"API Response Status: {response.status_code}")
                    LOGGER_INFO(f"API Response Time: {duration:.2f}s")
                    
                    # Check expected status
                    if response.status_code == expected_status:
                        LOGGER_INFO(f"API call successful: {api_name}")
                        
                        # Try to parse JSON response
                        try:
                            response_data = response.json()
                            LOGGER_INFO(f"Response data: {json.dumps(response_data, indent=2)}")
                            return f"SUCCESS: {api_name} completed"
                        except:
                            LOGGER_INFO(f"Response text: {response.text[:500]}")
                            return f"SUCCESS: {api_name} completed"
                    else:
                        LOGGER_WARNING(f"Unexpected status code: {response.status_code}, expected: {expected_status}")
                        if attempt < retry_count - 1:
                            LOGGER_INFO(f"Retrying... (attempt {attempt + 2}/{retry_count})")
                            time.sleep(1)  # Wait before retry
                            continue
                        return f"WARNING: Unexpected status {response.status_code}"
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    last_exception = e
                    if attempt < retry_count - 1:
                        LOGGER_WARNING(f"Request failed, retrying... (attempt {attempt + 2}/{retry_count}): {e}")
                        time.sleep(2)  # Wait longer before retry
                        continue
                    else:
                        break
                
            # If we get here, all retries failed
            if isinstance(last_exception, requests.exceptions.ConnectionError):
                error_msg = f"Connection error for API: {api_name} (node: {agent_node or 'default'})"
                LOGGER_ERROR(error_msg)
                return f"ERROR: {error_msg}"
            elif isinstance(last_exception, requests.exceptions.Timeout):
                error_msg = f"Timeout error for API: {api_name} (node: {agent_node or 'default'})"
                LOGGER_ERROR(error_msg)
                return f"ERROR: {error_msg}"
            else:
                error_msg = f"API call failed after {retry_count} retries: {api_name}"
                LOGGER_ERROR(error_msg)
                return f"ERROR: {error_msg}"
                
        except Exception as e:
            error_msg = f"API call failed for {api_name}: {str(e)}"
            LOGGER_ERROR(error_msg)
            return f"ERROR: {error_msg}"
    
    def get_action_type(self) -> str:
        return "api"
