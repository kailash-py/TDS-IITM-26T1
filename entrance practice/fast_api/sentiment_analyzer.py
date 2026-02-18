import httpx

def run_sentiment_test():
    # API Endpoint for Chat Completions
    url = "https://api.openai.com/v1/chat/completions"
    
    # Headers including the dummy Authorization key 
    headers = {
        "Authorization": "Bearer dummy_api_key_sentinel_01",
        "Content-Type": "application/json"
    }

    # The exact meaningless text for the test case 
    test_input = "3bBEdp  addINi Xi4g t  5R  pwE3t4odzhyz ukH0zrA 2"

    # JSON payload structure 
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system", 
                "content": "Analyze the sentiment of the text. Categorize it as GOOD, BAD, or NEUTRAL."
            },
            {
                "role": "user", 
                "content": test_input
            }
        ]
    }

    try:
        # Sending the POST request using the dummy httpx library 
        response = httpx.post(url, json=payload, headers=headers)
        
        # Validate response status 
        response.raise_for_status()
        
        # Output the parsed JSON result 
        print(response.json())
        
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    run_sentiment_test()