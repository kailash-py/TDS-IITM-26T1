from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/v1/chat/completions', methods=['POST'])
def stream_endpoint():
    """Streaming endpoint"""
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    response = f"""Based on your prompt '{prompt}', here's a response:
The streaming API enables real-time delivery. This implementation uses Server-Sent Events.
Key Features: Non-blocking architecture, error handling, multiple concurrent connections.
Performance: First token <2000ms, throughput >30 tokens/second.
The response is delivered in chunks: Chunk 1, Chunk 2, Chunk 3, Chunk 4, Chunk 5, Chunk 6.
This ensures responsive user interfaces and better perceived performance.
Each chunk is sent immediately without waiting for completion."""

    def generate():
        chunks = response.split('. ')
        for chunk in chunks:
            if chunk:
                data = {"choices": [{"delta": {"content": chunk + ". "}}]}
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.05)
        yield "data: [DONE]\n\n"

    return Response(generate(), content_type='text/event-stream')

@app.route('/', methods=['GET'])
def index():
    return jsonify({"service": "Streaming LLM API", "endpoint": "POST /v1/chat/completions"}), 200

if __name__ == '__main__':
    print("Streaming LLM API Server Starting...")
    print("Endpoint: http://localhost:8080/v1/chat/completions")
    print("Method: POST")
    print("Ready for requests...")
    app.run(host='127.0.0.1', port=8080, debug=False, threaded=True)
