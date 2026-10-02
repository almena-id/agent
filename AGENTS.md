# AGENTS.md

Guidance for coding agents working on `agent`.

## Layout

```
src/almena_agent/
  __main__.py        entry point (`almena-agent`): runs uvicorn with the settings
  main.py            FastAPI app factory (`create_app(model)`): health, A2A routes, Scalar docs
  config.py          Settings (pydantic-settings, AGENT_* variables)
  prompts.py         the built-in system prompt
  llm.py             `Model`, what the executor needs from the model, and `Claude`,
                     its implementation (streaming, adaptive thinking, caching,
                     refusal fallback); `get_model` builds it
  conversations.py   history per A2A context, in memory, append-only
  a2a/card.py        the agent card and the bindings' paths
  a2a/executor.py    `ClaudeAgentExecutor`: message → task → streamed artifact → final state
  a2a/routes.py      mounts the card, JSON-RPC and REST routes (a2a-sdk) on the app
  api/routes/        plain HTTP routes outside A2A (health.py; home.py, the browser page
                     at `/` and its typefaces at `/fonts/`)
  assets/            home.html (a `string.Template`), home.css and the portals'
                     typefaces (`fonts/`, SIL OFL, licences beside them)
tests/               pytest (async, httpx ASGITransport); conftest's FakeModel stands in for Claude
```

## Rules

- Teal `#0fa3a3` is the agent's identity: `--brand` in `assets/home.css` and
  `BRAND` in `api/routes/home.py` (the favicon), carried by the mark in the header
  and footer. Green carries the status only. The identity colours across Almena:
  status cyan `#3fe0ff`, catalog blue `#2563eb`, registry green `#1f9d55`,
  mediator magenta `#d63384`, landing orange `#eb7229`, docu yellow `#f2b705`,
  api red `#e0413a`, agent teal `#0fa3a3`, the wallet the person's choice
  (orange by default).

- Everything is written in English: code, comments, docs, commit messages.
- Use `task` for everything (`task --list`); `task check` must pass before finishing.
- mypy runs in strict mode: type every function.
- Tests never call Claude: they pass a fake `Model` to `create_app`.
- Conversation history is append-only: never edit or trim turns already sent
  to Claude (it invalidates its thinking blocks).
- A2A types are protobuf messages from `a2a.types`; build them with
  `a2a.helpers` and `TaskUpdater` rather than by hand.
- New skills go in the agent card (`a2a/card.py`) and the README.
- New settings get an `AGENT_` variable in `config.py`, `.env.example`,
  `compose.yml` and the README table.
- New endpoints come with tests and keep the README endpoint table current.
