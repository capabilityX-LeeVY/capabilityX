import requests
import threading
import json
import time
import logging
import socket

# Import potentially missing modules and provide fallbacks
try:
    import psutil
except ImportError:
    psutil = None
    print("⚠️ psutil not available, some system info features will be limited")

try:
    import platform
except ImportError:
    platform = None
    print("⚠️ platform module not available")

# Django import - may not be available when running standalone
try:
    from django.conf import settings
except ImportError:
    settings = None
    print("⚠️ Django not available, running in standalone mode")

# Flask import
try:
    from flask import Flask, request, jsonify
except ImportError:
    print("❌ Flask not available, HTTP server will not work")
    Flask = None
    request = None
    jsonify = None

# Configure logging
logger = logging.getLogger(__name__)

# Ensure logger has handlers - add console output if no handlers exist
if not logger.handlers:
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    
    print("🔧 MCP Client logger configured with console output")

# Try to import project logging system as backup
try:
    from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
    USE_PROJECT_LOGGER = True
    print("✅ Project logger available as backup")
except ImportError:
    USE_PROJECT_LOGGER = False
    print("⚠️ Project logger not available, using standard logging")

def log_info(message):
    """Unified INFO logging function"""
    if USE_PROJECT_LOGGER:
        LOGGER_INFO(message)
    else:
        logger.info(message)
    print(f"ℹ️ {message}")  # Ensure console can see it

def log_debug(message):
    """Unified DEBUG logging function"""
    if USE_PROJECT_LOGGER:
        LOGGER_DEBUG(message)
    else:
        logger.debug(message)

def log_warning(message):
    """Unified WARNING logging function"""
    if USE_PROJECT_LOGGER:
        LOGGER_WARNING(message)
    else:
        logger.warning(message)
    print(f"⚠️ {message}")  # Ensure console can see it

def log_error(message):
    """Unified ERROR logging function"""
    if USE_PROJECT_LOGGER:
        LOGGER_ERROR(message)
    else:
        logger.error(message)
    print(f"❌ {message}")  # Ensure console can see it

# Import MCP configuration
try:
    import sys
    import os
    # Add src directory to path to import mcp_config
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from mcp_config import DEFAULT_CLIENT_CONFIGS, get_local_ip
    
    # Use configuration from mcp_config.py
    DEFAULT_SERVERS = DEFAULT_CLIENT_CONFIGS
    
except ImportError:
    # Fallback configuration if mcp_config is not available
    DEFAULT_SERVERS = {
        "primary": {
            "base_url": "http://10.140.217.123:8000",
            "client_id": "wrs_client_001"
        },
        "local": {
            "base_url": "http://127.0.0.1:8000",
            "client_id": "wrs_client_local"
        }
    }

# Global variables to control client state
_client_thread = None
_client_running = False
_registration_status = False
_http_server = None
_http_thread = None


