# Chatbot Server

Python backend for the smart AI chatbot (FastAPI, LangChain, LangGraph).

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**

## Quick Start

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY=...`
2. Run the CLI or API server:

```bash
# CLI chat
./run_dev_cli.sh
# or
uv run python src/main.py

# API server
./run_dev_server.sh
# or
uv run uvicorn src.server.app:app --reload --host 0.0.0.0 --port 8000
```

- **CLI**: Type `quit`, `exit`, or `q` to end the conversation.
- **API**: `POST /api/v1/stateless_chat` with `{"messages": [{"role": "user", "content": "..."}]}` — docs at `/docs`.

Example API-HTTP-request to localhost:

```bash
curl -X POST http://localhost:8000/api/v1/stateless_chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is 3 + 5?"}]}'
```

shall produce a response similar to: `{"content":"3 + 5 = 8"}.`

## Production

Rate limiting is expected to be implemented outside this service (e.g. at a central reverse proxy or API gateway). Do not expose the server directly to the public without such protection.

## Development

| Command             | Description                |
|---------------------|----------------------------|
| `uv sync`           | Install/sync dependencies  |
| `uv run pytest`     | Run tests                  |
| `uv run black .`    | Format code                |
| `uv run isort .`    | Sort imports               |
| `uv run ruff check` | Lint code                  |
