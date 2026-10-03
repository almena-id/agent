# Almena Agent

The AI agent of Almena ID, served at `https://agent.almena.id`. It
answers with Claude (Anthropic) and is reached by other agents over the
[Agent2Agent (A2A) protocol](https://a2a-protocol.org) 1.0, through its agent
card and two bindings: JSON-RPC and HTTP+JSON (REST).

Built with Python 3.13, [a2a-sdk](https://pypi.org/project/a2a-sdk/) 1.1,
the [Anthropic SDK](https://pypi.org/project/anthropic/) 1.9 and FastAPI.

## Quick start

You need [uv](https://docs.astral.sh/uv/), [Task](https://taskfile.dev) and,
for `task up`, Docker. `task ask` also uses `jq`.

```bash
task init    # .env from .env.example; set ANTHROPIC_API_KEY in it
task dev     # the agent on http://localhost:8100, with auto-reload
task card    # its agent card
task ask -- "What is a did:web identity?"
task up      # the same, in Docker, behind Caddy at https://$AGENT_DOMAIN
task --list  # everything else
```

With `ANTHROPIC_API_KEY` empty, `task dev` uses an `ant auth login` profile.

Every merge into `main` publishes the image `ghcr.io/almena-id/agent`
(amd64 and arm64) with a `year.month.sequence` version (e.g. `2026.10.1`,
the sequence restarting each month), also tagged `latest` and `sha-<commit>`;
the commit gets the git tag `v<version>`. The image reports that version
(`ALMENA_VERSION`); outside it, the package's. See
[.github/workflows/docker.yml](.github/workflows/docker.yml).

`task up` also starts Caddy, which serves the agent at `https://$AGENT_DOMAIN`
(`agent.almena.id` in `.env.example`) with a Let's Encrypt certificate. Point
the name at this machine (in `/etc/hosts` for development); the certificate
needs the domain's zone in Cloudflare and `CLOUDFLARE_API_TOKEN` (Zone / DNS /
Edit) in `.env`. The agent still answers at `http://localhost:8100`.

## Endpoints

| Method | Path | What |
|--------|------|------|
| GET | `/.well-known/agent-card.json` | The A2A agent card: name, skills, capabilities and the endpoints below, under `AGENT_PUBLIC_URL` |
| POST | `/a2a/jsonrpc` | A2A JSON-RPC 2.0 binding (`SendMessage`, `SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`…) |
| * | `/a2a/rest/…` | A2A HTTP+JSON binding (`POST /message:send`, `POST /message:stream`, `GET /tasks/{id}`…) |
| GET | `/` | The home page for browsers (HTML, in teal): status, version, A2A protocol and the agent card's URL |
| GET | `/fonts/{name}` | The home page's typefaces (Chakra Petch, Inter, JetBrains Mono; woff2) |
| GET | `/.well-known/security.txt` | Where to report a vulnerability ([RFC 9116](https://www.rfc-editor.org/rfc/rfc9116)): this repository's private advisories; `Expires` stays 180 days ahead |
| GET | `/health` | Liveness and the running version |
| GET | `/docs`, `/openapi.json` | API reference (not in `production`) |

Requests to the A2A bindings carry the `A2A-Version: 1.0` header.

### How a message is answered

Each message opens a task. Claude's reply streams into it as one text
artifact (`response`), chunk by chunk under `SendStreamingMessage`; the task
ends `COMPLETED`; `REJECTED` when the message has no text, Claude declines
it, or the conversation is full, it belongs to another caller or the registry
refuses the caller's token; or `FAILED` when Claude cannot be reached
(the cause goes to the log, not to the peer). Messages sharing a `contextId` are one
conversation: Claude sees the turns before (up to `AGENT_HISTORY_TURNS`).

Claude runs with adaptive thinking at `AGENT_EFFORT`, prompt caching, and the
server-side refusal fallback (`fallbacks: "default"`): a request the model
declines for policy reasons is retried on its fallback model within the call.

Tasks and conversations are kept in memory: a restart loses them, and they are
not shared between replicas.

### The registry's tools

A message sent with the caller's Almena registry token, `Authorization: Bearer
almena_…` (an API token made in the registry portal or with `almena`), gets the
registry's tools: the agent is an MCP client of the API's endpoint
(`AGENT_REGISTRY_MCP_URL`) and acts as that token's account, so it sees and
does only what the account may, checked by the API as any other request. The
card declares the token as the optional `almenaRegistry` scheme, and the
`almena-registry` skill. Claude calls the tools as it needs them, up to
`AGENT_MAX_TOOL_ROUNDS` rounds per reply (the last must answer); what it says
between rounds streams into the same artifact. Changes that end in a signature
(publishing, signing an identity, issuing) only return the wallet request,
which the signer approves in their wallet.

Without a token there are no tools and the agent only converses; a token the
registry refuses rejects the task; an unreachable registry leaves the agent
without tools for that message. A context stays with whoever started it (by a
hash of the token, or no token): another caller continuing it is rejected,
since its history holds what the registry told the first.

```bash
curl -s https://agent.almena.id/a2a/rest/message:send \
  -H "A2A-Version: 1.0" -H "Authorization: Bearer $ALMENA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": {"messageId": "1", "role": "ROLE_USER", "parts": [{"text": "What does my tenant still need?"}]}}'
```

## Configuration

`.env` (from `.env.example`), or the environment:

| Variable | Default | What |
|----------|---------|------|
| `AGENT_ENVIRONMENT` | `development` | `development`, `production` (hides `/docs`) or `test` |
| `AGENT_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `AGENT_HOST` | `127.0.0.1` | Interface to listen on (`0.0.0.0` in the image) |
| `AGENT_PORT` | `8100` | Port to listen on (and the one Compose publishes) |
| `AGENT_FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies whose `X-Forwarded-*` headers are trusted |
| `AGENT_DOMAIN` | — | Domain of the deployment, for Docker Compose and Caddy only |
| `CLOUDFLARE_API_TOKEN` | — | Caddy's DNS-01 challenge (Zone / DNS / Edit) |
| `AGENT_PUBLIC_URL` | `https://agent.almena.id` | Public origin; the agent card's endpoints are under it |
| `AGENT_NAME` | `Almena Agent` | The agent's name in its card |
| `AGENT_DESCRIPTION` | `The AI agent of Almena ID.` | Its description in the card |
| `AGENT_PROVIDER_ORGANIZATION` | `Almena ID` | Who runs it |
| `AGENT_PROVIDER_URL` | `https://almena.id` | Their site |
| `ANTHROPIC_API_KEY` | — | Claude API key (read by the Anthropic SDK) |
| `AGENT_MODEL` | `claude-opus-5-5` | Claude model |
| `AGENT_EFFORT` | `high` | `low`, `medium`, `high`, `xhigh` or `max` |
| `AGENT_MAX_TOKENS` | `64000` | Most tokens per reply |
| `AGENT_SYSTEM_PROMPT` | — | Replaces the built-in prompt (`src/almena_agent/prompts.py`) |
| `AGENT_HISTORY_TURNS` | `50` | Exchanges a conversation holds |
| `AGENT_REGISTRY_MCP_URL` | `https://api.almena.id/mcp` | The registry API's MCP endpoint, used with each caller's token (empty: no tools) |
| `AGENT_MAX_TOOL_ROUNDS` | `20` | Rounds of tool calls one reply may take before it must answer |

## Deployment

The container listens on 8100 behind a TLS-terminating proxy for
`agent.almena.id` that forwards everything to it: this project's Caddy
(`Caddyfile`) when it runs alone; with the whole network, `../develop`'s,
whose `task up` stops this one and serves `AGENT_DOMAIN` in its place.

## License

[Apache License 2.0](LICENSE).
