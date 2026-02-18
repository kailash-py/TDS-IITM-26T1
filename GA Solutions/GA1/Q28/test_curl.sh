#!/bin/bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain streaming APIs", "stream": true}'
