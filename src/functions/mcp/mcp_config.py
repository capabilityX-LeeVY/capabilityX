"""
MCP Server and Client Configuration Management

This file contains all configuration information for MCP servers and clients,
allowing external machines to easily connect to your MCP server.
"""

import socket
import platform
import os

def get_local_ip():
    """Get local LAN IP address"""
    try:
        # Create a UDP socket connection to external address to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# Automatically get local IP
LOCAL_IP = get_local_ip()

def generate_unique_client_id():
    """Generate unique client ID - using simple combination of platform + machine name"""
    # Get platform information
    os_type = "win" if os.name == "nt" else "linux" if os.name == "posix" else "other"
    
    # Get machine name and clean special characters
    machine_name = platform.node().replace(' ', '-').replace('_', '-')
    
    # Generate simple client_id: wrs_platform_machinename
    client_id = f"wrs_{os_type}_{machine_name}"
    
    return client_id

def get_machine_info():
    """Get machine information for debugging"""
    try:
        import uuid
        mac_addr = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,8*6,8)][::-1])
    except:
        mac_addr = "unknown"
        
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "local_ip": LOCAL_IP,
        "mac_address": mac_addr,
        "os_name": os.name,
        "generated_client_id": generate_unique_client_id()
    }

# MCP server configuration
MCP_SERVER_CONFIG = {
    "host": "0.0.0.0",  # Listen on all interfaces
    "port": 8000,
    "local_url": f"http://127.0.0.1:8000",
    "external_url": f"http://{LOCAL_IP}:8000"
}

# Available MCP server list (for client selection)
AVAILABLE_SERVERS = {                               
    "local": {
        "name": "Local Server",
        "base_url": MCP_SERVER_CONFIG["local_url"],
        "description": "MCP server running on local machine"
    },
    "external": {
        "name": "External Accessible Server", 
        "base_url": MCP_SERVER_CONFIG["external_url"],
        "description": f"MCP server accessible from external network (IP: {LOCAL_IP})"
    }
}

# Default client configuration
DEFAULT_CLIENT_CONFIGS = {
    "primary": {
        "base_url": "https://wrs.qa.webex.com/mcp",  # Use remote server address
        "client_id": generate_unique_client_id()  # Auto-generate unique ID
    },
    "backup": {
        "base_url": MCP_SERVER_CONFIG["local_url"],
        "client_id": f"{generate_unique_client_id()}_backup"  # Backup connection uses different ID
    }
}

# API endpoints
API_ENDPOINTS = {
    "register": "/register",
    "send_message": "/send_message", 
    "events": "/events",
    "status": "/status"
}

def get_server_info():
    """Get server information summary"""
    return {
        "server_config": MCP_SERVER_CONFIG,
        "available_servers": AVAILABLE_SERVERS,
        "endpoints": {
            endpoint: f"{MCP_SERVER_CONFIG['external_url']}{path}"
            for endpoint, path in API_ENDPOINTS.items()
        }
    }

def get_client_connection_info():
    """Get external client connection information"""
    return f"""
=== MCP Client Connection Configuration ===

1. Server Address:
   - Local Access: {MCP_SERVER_CONFIG['local_url']}
   - External Access: {MCP_SERVER_CONFIG['external_url']}

2. API Endpoints:
   - Register Client: POST {MCP_SERVER_CONFIG['external_url']}/register
   - Send Message: POST {MCP_SERVER_CONFIG['external_url']}/send_message
   - SSE Event Stream: GET {MCP_SERVER_CONFIG['external_url']}/events

3. Example Client Code:
   ```python
   import requests
   
   # Register client
   response = requests.post(
       "{MCP_SERVER_CONFIG['external_url']}/register",
       json={{"client_id": "your_client_id"}}
   )
   
   # Send message
   response = requests.post(
       "{MCP_SERVER_CONFIG['external_url']}/send_message", 
       json={{"msg": "Hello from external client"}}
   )
   ```

4. Network Requirements:
   - Ensure port {MCP_SERVER_CONFIG['port']} is open in firewall
   - External clients need to be able to access IP: {LOCAL_IP}
"""

def print_connection_info():
    """Print connection information to console"""
    print(get_client_connection_info())

def print_machine_info():
    """Print machine information and generated client_id"""
    info = get_machine_info()
    print("\n=== Machine Information and Client ID ===")
    print(f"🖥️ Hostname: {info['hostname']}")
    print(f"🔧 Platform: {info['platform']}")
    print(f"💻 Processor: {info['processor']}")
    print(f"🏗️ Architecture: {info['machine']}")
    print(f"🌐 Local IP: {info['local_ip']}")
    print(f"🔐 MAC Address: {info['mac_address']}")
    print(f"💾 Operating System: {info['os_name']}")
    print(f"🆔 Generated Client ID: {info['generated_client_id']}")
    
    # Check persistent file
    config_dir = os.path.dirname(os.path.abspath(__file__))
    client_id_file = os.path.join(config_dir, '.client_id')
    if os.path.exists(client_id_file):
        try:
            with open(client_id_file, 'r') as f:
                stored_id = f.read().strip()
                print(f"📁 Stored Client ID: {stored_id}")
        except:
            print("📁 Stored Client ID: Read failed")
    else:
        print("📁 Stored Client ID: File does not exist")

if __name__ == "__main__":
    print_connection_info()
    print_machine_info()
