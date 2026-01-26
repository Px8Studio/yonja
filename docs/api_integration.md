# ALİM API Integration Guide

This guide describes how to integrate with the ALİM backend using standardized HTTP/SSE protocols.

## Overview

Third-party applications connect to ALİM via the FastAPI layer, which securely proxies requests to the LangGraph execution engine. This ensures:
1.  **Security**: All requests are authenticated.
2.  **Scalability**: Async handling without blocking.
3.  **Simplicity**: Standard REST + SSE (no complex WebSocket state management).

## Authentication

All `graph` endpoints require an API Key.

**Header**: `X-API-Key`  
**Value**: `dev-api-key-change-in-production` (Default for dev)

> [!IMPORTANT]
> In production, obtain your specific API Key from the administrator.

## Endpoints

### 1. Synchronous Invoke
Send a message and wait for the full response. Good for simple query-response interactions.

- **URL**: `POST /api/v1/graph/invoke`
- **Content-Type**: `application/json`

**Payload**:
```json
{
  "message": "Fermada susuzluq var, nə edim?",
  "user_id": "partner_app_user_123",
  "thread_id": "optional-uuid" 
}
```

**Response**:
```json
{
  "response": "Suvarmalı...",
  "thread_id": "uuid-of-thread",
  "model": "llama-3.3-70b-versatile"
}
```

### 2. Real-time Streaming (SSE)
Receive tokens as they are generated. Essential for "ChatGPT-like" typing effects.

- **URL**: `POST /api/v1/graph/stream`
- **Content-Type**: `application/json`
- **Accept**: `text/event-stream`

**Payload**: same as Invoke.

**Events**:
- `event: token` -> `data: <text_chunk>`
- `event: node` -> `data: <node_name>` (e.g., "retrieve_weather")
- `event: done` -> `data: [DONE]`

### Example Client (Python)

```python
import requests
import json

API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev-api-key-change-in-production"  # pragma: allowlist secret

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Streaming Example
def chat_stream(message):
    data = {"message": message, "user_id": "test_user"}
    
    with requests.post(f"{API_URL}/graph/stream", json=data, headers=headers, stream=True) as r:
        if r.status_code != 200:
            print("Error:", r.text)
            return

        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("event: token"):
                    # Next line is data: ...
                    continue 
                if decoded.startswith("data: "):
                    content = decoded.replace("data: ", "")
                    if content == "[DONE]":
                        break
                    print(content, end="", flush=True)

chat_stream("Salam, əkinçiliklə bağlı sualım var.")
```
