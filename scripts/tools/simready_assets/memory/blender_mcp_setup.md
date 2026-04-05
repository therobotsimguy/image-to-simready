---
name: Blender MCP Setup
description: How to connect Claude Code to Blender — startup order matters, direct socket is most reliable
type: reference
---

## Startup Order (MUST follow this sequence)
1. Open Blender
2. Verify MCP addon is active: Edit → Preferences → Add-ons → search "MCP" → should be checked
3. Check Blender's terminal shows: "MCP Server started on port 9876"
4. THEN start Claude Code

## Connection Method: Direct Socket (most reliable)
The MCP tool integration is flaky — tools don't always show up after restart.
Use direct socket instead (works every time if Blender is running):

```python
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(30)
sock.connect(('localhost', 9876))
cmd = json.dumps({"type": "execute_code", "params": {"code": "<blender python>"}})
sock.sendall(cmd.encode('utf-8'))
# read response...
```

## Quick Test (run this to check connection)
```bash
python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost',9876)); print('Blender MCP OK'); s.close()"
```

## If connection fails
- Is Blender open? Check taskbar
- Is MCP addon enabled? Edit → Preferences → Add-ons → "MCP"
- Is port 9876 in use? `lsof -i :9876`
- Restart Blender, re-enable addon if needed

## Config file
`.claude/settings.local.json` has mcpServers.blender configured but this only helps if MCP tools load properly. Direct socket bypasses this entirely.
