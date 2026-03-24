# Smart AI Chatbot

An **evolving** side project built for **experimentation** and for **showcasing** how a modern, full-stack, agentic chatbot can be put together. Nothing here is frozen in stone: APIs, UX, and architecture will shift as ideas are tried out and lessons land.

The goal is a credible playground for **advanced chatbot-building**—multi-turn dialogue, tool use, structured auth and persistence, and a web UI that feels good to use—without pretending to be a finished product.

## What you’ll find

- A **Python** service that exposes chat and auth APIs, runs an **agent** built with **LangGraph** / **LangChain**, and talks to **PostgreSQL** (or mock adapters) for real usage patterns.
- A **React** single-page app (**Vite**, **TypeScript**, **Tailwind**, **[shadcn/ui](https://ui.shadcn.com/)** on **Radix** primitives) for the chat experience, routing, and client state.
- **Hexagonal-style boundaries** for auth and app data (swappable adapters—e.g. Postgres vs mocks—so core logic stays testable and portable).
- **Docker** images for the API and static UI, plus the root **`./ci.sh`** script (and GitHub Actions) that runs linting, tests, production builds, and optional image smoke checks.

## Tech snapshot


| Area        | Choices                                                                                 |
| ----------- | --------------------------------------------------------------------------------------- |
| Backend     | Python 3.12+, **FastAPI**, **Pydantic**, **uv** for env/lockfiles                       |
| Agent & LLM | **LangGraph**, **LangChain**, OpenAI-compatible models                                  |
| Data & auth | **asyncpg**, SQL migrations, JWT, optional **Supabase** paths                           |
| Frontend    | **React 19**, **Vite**, **TypeScript**, **Zustand**, **TanStack Form**, **Zod, Shadcn** |
| Quality     | **Ruff**, **pytest**, **ESLint**, **Vitest**                                            |


## Where to read next

- `[python/chatbot-server/README.md](python/chatbot-server/README.md)` — running the API, env vars, migrations  
- `[web/chat-ui/README.md](web/chat-ui/README.md)` — frontend dev server and build
