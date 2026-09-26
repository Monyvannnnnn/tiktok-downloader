import json
import asyncio
from config import PORT
from services.logger import recent_logs, log_activity


async def handle_health_check(reader, writer):
    try:
        request_line = await reader.readline()
        while True:
            header_line = await reader.readline()
            if not header_line or header_line == b"\r\n":
                break

        req_str = request_line.decode("utf-8", errors="ignore")
        if "/api/logs" in req_str:
            body = json.dumps(list(recent_logs)).encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        else:
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrollSaver - Live Activity Log</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 18px 24px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .title { font-size: 18px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(35, 134, 54, 0.15);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.3);
            font-size: 13px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
        }
        .dot { width: 8px; height: 8px; background: #3fb950; border-radius: 50%; animation: pulse 1.8s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        .card-header {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
            font-weight: 600;
            color: #8b949e;
            display: flex;
            justify-content: space-between;
        }
        .logs-container {
            max-height: 550px;
            overflow-y: auto;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            padding: 8px;
        }
        .log-item {
            display: flex;
            gap: 14px;
            padding: 8px 12px;
            border-radius: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            word-break: break-all;
        }
        .log-item:hover { background: rgba(255, 255, 255, 0.04); }
        .log-time { color: var(--text-muted); flex-shrink: 0; font-size: 12px; }
        .log-text { color: #e6edf3; flex-grow: 1; }
        .empty-state { text-align: center; padding: 40px; color: var(--text-muted); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🤖 ScrollSaver Live Terminal Dashboard</div>
            <div class="badge"><span class="dot"></span> Bot Active</div>
        </div>
        <div class="card">
            <div class="card-header">
                <span>Live Activity Stream</span>
                <span>Auto-refreshing every 2s</span>
            </div>
            <div class="logs-container" id="logs-list">
                <div class="empty-state">Loading activity logs...</div>
            </div>
        </div>
    </div>
    <script>
        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const logs = await res.json();
                const container = document.getElementById('logs-list');
                if (!logs || logs.length === 0) {
                    container.innerHTML = '<div class="empty-state">No activity logged yet. Send /start or a TikTok link in Telegram!</div>';
                    return;
                }
                container.innerHTML = logs.map(item => `
                    <div class="log-item">
                        <span class="log-time">[${item.time} UTC]</span>
                        <span class="log-text">${escapeHtml(item.text)}</span>
                    </div>
                `).join('');
            } catch (err) {
                console.error("Fetch error:", err);
            }
        }
        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }
        fetchLogs();
        setInterval(fetchLogs, 2000);
    </script>
</body>
</html>"""
            body = html_content.encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        await writer.drain()
    except Exception as e:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_web_server():
    try:
        await asyncio.start_server(handle_health_check, "0.0.0.0", PORT)
        log_activity(f"HTTP health server started on port {PORT}")
    except Exception as e:
        log_activity(f"Port binding note: {e}")
