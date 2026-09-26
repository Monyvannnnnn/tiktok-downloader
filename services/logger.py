from collections import deque
from datetime import datetime, timezone

recent_logs = deque(maxlen=200)


def log_activity(text: str):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    recent_logs.appendleft({"time": timestamp, "text": text})
    print(f"[{timestamp}] {text}")
