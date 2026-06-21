#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP API Client - Receive remote calls
"""

from flask import Flask, request, jsonify
import os
import sys
import requests
import threading

# Add project src path so that 'core', 'config', etc. can be imported
current_file_dir = os.path.dirname(os.path.abspath(__file__))
# D:\code\WebexRegressSheild\src\functions\mcp -> up 2 levels -> D:\code\WebexRegressSheild\src
src_dir = os.path.dirname(os.path.dirname(current_file_dir))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.managers.bug_verifier_manager import BugVerifier

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "service": "WebexRegressSheild Simple API Client"
    })


@app.route('/execute', methods=['POST'])
def execute():
    """
    Execute test task
    
    POST /execute
    {
        "test_suite": "smoke",
        "platform": "windows",
        "other_params": {...}
    }
    """
    try:
        data = request.get_json()
        test_suite = data.get('test_suite')
        platform = data.get('platform', 'windows')
        other_params = data.get('other_params', {})
        
        print(f"📨 Received execution request:")
        print(f"   Test Suite: {test_suite}")
        print(f"   Platform: {platform}")
        print(f"   Other Params: {other_params}")
        
        # Import and execute test
        from run_test_case_job import TestCaseJobRunner
        import pythoncom
        
        pythoncom.CoInitialize()
        try:
            runner = TestCaseJobRunner()
            result = runner.run_complete_workflow_with_ui_response(
                test_suite=test_suite,
                pramas={"platform": platform},
                return_report_url=True
            )
            
            return jsonify({
                "success": True,
                "result": result,
                "message": f"Test suite '{test_suite}' executed successfully"
            })
            
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"❌ Execution error: {error_msg}")
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_msg
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """Check status"""
    import platform
    import socket
    
    return jsonify({
        "hostname": platform.node(),
        "platform": platform.platform(),
        "local_ip": socket.gethostbyname(socket.gethostname()),
        "status": "running"
    })


@app.route('/execute_command', methods=['POST'])
def execute_command():
    """
    Receive MCP format command message
    
    POST /execute_command
    {
        "command": "send_message",
        "params": {
            "message": "message content",
            "message_type": "info|warning|error|success",
            "client_id": "target client ID"
        }
    }
    """
    try:
        data = request.get_json()
        command = data.get('command')
        params = data.get('params', {})
        
        print(f"📨 Received MCP command:")
        print(f"   Command: {command}")
        print(f"   Params: {params}")
        
        # Handle different commands
        if command == 'test_message':
            message = params.get('message', '')
            message_type = params.get('message_type', 'info')
            
            # Select emoji based on message type
            emoji_map = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'success': '✅'
            }
            emoji = emoji_map.get(message_type, '💬')
            
            print(f"\n{emoji} [{message_type.upper()}] Received Message:")
            print(message)
            print()
            
            # Try to parse test_suite, test_case, test_step from message
            import re
            test_info = {}
            
            # Parse test_suite
            suite_match = re.search(r'test_suite:\s*(.+)', message)
            if suite_match:
                test_info['test_suite'] = suite_match.group(1).strip()
            
            # Parse test_case
            case_match = re.search(r'test_case:\s*(.+)', message)
            if case_match:
                test_info['test_case'] = case_match.group(1).strip()
            
            # Parse test_step
            step_match = re.search(r'test_step:\s*(\d+)', message)
            if step_match:
                test_info['test_step'] = step_match.group(1).strip()
            
            # Parse JIRA ID
            jira_match = re.search(r'Bug ID:\s*(SPARK-\d+)', message)
            if jira_match:
                test_info['jira_id'] = jira_match.group(1).strip()
            
            if test_info:
                print(f"📊 Parsed Test Information:")
                for key, value in test_info.items():
                    print(f"   {key}: {value}")
                print()
            
            return jsonify({
                "success": True,
                "message": "Message received and parsed",
                "command": command,
                "parsed_info": test_info
            })
            
        elif command == 'execute_workflow':
            # Execute test workflow
            test_suite = params.get('test_suite')
            platform_param = params.get('platform', 'windows')
            
            # If test_suite is not directly provided, try to parse from message
            test_case = None
            test_step = None
            bug_type = None
            bug_id = None
            
            message = params.get('message', '')
            if message:
                import re
                # Parse test_suite
                suite_match = re.search(r'test_suite:\s*(.+)', message)
                if suite_match:
                    test_suite = suite_match.group(1).strip()
                    print(f"📊 Parsed test_suite from message: {test_suite}")
                
                # Parse test_case
                case_match = re.search(r'test_case:\s*(.+)', message)
                if case_match:
                    test_case = case_match.group(1).strip()
                    print(f"📊 Parsed test_case from message: {test_case}")

                # Parse test_step
                step_match = re.search(r'test_step:\s*(\d+)', message)
                if step_match:
                    test_step = step_match.group(1).strip()
                    print(f"📊 Parsed test_step from message: {test_step}")
                
                # Parse bug_type (type)
                bug_type_match = re.search(r'Type:\s*(.+)', message)
                if bug_type_match:
                    bug_type = bug_type_match.group(1).strip()
                    print(f"📊 Parsed bug_type from message: {bug_type}")
                
                # Parse bug_id (JIRA ID)
                bug_id_match = re.search(r'JIRA ID:\s*(SPARK-\d+|WBX-\d+)', message, re.IGNORECASE)
                if bug_id_match:
                    bug_id = bug_id_match.group(1).strip()
                    print(f"📊 Parsed bug_id from message: {bug_id}")
                
                # Parse platform
                platform_match = re.search(r'platform:\s*(.+)', message)
                if platform_match:
                    platform_param = platform_match.group(1).strip()
                    print(f"📊 Parsed platform from message: {platform_param}")
            
            if not test_suite:
                return jsonify({
                    "success": False,
                    "error": "test_suite is required (either in params or in message)"
                }), 400
            
            print(f"🚀 Executing workflow: {test_suite} on {platform_param}")
            
            # Define background task function
            def execute_workflow_task():
                """Execute workflow in background and callback"""
                # Prefer callback_url from params; fall back to default if not provided
                callback_url = params.get('callback_url') or "http://10.140.217.58:9913/jira/mcp_callback"
                
                try:
                    from run_test_case_job import TestCaseJobRunner
                    import pythoncom
                    
                    pythoncom.CoInitialize()
                    try:
                        runner = TestCaseJobRunner()
                        result = runner.run_complete_workflow_with_ui_response(
                            test_suite=test_suite,
                            pramas={"platform": platform_param},
                            return_report_url=True
                        )
                        
                        # Extract report_url
                        report_url = None
                        if isinstance(result, tuple) and len(result) == 2:
                            main_result, report_url = result
                        elif isinstance(result, str):
                            report_url = result
                        elif isinstance(result, dict):
                            report_url = result.get('report_url') or result.get('url')
                        
                        print(f"✅ Workflow executed successfully!")
                        print(f"   Report URL: {report_url}")
                        
                        # If report_url and complete verification parameters exist, call verify_bug
                        verification_result = None
                        if report_url and test_suite and test_case and test_step and bug_type:
                            print(f"\n🔍 Starting bug verification...")
                            print(f"   Test Suite: {test_suite}")
                            print(f"   Test Case: {test_case}")
                            print(f"   Test Step: {test_step}")
                            print(f"   Bug Type: {bug_type}")
                            print(f"   Report URL: {report_url}")
                            
                            try:
                                verifier = BugVerifier(report_url)
                                is_verified = verifier.verify_bug(
                                    test_suite=test_suite,
                                    test_case=test_case,
                                    test_step=test_step,
                                    bug_type=bug_type,
                                    jira_id=bug_id
                                )
                                verification_result = is_verified
                                print(f"\n{'✅' if is_verified else '❌'} Bug verification {'passed' if is_verified else 'failed'}!")
                            except Exception as e:
                                print(f"\n⚠️ Bug verification error: {str(e)}")
                                verification_result = False
                        else:
                            if report_url:
                                missing = []
                                if not test_case: missing.append('test_case')
                                if not test_step: missing.append('test_step')
                                if not bug_type: missing.append('bug_type')
                                print(f"\n⚠️ Skipping bug verification - missing parameters: {', '.join(missing)}")
                        
                        # ✅ After test completes, send callback
                        print(f"\n📤 Sending callback to {callback_url}...")
                        try:
                            requests.post(
                                callback_url,
                                json={
                                    'jira_id': bug_id,
                                    'success': True,
                                    'verification': verification_result,
                                    'report_url': report_url,
                                    'test_suite': test_suite,
                                    'test_case': test_case,
                                    'test_step': test_step,
                                    'bug_type': bug_type,
                                    'message': 'Test completed successfully'
                                },
                                timeout=10
                            )
                            print(f"✅ Callback sent successfully")
                        except Exception as callback_error:
                            # Log callback failure but do not treat it as workflow failure
                            print(f"⚠️ Failed to send success callback: {str(callback_error)}")
                        
                    finally:
                        pythoncom.CoUninitialize()
                        
                except Exception as e:
                    # ❌ Send callback even on failure
                    import traceback
                    error_msg = traceback.format_exc()
                    print(f"\n❌ Workflow execution error: {error_msg}")
                    
                    try:
                        print(f"\n📤 Sending error callback to {callback_url}...")
                        requests.post(
                            callback_url,
                            json={
                                'jira_id': bug_id,
                                'success': False,
                                'verification': False,
                                'error': str(e),
                                'traceback': error_msg,
                                'message': 'Test execution failed'
                            },
                            timeout=10
                        )
                        print(f"✅ Error callback sent successfully")
                    except Exception as callback_error:
                        print(f"❌ Failed to send error callback: {str(callback_error)}")
            
            # Start background thread to execute workflow
            thread = threading.Thread(target=execute_workflow_task, daemon=True)
            thread.start()
            
            # Return immediately without waiting for execution to complete
            return jsonify({
                "success": True,
                "status": "accepted",
                "message": f"Workflow '{test_suite}' started in background. Results will be sent to callback URL.",
                "test_suite": test_suite,
                "jira_id": bug_id
            }), 202
        
        else:
            return jsonify({
                "success": False,
            }), 400
            
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"❌ Command execution error: {error_msg}")
        
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": error_msg
        }), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple API Client')
    parser.add_argument('--port', type=int, default=9000, help='Port to listen on')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Simple HTTP API Client Starting...")
    print("=" * 60)
    print(f"📡 Listening on: http://0.0.0.0:{args.port}")
    print(f"📝 Endpoints:")
    print(f"   GET  /health  - Health check")
    print(f"   GET  /status  - System status")
    print(f"   POST /execute - Execute test suite")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=args.port, debug=False)
