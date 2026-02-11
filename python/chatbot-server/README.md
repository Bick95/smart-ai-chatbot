# Chatbot Server

Python backend for the smart AI chatbot (FastAPI, LangChain, LangGraph).

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**

## Quick Start

```bash
./run_dev.sh
```

This syncs dependencies and starts the server.

## Development

| Command            | Description              |
|--------------------|--------------------------|
| `uv sync`          | Install/sync dependencies |
| `uv run pytest`    | Run tests                |
| `uv run black .`   | Format code              |
| `uv run ruff check`| Lint code                |

## Project Structure

```
chatbot-server/
├── src/
│   └── main.py
├── pyproject.toml
├── run_dev.sh
└── uv.lock
```
