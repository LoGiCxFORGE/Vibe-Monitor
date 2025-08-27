import requests
import time

url = "http://localhost:8000/hello"

for i in range(100):  # total 100 requests
    try:
        r = requests.get(url)
        print(f"{i+1}: {r.status_code} {r.json()}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.01)  # 50ms between requests
