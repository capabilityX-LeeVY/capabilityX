# Debug Tools - Remote Stress Test Guide

This folder contains tools for remotely triggering Webex stress tests via a simple web interface.

## 🚀 Quick Start (Recommended Method)

### Step 1: Start the API Server on Target Machine

On the machine where you want to run the stress test:

```bash
# Navigate to the project root
cd D:\code\wrs\webex-regress-shield

# Activate virtual environment
.venv\Scripts\activate

# Start the API server
python src/functions/api/server.py
```

The API server will start on port 9909.

### Step 2: Open the Web Interface

Simply open `stress_test_web_ui.html` in any web browser - **no additional server needed!**

You can:
- Copy the HTML file to any computer
- Open it directly from a file share
- Host it on any web server
- Use it locally or remotely

### Step 3: Configure Remote Connection

1. In the **Remote Server Configuration** section, enter the API server address:
   - For local testing: `localhost:9909`
   - For remote testing: `192.168.1.100:9909` (replace with actual IP)
   
2. Click **🔗 Test Connection** to verify connectivity

3. Configure your stress test parameters

4. Click **🚀 Start Stress Test**

## 🌐 Remote Access Examples

### Same Network
```
API Server IP: 192.168.1.100:9909
```

### Different Network (with port forwarding)
```  
API Server IP: company.example.com:9909
```

### VPN Connection
```
API Server IP: 10.0.0.50:9909
```

## 📊 Parameters Explained

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Remote Server** | string | localhost:9909 | IP:Port of the API server |
| **Stress Duration** | select | 180s (3 min) | Test duration (3/10/30/60 minutes) |
| **Participants** | select | 20 | Number of participants (20/30/50/100) |
| **Custom Message** | string | - | Custom message for testing |
| **Enable Video** | boolean | true | Enable video during test |
| **Enable Audio** | boolean | false | Enable audio during test |
| **Platform** | select | windows | Target platform |

## 🔧 Complete Workflow

The web interface triggers a complete test workflow:

1. **✅ Test Execution**: Runs stress test with your parameters
2. **🔍 Screen Reader Analysis**: AI accessibility analysis (if enabled)
3. **📈 Performance Analysis**: System performance metrics (if enabled)  
4. **🎯 Focus Ring Detection**: UI focus indicator validation
5. **☁️ Result Upload**: Uploads results to wrs.qa.webex.com
6. **📢 Notification**: Sends notification with test summary

## 📁 Files in This Directory

| File | Purpose |
|------|---------|
| **`stress_test_web_ui.html`** | **🌟 Main web interface - open this file!** |
| `call_stress_api_with_params.py` | Example Python script for API calls |
| `README.md` | This documentation |
| `run_*.bat` | Various test sequence batch files |
| `run_test_case_debug.py` | Debug script for test cases |

## 🛠️ Advanced Integration

For programmatic access, you can still use direct API calls:

### Example: Python Integration
```python
import requests

def run_remote_stress_test(server_ip, duration=180, participants=20):
    url = f"http://{server_ip}/api/run_stress_test"
    payload = {
        "stress_duration": duration,
        "participant_count": participants,
        "enable_video": True,
        "custom_message": f"Remote test - {participants} participants"
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Usage
result = run_remote_stress_test("192.168.1.100:9909", 300, 25)
print(f"Test completed: {result['result_url']}")
```

### Example: PowerShell Integration
```powershell
$serverIp = "192.168.1.100:9909"
$body = @{
    stress_duration = 240
    participant_count = 15
    enable_video = $true
    custom_message = "PowerShell remote test"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://$serverIp/api/run_stress_test" `
                              -Method Post `
                              -Body $body `
                              -ContentType "application/json"

Write-Host "Test URL: $($response.result_url)"
```

## 🆘 Troubleshooting

### Connection Issues
- **Can't connect**: Check firewall on target machine (port 9909)
- **API server not responding**: Verify server is running with `python src/functions/api/server.py`
- **Wrong IP**: Use `ipconfig` (Windows) or `ifconfig` (Mac/Linux) to find correct IP

### Test Execution Issues
- **Webex not installed**: Ensure Webex is installed on target machine
- **Account issues**: Check credentials in `src/config/account.json`
- **Network problems**: Verify target machine has internet access

### Results Not Uploading
- **Upload disabled**: Check feature toggles in project settings
- **Network access**: Verify target machine can reach wrs.qa.webex.com
- **Check logs**: Review logs in `src/logs/` on target machine

## 📝 Summary

**The easiest way to run remote stress tests:**

1. ✅ Start API server on target machine: `python src/functions/api/server.py`
2. ✅ Open `stress_test_web_ui.html` in any web browser (anywhere)
3. ✅ Enter target machine IP address
4. ✅ Test connection and run stress test
5. ✅ Get results URL automatically

**No additional setup needed!** The HTML file works standalone and can be used from anywhere to control remote stress tests.

---

**Note**: This approach provides the simplest way to remotely trigger stress tests - just one HTML file and one API server.
