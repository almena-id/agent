"""Mounts the A2A interface on the app: the agent card and both bindings."""

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI

from almena_agent.a2a.card import JSONRPC_PATH, REST_PATH, build_agent_card
from almena_agent.a2a.executor import ClaudeAgentExecutor
from almena_agent.config import Settings
from almena_agent.conversations import Conversations
from almena_agent.llm import Model
from almena_agent.registry import Registry


def add_a2a_routes(
    app: FastAPI, settings: Settings, model: Model, registry: Registry | None
) -> None:
    card = build_agent_card(settings)
    handler = DefaultRequestHandler(
        agent_executor=ClaudeAgentExecutor(model, Conversations(settings.history_turns), registry),
        # Tasks live in memory: lost on restart, not shared between replicas.
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url=JSONRPC_PATH),
        rest_routes=create_rest_routes(handler, path_prefix=REST_PATH),
    )
