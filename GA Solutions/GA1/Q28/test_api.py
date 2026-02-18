#!/usr/bin/env python3
"""Test script for the streaming LLM API"""

import requests
import json
import sys

def test_streaming_api():
    """Test the streaming endpoint"""
    url = "http://localhost:8080/v1/chat/completions"
    
    payload = {
        "prompt": "Explain how streaming APIs improve user experience",
        "stream": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing Streaming LLM API")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)
    print("\nStreaming Response:\n")
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            chunk_count = 0
            total_chars = 0
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8') if isinstance(line, bytes) else line
                    if line.startswith('data: '):
                        chunk_count += 1
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            print("\n✅ Stream completed successfully!")
                        else:
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and data['choices']:
                                    content = data['choices'][0]['delta'].get('content', '')
                                    print(content, end='', flush=True)
                                    total_chars += len(content)
                            except json.JSONDecodeError:
                                print(f"\n[Error parsing JSON]: {data_str}")
            
            print(f"\n\n{'=' * 60}")
            print(f"Statistics:")
            print(f"  Total chunks: {chunk_count}")
            print(f"  Total characters: {total_chars}")
            print(f"  Status code: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print("=" * 60)
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server at http://localhost:8080")
        print("Make sure the server is running with: python src/app.py")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_streaming_api()
