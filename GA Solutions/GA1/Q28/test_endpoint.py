import urllib.request
import json

print("=" * 80)
print("TESTING CURL EQUIVALENT:")
print("curl -X POST http://localhost:8080/v1/chat/completions")
print('  -H "Content-Type: application/json"')
print('  -d \'{"prompt": "Explain streaming APIs", "stream": true}\'')
print("=" * 80)

url = 'http://localhost:8080/v1/chat/completions'
payload = {"prompt": "Explain streaming APIs", "stream": True}
data = json.dumps(payload).encode('utf-8')

req = urllib.request.Request(
    url,
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"\nHTTP/1.1 {response.status} {response.reason}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Transfer-Encoding: chunked")
        print("\n" + "-" * 80)
        print("RESPONSE BODY:\n")
        
        line_count = 0
        for line in response:
            decoded_line = line.decode('utf-8').strip()
            if decoded_line:
                print(decoded_line)
                line_count += 1
                if line_count >= 12:
                    print("\n... (additional streaming chunks) ...\n")
                    break
                    
        print("-" * 80)
        print(f"\nResponse completed successfully with {line_count}+ streaming chunks")
        
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
