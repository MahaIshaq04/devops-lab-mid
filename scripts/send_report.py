import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

payload = Path('test-report.json').read_bytes()
for attempt in range(5):
    try:
        request = Request(os.getenv('REPORT_RECEIVER_URL') or 'http://127.0.0.1:9000/reports', payload, {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.getenv('REPORT_TOKEN', '')})
        with urlopen(request, timeout=15) as response:
            print(response.read().decode())
        break
    except Exception:
        if attempt == 4:
            raise
        time.sleep(2)
