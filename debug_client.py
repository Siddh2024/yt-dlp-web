import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:5000"

def test_index():
    print("Testing GET / ...")
    try:
        with urllib.request.urlopen(BASE_URL, timeout=5) as response:
            print(f"Status: {response.getcode()}")
            content = response.read()
            print(f"Content Length: {len(content)}")
            print(f"Preview: {content[:100]}...")
    except Exception as e:
        print(f"Failed to get index: {e}")

def test_download_flow():
    print("\nTesting POST /download ...")
    url = "https://youtu.be/xztfsYDM5HM"
    payload = json.dumps({"url": url, "format": "best"}).encode('utf-8')
    
    req = urllib.request.Request(f"{BASE_URL}/download", data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Status: {response.getcode()}")
            print(f"Headers: {response.info()}")
            resp_body = response.read().decode('utf-8')
            print(f"Response: {resp_body}")
            
            if response.getcode() != 200:
                print("Download start failed.")
                return

        print("\nConnecting to /progress ...")
        # Streaming request
        req_progress = urllib.request.Request(f"{BASE_URL}/progress")
        with urllib.request.urlopen(req_progress, timeout=60) as response:
            print("Connected to SSE stream.")
            for line in response:
                line = line.decode('utf-8').strip()
                if not line: continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    print(f"SSE Event: {data_str}")
                    try:
                        data = json.loads(data_str)
                        if data.get('status') in ['finished', 'error']:
                            print("Finished stream.")
                            break
                    except:
                        pass
                
    except Exception as e:
        print(f"Flow failed: {e}")

if __name__ == "__main__":
    test_index()
    test_download_flow()
