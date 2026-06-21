# TEST_PLATFORM_REGISTRTION_AND_USAGE

Guide for running a test suite from the WRS test platform and handling common runtime issues.

## Access the Platform

1. Open: <https://wrs.qa.webex.com/>
2. Enter your email address.
3. Click **Sign In**.

## Run a Test Suite

1. Under **TEST SUITE**, select the suite you want to run (example: `video_vbg`).
   - Currently, only run test suite is supported.
2. Click **Open VM Management**.
3. Select a VM (example: `wrs-agent-gt01`).
4. Click **Allocate VM** under **VM Operations**.
   - After allocation, the VM is connected and the connected UI is available.
5. Click the green **Run** button.
6. The test suite starts running.
   - You can monitor job status directly in the platform UI.

## After Execution

1. After the suite finished, open the **View Report** link in the AI Assistant panel (right side).
2. Release the VM when done:
   - Select the VM (example: `wrs-agent-gt01`).
   - Click **Release VM**.

## Notes

1. The platform currently supports **Run Test Suite** only.
   - Running individual test cases is not supported.
   - Uploading ACC is not supported.
2. During suite execution, select only the target **TEST SUITE**.
   - Other options do not need to be selected.

## Troubleshooting

### Error: No MCP client found

If clicking **Run** shows an MCP error such as:

```text
No MCP client found for VM wrs-agent-gt01.qa.webex.com
```

perform the following on that VM:

1. Pull latest code:

```bash
git pull origin main
```

1. Restart MCP client manager:

Windows example:

```bat
cd C:\dev\webex-regress-shield
python src\functions\mcp\mcp_client_manager.py
```

1. Verify successful restart in logs. If you see both messages below, MCP client recovery is successful:

```text
Heartbeat sent successfully
SSE connection established
```
