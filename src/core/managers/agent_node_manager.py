"""
Agent Node Manager

Manages different API agent nodes and environments for test execution.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING, LOGGER_DEBUG
from config.paths import AGENT_NODES_CONFIG_PATH

_REGISTRY_URL = os.getenv("REGISTRY_URL", "").rstrip("/")
_REGISTRY_STRATEGY = os.getenv("REGISTRY_STRATEGY", "round_robin")


class AgentNodeManager:
    """Manages agent nodes configuration and provides node resolution"""
    
    def __init__(self, nodes_config_path: Optional[str] = None):
        if nodes_config_path is None:
            # Use centralized path configuration
            nodes_config_path = str(AGENT_NODES_CONFIG_PATH)
        
        self.config_path = Path(nodes_config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent nodes configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                LOGGER_DEBUG(f"Loaded agent nodes config with {len(config.get('nodes', {}))} nodes")
                return config
        except FileNotFoundError:
            LOGGER_ERROR(f"Agent nodes config file not found: {self.config_path}")
            return {"nodes": {}, "default_node": "local_dev"}
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"Invalid JSON in agent nodes config: {e}")
            return {"nodes": {}, "default_node": "local_dev"}
        except Exception as e:
            LOGGER_ERROR(f"Failed to load agent nodes config: {e}")
            return {"nodes": {}, "default_node": "local_dev"}
    
    def get_node_config(self, node_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific node
        
        Args:
            node_name: Name of the node. If None, returns default node.
            
        Returns:
            Node configuration dict or None if not found
        """
        if node_name is None:
            node_name = self._config.get("default_node", "local_dev")
        
        nodes = self._config.get("nodes", {})
        node_config = nodes.get(node_name)
        
        if not node_config:
            LOGGER_WARNING(f"Node '{node_name}' not found, trying fallback node")
            fallback_node = self._config.get("fallback_node")
            if fallback_node and fallback_node in nodes:
                LOGGER_INFO(f"Using fallback node: {fallback_node}")
                return nodes[fallback_node]
            else:
                LOGGER_ERROR(f"Node '{node_name}' not found and no valid fallback")
                return None
        
        return node_config
    
    def get_base_url(self, node_name: Optional[str] = None) -> str:
        """
        Get base URL for a specific node
        
        Args:
            node_name: Name of the node
            
        Returns:
            Base URL for the node
        """
        node_config = self.get_node_config(node_name)
        if node_config:
            return node_config.get("base_url", "http://localhost:9909")
        
        # Fallback to localhost
        LOGGER_WARNING(f"Using fallback URL for node: {node_name}")
        return "http://localhost:9909"

    def discover_dynamic_agent(self, tag: Optional[str] = None) -> Optional[str]:
        """
        Query the registry for a live agent.

        Used when agent_node starts with "auto".
        Returns base_url string, or None if registry is unavailable.
        """
        if not _REGISTRY_URL:
            LOGGER_WARNING("REGISTRY_URL not set — cannot auto-discover agent")
            return None
        params = {"strategy": _REGISTRY_STRATEGY}
        if tag:
            params["tag"] = tag
        try:
            resp = requests.get(
                f"{_REGISTRY_URL}/pick",
                params=params,
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                ip = data.get("ip")
                port = data.get("port")
                if ip and port:
                    url = f"http://{ip}:{port}"
                    LOGGER_INFO(
                        f"Auto-discovered agent (tag={tag or 'any'}) → {url} "
                        f"(agent_id={data.get('agent_id')}, strategy={_REGISTRY_STRATEGY})"
                    )
                    return url
            elif resp.status_code == 503:
                LOGGER_WARNING(f"Registry: no live agents available (tag={tag or 'any'})")
            else:
                LOGGER_WARNING(f"Registry /pick returned {resp.status_code}")
        except Exception as e:
            LOGGER_WARNING(f"Registry unreachable ({_REGISTRY_URL}): {e}")
        return None
    
    def list_available_nodes(self) -> list:
        """Get list of available node names"""
        return list(self._config.get("nodes", {}).keys())
    
    def get_node_environment(self, node_name: Optional[str] = None) -> str:
        """Get environment type for a node"""
        node_config = self.get_node_config(node_name)
        if node_config:
            return node_config.get("environment", "development")
        return "development"
    
    def get_timeout_multiplier(self, node_name: Optional[str] = None) -> float:
        """Get timeout multiplier for a node"""
        node_config = self.get_node_config(node_name)
        if node_config:
            return node_config.get("timeout_multiplier", 1.0)
        return 1.0
    
    def get_retry_count(self, node_name: Optional[str] = None) -> int:
        """Get retry count for a node"""
        node_config = self.get_node_config(node_name)
        if node_config:
            return node_config.get("retry_count", 3)
        return 3
    
    def validate_node_config(self) -> Dict[str, list]:
        """Validate all node configurations"""
        issues = {"errors": [], "warnings": []}
        
        nodes = self._config.get("nodes", {})
        if not nodes:
            issues["errors"].append("No nodes configured")
            return issues
        
        default_node = self._config.get("default_node")
        if default_node and default_node not in nodes:
            issues["errors"].append(f"Default node '{default_node}' not found in nodes")
        
        fallback_node = self._config.get("fallback_node")
        if fallback_node and fallback_node not in nodes:
            issues["warnings"].append(f"Fallback node '{fallback_node}' not found in nodes")
        
        for node_name, node_config in nodes.items():
            if not node_config.get("base_url"):
                issues["errors"].append(f"Node '{node_name}': Missing required 'base_url' field")
            
            if not node_config.get("name"):
                issues["warnings"].append(f"Node '{node_name}': Missing 'name' field")
        
        return issues
    
    def health_check_node(self, node_name: Optional[str] = None) -> bool:
        """
        Perform health check on a node
        
        Args:
            node_name: Name of the node to check
            
        Returns:
            True if node is healthy, False otherwise
        """
        import requests
        
        node_config = self.get_node_config(node_name)
        if not node_config:
            return False
        
        base_url = node_config.get("base_url")
        health_endpoint = node_config.get("health_check_endpoint", "/health")
        timeout = node_config.get("timeout_multiplier", 1.0) * 10  # Base timeout of 10s
        
        try:
            url = f"{base_url}{health_endpoint}"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                LOGGER_INFO(f"Node '{node_name}' health check passed")
                return True
            else:
                LOGGER_WARNING(f"Node '{node_name}' health check failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            LOGGER_ERROR(f"Node '{node_name}' health check failed: {e}")
            return False


# Global instance
agent_node_manager = AgentNodeManager()
