# Chatbot Server

Python backend for the smart AI chatbot (FastAPI, LangChain, LangGraph).

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**

## Quick Start

1. Create `.env` with `OPENAI_API_KEY=...`
2. Run the CLI chat interface:

```bash
uv run python src/main.py
# or
./run_dev.sh
```

Type `quit` or `exit` or `q` to end the conversation.

## Development

| Command            | Description              |
|--------------------|--------------------------|
| `uv sync`          | Install/sync dependencies |
| `uv run pytest`    | Run tests                |
| `uv run black .`   | Format code              |
| `uv run ruff check`| Lint code                |
