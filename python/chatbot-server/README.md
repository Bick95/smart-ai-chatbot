# Chatbot Server

Python backend for the smart AI chatbot (FastAPI, LangChain, LangGraph).

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**

## Quick Start

1. Create `.env` with `OPENAI_API_KEY=...`
2. Run the CLI or API server:

```bash
# CLI chat
uv run python src/main.py
# or
./run_dev.sh

# API server
./run_server.sh
# or
uv run uvicorn src.server.app:app --reload --host 0.0.0.0 --port 8000
```

- **CLI**: Type `quit`, `exit`, or `q` to end the conversation.
- **API**: `POST /api/v1/chat` with `{"messages": [{"role": "user", "content": "..."}]}` — docs at `/docs`.

## Development

| Command            | Description              |
|--------------------|--------------------------|
| `uv sync`          | Install/sync dependencies |
| `uv run pytest`    | Run tests                |
| `uv run black .`   | Format code              |
| `uv run ruff check`| Lint code                |
