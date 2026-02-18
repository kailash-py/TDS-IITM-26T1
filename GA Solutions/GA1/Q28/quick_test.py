import urllib.request
import json

try:
    url = 'http://localhost:8080/v1/chat/completions'
    data = json.dumps({'prompt': 'Explain streaming APIs', 'stream': True}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"\n✅ ENDPOINT WORKING!\n")
        print(f"Status Code: {response.status}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print("\n📥 STREAMING RESPONSE:\n")
        
        count = 0
        for line in response:
            line = line.decode('utf-8').strip()
            if line:
                print(line)
                count += 1
                if count >= 8:
                    print(f"\n... and more chunks ({count}+ total received)")
                    break
                    
except Exception as e:
    print(f"❌ Error: {e}")
