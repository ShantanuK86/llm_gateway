# 🚀 Production-Grade LLM Gateway

A high-performance, async, OpenAI-compatible API Gateway designed to securely route, scale, and manage traffic to Large Language Models (like OpenAI and Google Gemini).

Built entirely from scratch with **FastAPI**, **PostgreSQL**, **Redis**, and **Docker** to demonstrate advanced backend engineering concepts for AI services.

## ✨ Features

- **OpenAI Standardized Schema**: Drop-in replacement for official OpenAI SDKs. The gateway dynamically translates payloads for non-OpenAI models like Gemini.
- **Resiliency & Fallbacks**: Built-in exponential backoff for handling `429` rate limits and `500` errors. If OpenAI goes down entirely, requests seamlessly fallback to Gemini.
- **Server-Sent Events (SSE) Streaming**: Supports real-time token streaming using async Python generators.
- **Exact-Match Caching**: Drastically reduces latency and API costs by hashing prompts via SHA-256 and serving identical queries instantly from Redis.
- **Distributed Rate Limiting**: Uses Redis atomic operations to implement fixed-window rate limiting per user, preventing abuse across horizontally scaled instances.
- **Async Cost Tracking**: Offloads token calculation and PostgreSQL database updates to FastAPI Background Tasks, ensuring zero latency penalty to the end-user.
- **OpenTelemetry Observability**: Automatically instruments inbound HTTP requests and outbound LLM network calls for distributed tracing.

## 📚 Masterclass Architecture Guide

This repository was built as an educational masterclass. For a deep dive into the engineering decisions, algorithms, and a complete system flow diagram, please read the [Architecture Guide](docs/architecture.md).

## 🛠️ Tech Stack

- **Framework**: FastAPI (Async)
- **HTTP Client**: HTTPX
- **Database**: PostgreSQL (SQLAlchemy Asyncpg)
- **Cache & Rate Limiting**: Redis
- **Observability**: OpenTelemetry
- **Containerization**: Docker & Docker Compose

## 🚀 Quickstart

### 1. Configure Environment Variables
Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```
Open `.env` and add your keys:
```text
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 2. Start the Gateway
Use Docker Compose to build and start the API, PostgreSQL database, and Redis cache:
```bash
docker-compose up -d --build
```
*(Note: On initial startup, a test user and an API key `test_api_key_123` are automatically seeded into the database for testing.)*

### 3. Test the Gateway
You can now test the gateway using standard curl commands or any OpenAI-compatible SDK!

**Basic Request (Will try OpenAI, fallback to Gemini if rate limited):**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: test_api_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

**Test the Redis Cache:**
Run the exact same command twice. The second response will return instantly (cache hit) and will not count towards your token cost!

### 4. View API Documentation
FastAPI provides automatic, interactive documentation. Once the server is running, visit:
👉 **http://localhost:8000/docs**

### 5. View Tracing Logs
To see the OpenTelemetry trace trees for your requests, view the container logs:
```bash
docker-compose logs -f api
```

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

## 📝 License
This project is open-source and available under the MIT License.