class MCPClientHTTPServer:
    """HTTP server for receiving commands from MCP server"""
    
    def __init__(self, port=9001, host='0.0.0.0', parent_client=None):
        self.port = port
        self.host = host
        self.parent_client = parent_client  # Add reference to parent client
        self.server_thread = None
        self.running = False
        self.command_handlers = {}
        
        # Check if Flask is available
        if Flask is None:
            log_error("Flask not available, HTTP server cannot be created")
            self.app = None
            return
            
        self.app = Flask(__name__)
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        # If Flask is not available, skip route setup
        if self.app is None or Flask is None or request is None or jsonify is None:
            log_warning("Flask components not available, skipping route setup")
            return
        
        @self.app.route('/execute_command', methods=['POST'])
        def execute_command():
            """Receive and execute commands from server"""
            try:
                # Double check Flask component availability
                if request is None:
                    error_msg = "Flask request object not available"
                    logger.error(error_msg)
                    return {"status": "error", "message": error_msg}, 500
                
                data = request.get_json()
                if not data:
                    error_response = {"status": "error", "message": "No JSON data provided"}
                    if jsonify is not None:
                        return jsonify(error_response), 400
                    else:
                        return error_response, 400
                
                command = data.get('command')
                params = data.get('params', {})
                client_id = data.get('client_id')
                
                logger.info(f"Received HTTP command: {command}")
                print(f"📨 HTTP: {command}")
                
                if command in self.command_handlers:
                    try:
                        # Execute command
                        result = self.command_handlers[command](params)
                        
                        # Build response
                        response = {
                            "status": "success", 
                            "command": command,
                            "result": result,
                            "message": f"Command '{command}' executed successfully",
                            "timestamp": time.time(),
                            "client_id": client_id
                        }
                        
                        logger.info(f"HTTP command executed successfully: {command}")
                        print(f"✅ {command} done")
                        
                        # Asynchronously send result back to server (non-blocking HTTP response)
                        def send_result_async():
                            try:
                                # Debug information
                                logger.debug(f"send_result_async: parent_client={self.parent_client}, type={type(self.parent_client)}")
                                
                                if self.parent_client is not None:
                                    if hasattr(self.parent_client, '_send_http_command_result'):
                                        logger.debug(f"Calling _send_http_command_result for command: {command}")
                                        self.parent_client._send_http_command_result(command, result, client_id)
                                    else:
                                        logger.error(f"parent_client does not have _send_http_command_result method. Available methods: {[m for m in dir(self.parent_client) if not m.startswith('__')]}")
                                else:
                                    logger.error("parent_client is None")
                            except Exception as e:
                                logger.error(f"Error in async result sending: {e}")
                                import traceback
                                logger.error(f"Full traceback: {traceback.format_exc()}")
                        
                        # Send result in background thread
                        import threading
                        threading.Thread(target=send_result_async, daemon=True).start()
                        
                        if jsonify is not None:
                            return jsonify(response), 200
                        else:
                            return response, 200
                        
                    except Exception as e:
                        error_msg = f"Error executing command '{command}': {str(e)}"
                        logger.error(error_msg)
                        print(f"❌ {command} error")
                        
                        error_response = {
                            "status": "error", 
                            "command": command,
                            "message": error_msg,
                            "timestamp": time.time(),
                            "client_id": client_id
                        }
                        
                        # Send error result back to server
                        def send_error_async():
                            try:
                                # Debug information
                                logger.debug(f"send_error_async: parent_client={self.parent_client}, type={type(self.parent_client)}")
                                
                                if self.parent_client is not None:
                                    if hasattr(self.parent_client, '_send_http_command_result'):
                                        logger.debug(f"Calling _send_http_command_result for error command: {command}")
                                        self.parent_client._send_http_command_result(command, {"error": error_msg, "success": False}, client_id)
                                    else:
                                        logger.error(f"parent_client does not have _send_http_command_result method. Available methods: {[m for m in dir(self.parent_client) if not m.startswith('__')]}")
                                else:
                                    logger.error("parent_client is None in error handler")
                            except Exception as e:
                                logger.error(f"Error in async error sending: {e}")
                                import traceback
                                logger.error(f"Full traceback: {traceback.format_exc()}")
                        
                        threading.Thread(target=send_error_async, daemon=True).start()
                        
                        if jsonify is not None:
                            return jsonify(error_response), 500
                        else:
                            return error_response, 500
                else:
                    error_msg = f"Unknown command: {command}"
                    logger.warning(error_msg)
                    print(f"⚠️ Unknown: {command}")
                    
                    error_response = {
                        "status": "error", 
                        "command": command,
                        "message": error_msg,
                        "available_commands": list(self.command_handlers.keys()),
                        "timestamp": time.time(),
                        "client_id": client_id
                    }
                    
                    if jsonify is not None:
                        return jsonify(error_response), 400
                    else:
                        return error_response, 400
                    
            except Exception as e:
                error_msg = f"Error processing HTTP request: {str(e)}"
                logger.error(error_msg)
                if jsonify is not None:
                    return jsonify({"status": "error", "message": error_msg, "timestamp": time.time()}), 500
                else:
                    return {"status": "error", "message": error_msg, "timestamp": time.time()}, 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            response_data = {
                "status": "healthy",
                "service": "MCP Client HTTP Server",
                "available_commands": list(self.command_handlers.keys())
            }
            if jsonify is not None:
                return jsonify(response_data), 200
            else:
                return response_data, 200
            
        @self.app.route('/commands', methods=['GET'])
        def list_commands():
            """List all available commands"""
            response_data = {
                "available_commands": list(self.command_handlers.keys()),
                "total_commands": len(self.command_handlers)
            }
            if jsonify is not None:
                return jsonify(response_data), 200
            else:
                return response_data, 200
    
    def register_command(self, command_name, handler_func):
        """Register command handler"""
        self.command_handlers[command_name] = handler_func
        logger.info(f"Registered command handler: {command_name}")
    
    def start(self):
        """Start HTTP server"""
        if self.running:
            logger.warning("HTTP server is already running")
            return True
            
        try:
            # Check if port is available
            if not self._is_port_available():
                logger.error(f"Port {self.port} is already in use")
                return False
                
            self.running = True
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="MCP-HTTP-Server"
            )
            self.server_thread.start()
            
            # Wait for server to start
            time.sleep(1)
            
            logger.info(f"MCP Client HTTP Server started on {self.host}:{self.port}")
            print(f"🚀 HTTP Server: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            print(f"❌ HTTP server failed: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop HTTP server"""
        self.running = False
        logger.info("MCP Client HTTP Server stopped")
        logger.info("HTTP Server stopped")
    
    def _is_port_available(self):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                return True
        except socket.error:
            return False
    
    def _run_server(self):
        """Run Flask server"""
        try:
            if self.app is not None:
                self.app.run(
                    host=self.host,
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            else:
                logger.error("Flask app is None, cannot start HTTP server")
                print("❌ Flask not available, HTTP server cannot start")
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            print(f"❌ HTTP error: {e}")
        finally:
            self.running = False


class MCPClient:
    """MCP Client Manager"""
    
    def __init__(self, server_url=None, client_id=None, http_port=9001):
        self.server_url = server_url or DEFAULT_SERVERS["primary"]["base_url"]
        self.client_id = client_id or DEFAULT_SERVERS["primary"]["client_id"]
        self.running = False
        self.sse_connected = False  # Add SSE connection status
        self.sse_thread = None
        self.http_server = MCPClientHTTPServer(port=http_port, parent_client=self)  # Pass self reference
        self.http_port = http_port
        
        # 🔐 Get client IP address for session identification
        self.client_ip = self._get_local_ip()
        self.session_id = None  # 🔐 Will be set after registration
        
        # Heartbeat related configuration
        self.heartbeat_interval = 60  # Send heartbeat every 60 seconds
        self.heartbeat_thread = None
        self.heartbeat_running = False
        
        # Message filtering to prevent processing old/duplicate messages
        self.processed_message_ids = set()  # Track processed message IDs
        self.session_start_time = time.time()  # Record session start time
        self.max_message_age = 300  # Ignore messages older than 5 minutes
        
        # Register default command handlers
        self._register_default_commands()
    
    def _get_local_ip(self):
        """🔐 Get local IP address for session identification"""
        try:
            # Method 1: Connect to external address to get local IP
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"🔐 Detected local IP: {local_ip}")
            return local_ip
        except Exception as e:
            logger.warning(f"⚠️ Could not detect local IP (Method 1): {e}")
            
            # Method 2: Fallback to hostname resolution
            try:
                import socket
                local_ip = socket.gethostbyname(socket.gethostname())
                logger.info(f"🔐 Detected local IP (fallback): {local_ip}")
                return local_ip
            except Exception as e2:
                logger.error(f"❌ Could not detect local IP (Method 2): {e2}")
                return "127.0.0.1"  # Ultimate fallback
    
    def _register_default_commands(self):
        """Register default command handlers"""
        
        # Basic command handlers
        def handle_ping(params):
            return {
                "success": True,
                "message": "pong", 
                "timestamp": time.time(), 
                "client_id": self.client_id
            }

        def handle_status(params):
            return {
                "success": True,
                "client_id": self.client_id,
                "server_url": self.server_url,
                "sse_connected": self.sse_connected,
                "http_server_running": self.http_server and self.http_server.server_thread and self.http_server.server_thread.is_alive(),
                "timestamp": time.time()
            }

        def handle_send_message(params):
            message = params.get('message', 'Hello from client')
            if self.send_message(message):
                return {"success": True, "message": f"Sent: {message}"}
            return {"success": False, "error": "Failed to send message"}

        def handle_restart_sse(params):
            # Restart SSE connection
            try:
                self.stop()
                time.sleep(1)
                self.start()
                return {
                    "success": True, 
                    "message": "SSE connection restarted",
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to restart SSE: {str(e)}",
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }

        def handle_execute_test_case(params):
            test_case = params.get('test_case', 'default_test')
            try:
                return {
                    "success": True,
                    "result": f"Executed test case: {test_case}",
                    "test_case": test_case,
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to execute test case: {str(e)}",
                    "test_case": test_case,
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }

        def handle_system_info(params):
            try:
                import psutil
                import platform
                return {
                    "success": True,
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to get system info: {str(e)}",
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }

        def handle_custom_action(params):
            action = params.get('action', 'unknown')
            try:
                if action == 'log_message':
                    message = params.get('message', 'Default log message')
                    print(f"📝 Log: {message}")
                    return {
                        "success": True, 
                        "logged": message,
                        "timestamp": time.time(),
                        "client_id": self.client_id
                    }
                elif action == 'send_notification':
                    title = params.get('title', 'Notification')
                    body = params.get('body', 'Default notification body')
                    print(f"🔔 Notification: {title} - {body}")
                    return {
                        "success": True, 
                        "notification_sent": True,
                        "title": title,
                        "body": body,
                        "timestamp": time.time(),
                        "client_id": self.client_id
                    }
                else:
                    return {
                        "success": False, 
                        "error": f"Unknown action: {action}",
                        "available_actions": ["log_message", "send_notification"],
                        "timestamp": time.time(),
                        "client_id": self.client_id
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error executing action '{action}': {str(e)}",
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }

        # Register basic commands
        self.http_server.register_command('ping', handle_ping)
        self.http_server.register_command('status', handle_status)
        self.http_server.register_command('send_message', handle_send_message)
        self.http_server.register_command('restart_sse', handle_restart_sse)
        self.http_server.register_command('execute_test_case', handle_execute_test_case)
        self.http_server.register_command('system_info', handle_system_info)
        self.http_server.register_command('custom_action', handle_custom_action)
        
        # Import and register business related commands
        try:
            # Try absolute import
            try:
                from business_commands import (
                    handle_run_test_suite,
                    handle_run_single_test, 
                    handle_get_test_report,
                    handle_cleanup_test_environment,
                    handle_get_test_status,
                    handle_execute_workflow
                )
            except ImportError:
                # Try relative import (if running in package)
                from .business_commands import (
                    handle_run_test_suite,
                    handle_run_single_test, 
                    handle_get_test_report,
                    handle_cleanup_test_environment,
                    handle_get_test_status,
                    handle_execute_workflow
                )
            
            # Register business commands
            self.http_server.register_command('run_test_suite', handle_run_test_suite)
            self.http_server.register_command('run_single_test', handle_run_single_test)
            self.http_server.register_command('get_test_report', handle_get_test_report)
            self.http_server.register_command('cleanup_environment', handle_cleanup_test_environment)
            self.http_server.register_command('get_test_status', handle_get_test_status)
            self.http_server.register_command('execute_workflow', handle_execute_workflow)
            
            logger.info("Business commands registered successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import business commands: {e}")
        
        logger.debug(f"Registered {len(self.http_server.command_handlers)} commands")
    
    def register_custom_command(self, command_name, handler_func):
        """Register custom command handler"""
        self.http_server.register_command(command_name, handler_func)
        
    def register(self):
        """Register client to server"""
        try:
            # First try to clear any pending messages for this client
            self._clear_pending_messages()
            
            # 🔐 Send client IP for session identification
            url = f"{self.server_url}/register"
            payload = {
                "client_id": self.client_id,
                "client_ip": self.client_ip,  # 🔐 Add client IP for session identification
                "http_callback_url": f"http://{self.client_ip}:{self.http_port}",  # Use actual IP instead of localhost
                "http_port": self.http_port,
                "clear_pending": True,  # Request server to clear any pending messages
                "session_start": True   # Indicate this is a new session
            }
            logger.info(f"📤 Registering client: {self.client_id} from IP: {self.client_ip}")
            resp = requests.post(url, json=payload, timeout=10)
            logger.info(f"Registration: {resp.status_code}")
            
            # 🔐 Check if server returned session_id
            if resp.status_code == 200:
                try:
                    response_data = resp.json()
                    session_id = response_data.get('session_id')
                    if session_id:
                        logger.info(f"🔐 Received session_id from server: {session_id}")
                        self.session_id = session_id  # Store session_id
                    else:
                        logger.warning("⚠️ Server did not return session_id")
                except Exception as e:
                    logger.warning(f"⚠️ Could not parse registration response: {e}")
            
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False

    def _clear_pending_messages(self):
        """Clear any pending messages for this client on the server"""
        try:
            url = f"{self.server_url}/clear_pending"
            payload = {
                "client_id": self.client_id,
                "action": "clear_all"
            }
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                logger.info("✅ Successfully cleared pending messages")
            else:
                logger.warning(f"⚠️ Clear pending messages returned: {resp.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear pending messages: {e}")
            # This is not critical, continue with registration

    def send_message(self, msg):
        """Send message to server"""  
        try:
            url = f"{self.server_url}/send_message"
            payload = {"msg": msg}
            
            # Simplified pre-send logging
            logger.info(f"📤 [SEND_MESSAGE] Sending to {url}")
            logger.info(f"📤 [SEND_MESSAGE] Message: {str(msg)[:100]}{'...' if len(str(msg)) > 100 else ''}")
            logger.debug(f"📤 [SEND_MESSAGE] Full payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            print(f"📤 [SEND_MESSAGE] Sending message ({len(str(msg))} chars)")
            
            # Send request
            resp = requests.post(url, json=payload, timeout=10)
            
            # Simplified response logging
            logger.info(f"📨 [SEND_MESSAGE] Response status: {resp.status_code}")
            logger.debug(f"📨 [SEND_MESSAGE] Response headers: {dict(resp.headers)}")
            
            # Handle response content
            try:
                response_text = resp.text
                if response_text:
                    logger.debug(f"📨 [SEND_MESSAGE] Response body: {response_text}")
                    try:
                        response_json = resp.json()
                        logger.debug(f"📨 [SEND_MESSAGE] Response JSON: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        logger.debug("📨 [SEND_MESSAGE] Response is not JSON format")
            except Exception as resp_e:
                logger.warning(f"📨 [SEND_MESSAGE] Could not read response: {resp_e}")
            
            success = resp.status_code == 200
            if success:
                logger.info(f"✅ [SEND_MESSAGE] Message sent successfully")
                print(f"✅ [SEND_MESSAGE] Success")
            else:
                logger.warning(f"❌ [SEND_MESSAGE] Failed to send message. Status: {resp.status_code}")
                print(f"❌ [SEND_MESSAGE] Failed: {resp.status_code}")
                
            return success
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [SEND_MESSAGE] Connection error: {e}")
            print(f"❌ [SEND_MESSAGE] Connection error")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ [SEND_MESSAGE] Timeout error: {e}")
            print(f"❌ [SEND_MESSAGE] Timeout")
            return False
        except Exception as e:
            logger.error(f"❌ [SEND_MESSAGE] Unexpected error: {e}")
            print(f"❌ [SEND_MESSAGE] Error: {e}")
            return False
    
    def send_result_to_server(self, result_data):
        """Send result data directly to server's dedicated endpoint"""
        try:
            url = f"{self.server_url}/client_response"
            
            # Pre-send logging
            command_type = result_data.get('type', 'unknown')
            command_name = result_data.get('command_executed', 'unknown')
            logger.info(f"🚀 [SEND_RESULT] Sending {command_type} result: {command_name}")
            logger.info(f"🚀 [SEND_RESULT] Target URL: {url}")
            logger.debug(f"🚀 [SEND_RESULT] Payload: {json.dumps(result_data, indent=2, ensure_ascii=False)}")
            
            # Send request
            resp = requests.post(url, json=result_data, timeout=10)
            
            # Response logging
            logger.info(f"📨 [SEND_RESULT] Response status: {resp.status_code}")
            logger.debug(f"📨 [SEND_RESULT] Response headers: {dict(resp.headers)}")
            
            # Try to read response content
            try:
                response_text = resp.text
                if response_text:
                    logger.debug(f"📨 [SEND_RESULT] Response body: {response_text}")
                    try:
                        response_json = resp.json()
                        logger.debug(f"📨 [SEND_RESULT] Response JSON: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        logger.debug("📨 [SEND_RESULT] Response is not JSON format")
            except Exception as resp_e:
                logger.warning(f"📨 [SEND_RESULT] Could not read response: {resp_e}")
            
            # Determine success status
            success = resp.status_code == 200
            if success:
                logger.info(f"✅ [SEND_RESULT] Successfully sent {command_name} result to server")
                print(f"✅ Result sent: {command_name}")
            else:
                # Enhanced error logging
                logger.error(f"❌ [SEND_RESULT] Failed to send {command_name} result. Status: {resp.status_code}")
                print(f"❌ Result failed: {command_name} (Status: {resp.status_code})")
                
                # If it's a 400 error, record more detailed information
                if resp.status_code == 400:
                    try:
                        error_response = resp.json()
                        logger.error(f"❌ [SEND_RESULT] 400 Error details: {json.dumps(error_response, indent=2)}")
                        print(f"❌ 400 Error details: {error_response}")
                    except:
                        logger.error(f"❌ [SEND_RESULT] 400 Error response text: {resp.text}")
                        print(f"❌ 400 Error text: {resp.text}")
                    
                    # Record the data we sent for debugging
                    logger.error(f"❌ [SEND_RESULT] Sent data was: {json.dumps(result_data, indent=2)}")
                
            return success
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [SEND_RESULT] Connection error: {e}")
            print(f"❌ Connection error sending result")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ [SEND_RESULT] Timeout error: {e}")
            print(f"❌ Timeout sending result")
            return False
        except Exception as e:
            logger.error(f"❌ [SEND_RESULT] Unexpected error: {e}")
            print(f"❌ Error sending result: {e}")
            return False

    def listen_sse(self):
        """Listen to server-sent events"""
        retry_count = 0
        max_retries = 3
        
        while self.running and retry_count < max_retries:
            try:
                # 🔐 Add client_id parameter to SSE connection for message filtering
                url = f"{self.server_url}/events?client_id={self.client_id}"
                log_info(f"🔐 Starting SSE connection to {url}...")
                log_info(f"🔐 Using client_id: {self.client_id} for targeted message filtering")
                log_info("Connecting to SSE, waiting for server push...")
                
                # Use better headers and timeout settings
                headers = {
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
                
                response = requests.get(
                    url, 
                    stream=True, 
                    timeout=(10, 60),  # (connect_timeout, read_timeout)
                    headers=headers
                )
                
                # Check response status
                if response.status_code != 200:
                    log_error(f"SSE connection failed with status {response.status_code}")
                    break
                
                log_info(f"SSE connection established, status: {response.status_code}")
                self.sse_connected = True  # Mark SSE as connected
                
                # Manual SSE parsing instead of using sseclient library
                for line in response.iter_lines(decode_unicode=True):
                    if not self.running:
                        break
                        
                    if line:
                        line = line.strip()
                        
                        # Parse SSE format manually
                        if line.startswith('data: '):
                            data_content = line[6:].strip()  # Remove 'data: ' prefix and strip whitespace
                            
                            try:
                                # Try to parse as JSON - skip empty content
                                if data_content and data_content not in ['', 'null', 'undefined']:
                                    data = json.loads(data_content)
                                    logger.info(f"Received SSE message: {data.get('type', 'unknown')}")
                                    self._handle_server_message(data)
                                else:
                                    logger.debug(f"Skipping empty SSE data: '{data_content}'")
                                    continue
                            except json.JSONDecodeError as e:
                                # Maybe it's double-encoded or has extra formatting
                                try:
                                    # Check if it has another 'data: ' prefix
                                    if data_content.startswith('data: '):
                                        inner_data = data_content[6:].strip()
                                        if inner_data and inner_data not in ['', 'null', 'undefined']:
                                            data = json.loads(inner_data)
                                            logger.info(f"Received nested SSE: {data.get('type', 'unknown')}")
                                            self._handle_server_message(data)
                                        else:
                                            logger.debug(f"Skipping empty nested SSE data: '{inner_data}'")
                                    else:
                                        if data_content:  # Only warn about non-empty content
                                            logger.warning(f"Non-JSON SSE data: {data_content[:50]}...")
                                except json.JSONDecodeError:
                                    if data_content:  # Only warn about non-empty content
                                        logger.warning(f"Non-JSON SSE data: {data_content[:50]}...")
                            except Exception as e:
                                logger.error(f"Parse SSE message failed: {e}")
                        
                        elif line.startswith('event: '):
                            event_type = line[7:]  # Remove 'event: ' prefix
                            logger.debug(f"Received SSE event type: {event_type}")
                        
                        elif line.startswith('id: '):
                            event_id = line[4:]  # Remove 'id: ' prefix
                            logger.debug(f"Received SSE event id: {event_id}")
                        
                        elif line.startswith('retry: '):
                            retry_time = line[7:]  # Remove 'retry: ' prefix
                            logger.debug(f"Received SSE retry time: {retry_time}")
                
                # If we reach here, the connection closed normally
                logger.info("SSE connection closed by server")
                break
                
            except requests.exceptions.ConnectTimeout:
                logger.warning("SSE connection timeout")
                break
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"SSE connection error: {e}")
                retry_count += 1
                if retry_count < max_retries and self.running:
                    logger.info(f"Retrying SSE connection... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(5)
                else:
                    break
            except Exception as e:
                logger.error(f"SSE connection failed: {e}")
                retry_count += 1
                if retry_count < max_retries and self.running:
                    logger.info(f"Retrying SSE connection... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(5)
                else:
                    break
        
        logger.info("SSE listening thread terminated")
        logger.info("SSE listening thread terminated")
        self.sse_connected = False  # Mark SSE as disconnected
            
    def _handle_server_message(self, data):
        """Handle messages pushed from server"""
        # Handle different message types here
        message_type = data.get('type', 'unknown')
        content = data.get('content', '')
        sender = data.get('sender', 'unknown')
        target_client = data.get('target_client')
        message_id = data.get('message_id', 'no_id')
        timestamp = data.get('timestamp', 'no_timestamp')
        
        # Detailed message debug information
        log_info(f"📨 Incoming SSE Message Details:")
        log_info(f"  📋 Type: {message_type}")
        log_info(f"  📝 Content: {content}")
        log_info(f"  👤 Sender: {sender}")
        log_info(f"  🎯 Target Client: {target_client}")
        log_info(f"  🆔 Message ID: {message_id}")
        log_info(f"  ⏰ Timestamp: {timestamp}")
        log_info(f"  🔧 Current Client ID: {self.client_id}")
        
        print(f"🔄 Processing message: {message_type} from {sender}")  # Add console output as backup
        
        # 🚫 Filter duplicate and old messages
        if not self._should_process_message(message_id, timestamp, content):
            return
        
        # Check if message is for current client
        if target_client and target_client != self.client_id:
            log_info(f"Message not for this client (target: {target_client}, current: {self.client_id})")
            return
        
        if message_type == 'notification':
            log_info(f"Received notification: {content}")
        elif message_type == 'command':
            log_info(f"Received command: {content}")
            # Convert SSE message to HTTP command format and execute
            self._execute_sse_command(content, data)
        elif message_type == 'notify':
            # Handle notify type messages - may contain commands to execute
            self._handle_notify_message(content, data)
        else:
            log_info(f"Received unknown message type: {message_type}")

    def _should_process_message(self, message_id, timestamp, content):
        """Check if the message should be processed (filter duplicates and old messages)"""
        # Check for duplicate message IDs
        if message_id != 'no_id' and message_id in self.processed_message_ids:
            log_info(f"🚫 Skipping duplicate message ID: {message_id}")
            return False
        
        # Check message age based on timestamp
        try:
            if timestamp != 'no_timestamp':
                # Parse timestamp (assuming it's a Unix timestamp)
                msg_time = float(timestamp)
                current_time = time.time()
                
                # Check if timestamp looks wrong (too old or in future)
                if msg_time < 1700000000:  # Before 2023 (clearly wrong)
                    log_info(f"🚫 Skipping message with invalid timestamp: {timestamp}")
                    return False
                
                # Check if message is from before this session started
                if msg_time < self.session_start_time:
                    log_info(f"🚫 Skipping old message from before session start: {timestamp}")
                    return False
                
                # Check if message is too old
                age = current_time - msg_time
                if age > self.max_message_age:
                    log_info(f"🚫 Skipping old message (age: {age:.1f}s): {content[:50]}")
                    return False
        except (ValueError, TypeError) as e:
            log_info(f"⚠️ Could not parse timestamp '{timestamp}': {e}")
        
        # Record this message as processed
        if message_id != 'no_id':
            self.processed_message_ids.add(message_id)
        
        log_info(f"✅ Message passed filtering, will process: {message_id}")
        return True
    
    def _handle_notify_message(self, content, data):
        """Handle notify type messages"""
        logger.debug(f"Notify message: {content[:50]}...")
        
        # First check if it's a command execution result
        if content.startswith('Command execution result:'):
            logger.info("Received command execution result notification")
            self._handle_command_result_notification(content, data)
            return
        
        # Try to parse JSON format content
        try:
            if content.startswith('{') and content.endswith('}'):
                parsed_content = json.loads(content)
                
                # Check if it's a command execution result
                if parsed_content.get('type') == 'command_result':
                    logger.info("Received command execution result")
                    self._handle_command_result_notification(content, data, parsed_content)
                    return
                elif parsed_content.get('type') == 'http_command_result':
                    logger.info("Received HTTP command execution result")
                    self._handle_command_result_notification(content, data, parsed_content)
                    return
                elif 'command' in parsed_content:
                    # This is a command to execute
                    self._execute_sse_command(parsed_content['command'], parsed_content)
                    return
        except json.JSONDecodeError:
            pass  # Continue processing non-JSON content
        
        # Determine if it's a command based on message content
        # Filter out heartbeat-related ping messages, these are now handled by independent heartbeat thread
        if content == 'ping' or content == 'heartbeat':
            log_debug(f"🔇 Ignoring heartbeat/ping message in SSE: {content}")
            return  # Return directly, don't process heartbeat messages
        
        if content in self.http_server.command_handlers:
            logger.info(f"Executing SSE command: {content}")
            self._execute_sse_command(content, data)
            return  # Add return to avoid executing subsequent confirmation logic
        elif content == 'status':
            # Special handling for status messages
            self._execute_sse_command('status', data)
            return  # Add return
        elif content.startswith('execute_'):
            # Handle commands starting with execute_
            command = content.replace('execute_', '')
            if command in self.http_server.command_handlers:
                self._execute_sse_command(command, data)
                return  # Add return
        else:
            # If it's not a known command or result, log and optionally forward confirmation
            logger.info(f"Content '{content}' is not a recognized command, treating as information message")
            self._send_acknowledgment(content, data)
    
    def _handle_command_result_notification(self, content, original_data, parsed_result=None):
        """Handle command execution result notifications"""
        try:
            # Parse result (if not already parsed)
            if parsed_result is None:
                if content.startswith('Command execution result:'):
                    # Extract JSON part
                    json_start = content.find('{')
                    if json_start != -1:
                        json_content = content[json_start:]
                        parsed_result = json.loads(json_content)
                    else:
                        logger.warning("Could not extract JSON from command result content")
                        return
                else:
                    parsed_result = json.loads(content)
            
            command_executed = parsed_result.get('command_executed', 'unknown')
            execution_source = parsed_result.get('execution_source', 'unknown')
            success = parsed_result.get('success', True)
            result_client_id = parsed_result.get('client_id')
            
            logger.info(f"Processing result: {command_executed} (source: {execution_source}, success: {success})")
            
            # Check if this is a result from the current client, if so no need to send acknowledgment
            if result_client_id == self.client_id:
                logger.info(f"Received result from own client ({self.client_id}), skipping acknowledgment to avoid duplication")
                return
            
            # Only send acknowledgment for results from other clients
            acknowledgment = {
                'type': 'result_acknowledgment',
                'original_command': command_executed,
                'original_execution_source': execution_source,
                'received_at': time.time(),
                'client_id': self.client_id,
                'status': 'received_and_processed',
                'original_message_id': original_data.get('message_id'),
                'original_result': parsed_result
            }
            
            # Send acknowledgment
            ack_success = self._send_acknowledgment_to_server(acknowledgment)
            
            if ack_success:
                logger.info(f"Acknowledgment sent for {command_executed} from client {result_client_id}")
            else:
                logger.warning(f"Failed to send acknowledgment for {command_executed}")
                
        except Exception as e:
            logger.error(f"Error handling command result notification: {e}")
    
    def _send_acknowledgment(self, content, data):
        """Send general acknowledgment message"""
        try:
            ack_message = {
                'type': 'general_acknowledgment',
                'received_content': content[:100] + '...' if len(content) > 100 else content,  # Truncate long content
                'received_at': time.time(),
                'client_id': self.client_id,
                'original_message_id': data.get('message_id'),
                'status': 'received'
            }
            
            self._send_acknowledgment_to_server(ack_message)
            logger.debug("General acknowledgment sent")
            
        except Exception as e:
            logger.error(f"Error sending general acknowledgment: {e}")
    
    def _send_acknowledgment_to_server(self, ack_data):
        """Send acknowledgment message to server, avoid duplicate sending"""
        try:
            command_type = ack_data.get('type', 'unknown')
            logger.info(f"📤 [SEND_ACK] Preparing acknowledgment: {command_type}")
            
            # Method 1: Only use dedicated result endpoint (recommended and only method)
            direct_success = self.send_result_to_server(ack_data)
            
            if direct_success:
                logger.info(f"✅ [SEND_ACK] Acknowledgment sent successfully via direct endpoint")
                print(f"✅ Acknowledgment sent: {command_type}")
                return True
            else:
                logger.error(f"❌ [SEND_ACK] Failed to send acknowledgment via direct endpoint")
                print(f"❌ Acknowledgment failed: {command_type}")
                return False
            
        except Exception as e:
            error_msg = f"❌ [SEND_ACK] Error sending acknowledgment: {e}"
            logger.error(error_msg)
            print(f"❌ Acknowledgment error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def _execute_sse_command(self, command, message_data):
        """Execute command extracted from SSE message"""
        try:
            log_info(f"🚀 Executing SSE Command: {command}")
            log_info(f"  📊 Available handlers: {list(self.http_server.command_handlers.keys())}")
            log_info(f"  🔍 Command exists in handlers: {command in self.http_server.command_handlers}")
            log_info(f"  📋 Message data keys: {list(message_data.keys())}")
            
            if command in self.http_server.command_handlers:
                logger.info(f"Executing SSE command: {command}")
                print(f"🚀 SSE: {command}")
                
                # Prepare parameters
                params = message_data.get('params', {})
                if not params and 'content' in message_data:
                    # If no params, try to parse from content
                    try:
                        import json
                        if isinstance(message_data['content'], str) and message_data['content'].startswith('{'):
                            params = json.loads(message_data['content'])
                    except:
                        params = {'message_content': message_data['content']}
                
                log_info(f"  🔧 Final params: {params}")
                
                # Add message metadata to parameters
                params.update({
                    'sse_message': True,
                    'sender': message_data.get('sender'),
                    'timestamp': message_data.get('timestamp'),
                    'message_id': message_data.get('message_id')
                })
                
                # Execute command
                result = self.http_server.command_handlers[command](params)
                
                print(f"✅ {command} done")
                logger.info(f"SSE command result: {result}")
                
                # Optional: send result back to server
                self._send_command_result(command, result, message_data, "SSE")
                
            else:
                logger.warning(f"Unknown SSE command: {command}")
                log_info(f"❌ Command '{command}' not found in handlers")
                
        except Exception as e:
            error_msg = f"Error executing SSE command '{command}': {str(e)}"
            logger.error(error_msg)
            log_error(error_msg)
    
    def _send_command_result(self, command, result, original_message, execution_source="SSE"):
        """Send command execution result back to server, avoid duplicate sending"""
        try:
            # Build detailed result message
            response_message = {
                'type': 'command_result',
                'command_executed': command,
                'result': result,
                'response': result,  # Add response field required by server
                'execution_source': execution_source,  # SSE or HTTP
                'original_message_id': original_message.get('message_id'),
                'client_id': self.client_id,
                'timestamp': time.time(),
                'success': result.get('success', True) if isinstance(result, dict) else True
            }
            
            # If there's error information in result, extract it
            if isinstance(result, dict) and 'error' in result:
                response_message['error'] = result['error']
                response_message['success'] = False
            
            # Ensure necessary fields exist
            if 'message_id' not in response_message:
                response_message['message_id'] = f"{command}_{int(time.time() * 1000)}"
            
            logger.info(f"📤 [COMMAND_RESULT] Sending {execution_source} command result: {command}")
            logger.debug(f"📤 [COMMAND_RESULT] Full payload: {json.dumps(response_message, indent=2, ensure_ascii=False)}")
            
            # Only use dedicated result endpoint (no message endpoint backup)
            direct_success = self.send_result_to_server(response_message)
            
            if direct_success:
                logger.info(f"✅ [COMMAND_RESULT] {execution_source} {command} result sent successfully")
                print(f"✅ {execution_source} result sent: {command}")
            else:
                logger.error(f"❌ [COMMAND_RESULT] Failed to send {execution_source} {command} result")
                print(f"❌ {execution_source} result failed: {command}")
                
        except Exception as e:
            logger.error(f"❌ [COMMAND_RESULT] Error sending {execution_source} command result for {command}: {e}")
            print(f"❌ {execution_source} result error: {command} - {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _send_http_command_result(self, command, result, client_id=None):
        """Send HTTP command execution result back to server (specifically for HTTP direct calls), avoid duplicate sending"""
        try:
            response_message = {
                'type': 'http_command_result',
                'command_executed': command,
                'result': result,
                'response': result,  # Add server-required response field
                'execution_source': 'HTTP',
                'client_id': client_id or self.client_id,
                'timestamp': time.time(),
                'success': result.get('success', True) if isinstance(result, dict) else True
            }
            
            # Extract error information from result if present
            if isinstance(result, dict) and 'error' in result:
                response_message['error'] = result['error']
                response_message['success'] = False
            
            logger.info(f"📤 [HTTP_RESULT] Sending HTTP command result: {command}")
            
            # Use dedicated result endpoint only (no message endpoint fallback)
            direct_success = self.send_result_to_server(response_message)
            
            if direct_success:
                logger.info(f"✅ [HTTP_RESULT] HTTP {command} result sent successfully")
                print(f"✅ HTTP result sent: {command}")
            else:
                logger.error(f"❌ [HTTP_RESULT] Failed to send HTTP {command} result")
                print(f"❌ HTTP result failed: {command}")
                
            return response_message if direct_success else None
                
        except Exception as e:
            logger.error(f"❌ [HTTP_RESULT] Error sending HTTP command result for {command}: {e}")
            print(f"❌ HTTP result error: {command} - {e}")
            return None
    
    def start(self):
        """Start MCP client"""
        if self.running:
            logger.warning("MCP Client is already running")
            return True
        
        # First start HTTP server
        try:
            if not self.http_server.start():
                logger.warning("Failed to start HTTP server, but continuing...")
                logger.warning("HTTP server failed to start")
        except Exception as e:
            logger.error(f"HTTP server startup error: {e}")
            print(f"❌ HTTP server error: {e}")
            
        # Try to register first
        try:
            registration_success = self.register()
            if not registration_success:
                logger.warning("Failed to register, but continuing to allow Django startup...")
                # Don't return False here - we want Django to start even if MCP fails
        except Exception as e:
            logger.error(f"Registration error: {e}")
            registration_success = False
            
        self.running = True
        
        # Only start SSE if registration was successful
        if registration_success:
            try:
                # Start SSE listening thread
                self.sse_thread = threading.Thread(
                    target=self.listen_sse, 
                    daemon=True,
                    name="MCP-SSE-Thread"
                )
                self.sse_thread.start()
                
                # Start heartbeat thread
                self.start_heartbeat()
                
                logger.info("MCP Client started successfully with HTTP server and heartbeat")
                print("✅ MCP Client: started with SSE and heartbeat")
            except Exception as e:
                logger.error(f"Failed to start SSE thread: {e}")
                print(f"⚠️ MCP Client: SSE failed")
        else:
            logger.info("MCP Client started without SSE (registration failed)")
            print("⚠️ MCP Client: started without SSE")
            
        return True  # Always return True to not block Django startup
        
    def stop(self):
        """Stop MCP client"""
        self.running = False
        
        # Stop heartbeat thread
        self.stop_heartbeat()
        
        # Stop SSE thread
        if self.sse_thread and self.sse_thread.is_alive():
            self.sse_thread.join(timeout=5)
            
        # Stop HTTP server
        if self.http_server:
            self.http_server.stop()
            
        logger.info("MCP Client stopped")
        print("MCP Client stopped")
    
    def send_heartbeat(self):
        """Send heartbeat message to server"""
        try:
            url = f"{self.server_url}/heartbeat"
            
            heartbeat_data = {
                "client_id": self.client_id,
                "client_ip": self.client_ip,  # 🔐 Add client IP
                "timestamp": time.time(),
                "status": "alive",
                "sse_connected": self.sse_connected,
                "http_server_running": self.http_server and self.http_server.running,
                "session_id": self.session_id  # 🔐 Add session_id if available
            }
            
            # Send heartbeat request
            response = requests.post(url, json=heartbeat_data, timeout=10)
            
            if response.status_code == 200:
                log_debug(f"💓 Heartbeat sent successfully")
                return True
            else:
                log_warning(f"💔 Heartbeat failed with status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            log_warning("💔 Heartbeat connection failed")
            return False
        except requests.exceptions.Timeout:
            log_warning("💔 Heartbeat timeout")
            return False
        except Exception as e:
            log_error(f"💔 Heartbeat error: {str(e)}")
            return False
    
    def _heartbeat_loop(self):
        """Heartbeat loop thread"""
        log_info(f"💓 Starting heartbeat thread (interval: {self.heartbeat_interval}s)")
        
        while self.heartbeat_running and self.running:
            try:
                # Send heartbeat
                success = self.send_heartbeat()
                
                if success:
                    log_debug(f"💓 Heartbeat sent at {time.strftime('%H:%M:%S')}")
                else:
                    log_warning(f"💔 Heartbeat failed at {time.strftime('%H:%M:%S')}")
                
                # Wait for next heartbeat interval
                for _ in range(self.heartbeat_interval):
                    if not self.heartbeat_running or not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                log_error(f"💔 Heartbeat thread error: {str(e)}")
                time.sleep(5)  # Short wait after error
        
        log_info("💓 Heartbeat thread terminated")
    
    def start_heartbeat(self):
        """Start heartbeat thread"""
        if self.heartbeat_running:
            log_warning("💓 Heartbeat is already running")
            return
            
        self.heartbeat_running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="MCP-Heartbeat-Thread"
        )
        self.heartbeat_thread.start()
        log_info("💓 Heartbeat thread started")
    
    def stop_heartbeat(self):
        """Stop heartbeat thread"""
        if not self.heartbeat_running:
            return
            
        self.heartbeat_running = False
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=3)
        log_info("💓 Heartbeat thread stopped")


class MCPMultiClient:
    """Multi-Server MCP Client Manager"""
    
    def __init__(self, server_configs=None):
        self.server_configs = server_configs or DEFAULT_SERVERS
        self.clients = {}
        self.running = False
        
    def add_server(self, name, base_url, client_id):
        """Add a new server configuration"""
        self.server_configs[name] = {
            "base_url": base_url,
            "client_id": client_id
        }
        logger.info(f"Added server configuration: {name} -> {base_url}")
        
    def start_all(self):
        """Start all MCP clients"""
        success_count = 0
        total_count = len(self.server_configs)
        
        logger.info(f"Starting {total_count} MCP client connections...")
        
        for server_name, config in self.server_configs.items():
            try:
                logger.info(f"Starting client for server: {server_name}")
                client = MCPClient(
                    server_url=config['base_url'],
                    client_id=config['client_id']
                )
                self.clients[server_name] = client
                
                # Start individual client
                if client.start():
                    success_count += 1
                    logger.info(f"Successfully started client for {server_name}")
                else:
                    logger.warning(f"Failed to start client for {server_name}")
                    
            except Exception as e:
                logger.error(f"Exception starting client for {server_name}: {e}")
                
        self.running = True
        
        # Always return True to not block Django - log results instead
        logger.info(f"MCP Multi-Client startup complete: {success_count}/{total_count} clients started")
        print(f"✅ MCP: {success_count}/{total_count} clients started")
        
        return True  # Always return True to not block Django startup
        
    def stop_all(self):
        """Stop all MCP clients"""
        for server_name, client in self.clients.items():
            try:
                client.stop()
                logger.info(f"Stopped client for {server_name}")
            except Exception as e:
                logger.error(f"Error stopping client for {server_name}: {e}")
                
        self.clients.clear()
        self.running = False
        logger.info("All MCP clients stopped")
        
    def send_message_to_all(self, message):
        """Send message to all connected servers"""
        results = {}
        for server_name, client in self.clients.items():
            try:
                if client.running:
                    result = client.send_message(message)
                    results[server_name] = result
                else:
                    results[server_name] = False
                    logger.warning(f"Client for {server_name} is not running")
            except Exception as e:
                logger.error(f"Failed to send message to {server_name}: {e}")
                results[server_name] = False
                
        return results
        
    def send_message_to_server(self, server_name, message):
        """Send message to specific server"""
        if server_name not in self.clients:
            logger.error(f"Server {server_name} not found")
            return False
            
        client = self.clients[server_name]
        if not client.running:
            logger.warning(f"Client for {server_name} is not running")
            return False
            
        return client.send_message(message)
        
    def get_status(self):
        """Get status of all clients"""
        status = {}
        for server_name, client in self.clients.items():
            status[server_name] = {
                "running": client.running,
                "server_url": client.server_url,
                "client_id": client.client_id
            }
        return status


# Global client instances
_mcp_client = None
_mcp_multi_client = None


def get_mcp_client():
    """Get MCP client instance (single server)"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


def get_mcp_multi_client():
    """Get MCP multi-client instance (multi-server)"""
    global _mcp_multi_client
    if _mcp_multi_client is None:
        _mcp_multi_client = MCPMultiClient()
    return _mcp_multi_client


def start_mcp_client(use_multi_server=True):
    """Start MCP client (called when Django app starts)"""
    global _client_running
    if _client_running:
        return True
        
    try:
        if use_multi_server:
            # Use multi-server client
            multi_client = get_mcp_multi_client()
            
            # Add additional servers if needed
            # multi_client.add_server("backup", "http://10.140.217.48:8000", "wrs_client_backup")
            
            if multi_client.start_all():
                _client_running = True
                logger.info("MCP Multi-Client auto-started")
                return True
            else:
                logger.warning("MCP Multi-Client started with some failures")
                _client_running = True  # Still mark as running even with partial failures
                return True
        else:
            # Use single server client
            client = get_mcp_client()
            if client.start():
                _client_running = True
                logger.info("MCP Client auto-started")
                return True
            else:
                logger.warning("MCP Client startup failed")
                return True  # Don't block Django startup
                
    except Exception as e:
        logger.error(f"Exception during MCP client startup: {e}")
        return True  # Don't block Django startup


def stop_mcp_client():
    """Stop MCP client"""
    global _client_running, _mcp_client, _mcp_multi_client
    if not _client_running:
        return
        
    try:
        # Stop multi-client if exists
        if _mcp_multi_client:
            _mcp_multi_client.stop_all()
            
        # Stop single client if exists
        if _mcp_client:
            _mcp_client.stop()
            
        _client_running = False
        logger.info("All MCP clients stopped")
        
    except Exception as e:
        logger.error(f"Error stopping MCP clients: {e}")


def send_message_to_server(message, server_name=None):
    """Convenient function to send message to server(s)"""
    global _mcp_multi_client, _mcp_client
    
    # Try multi-client first
    if _mcp_multi_client and _mcp_multi_client.running:
        if server_name:
            return _mcp_multi_client.send_message_to_server(server_name, message)
        else:
            return _mcp_multi_client.send_message_to_all(message)
    
    # Fallback to single client
    elif _mcp_client and _mcp_client.running:
        return _mcp_client.send_message(message)
    
    else:
        logger.warning("No MCP client is running")
        return False


def get_mcp_status():
    """Get status of all MCP clients"""
    global _mcp_multi_client, _mcp_client
    
    status = {
        "multi_client_running": False,
        "single_client_running": False,
        "servers": {},
        "overall_running": _client_running
    }
    
    # Check multi-client status
    if _mcp_multi_client:
        status["multi_client_running"] = _mcp_multi_client.running
        status["servers"] = _mcp_multi_client.get_status()
    
    # Check single client status
    if _mcp_client:
        status["single_client_running"] = _mcp_client.running
        if _mcp_client.running:
            status["servers"]["single"] = {
                "running": _mcp_client.running,
                "server_url": _mcp_client.server_url,
                "client_id": _mcp_client.client_id
            }
    
    return status


# Keep original functions for compatibility with existing code
def register():
    """Register client to server"""
    client = get_mcp_client()
    return client.register()


def send_message(msg):
    """Send message to server"""
    client = get_mcp_client()
    return client.send_message(msg)


def listen_sse():
    """Listen to server-sent events"""
    client = get_mcp_client()
    client.listen_sse()


if __name__ == "__main__":
    
    print("🚀 Starting MCP Client...")
    print("=" * 50)
    
    try:
        
        client = MCPClient()
        
        print(f"✅ Client ID: {client.client_id}")
        print(f"✅ Server URL: {client.server_url}")
        print(f"✅ HTTP Port: {client.http_port}")
        
        
        print("\n� Starting MCP Client...")
        if client.start():
            print("✅ MCP Client started successfully!")
            
            try:
                
                print("\n� MCP Client is running... Press Ctrl+C to stop")
                while client.running:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping MCP Client...")
                client.stop()
                print("✅ MCP Client stopped successfully!")
                
        else:
            print("❌ Failed to start MCP Client")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()