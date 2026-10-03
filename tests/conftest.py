from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest
from anthropic.types.beta import BetaMessageParam, BetaTextBlock, BetaToolParam
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from almena_agent.llm import ModelUnavailable, OnText, Reply
from almena_agent.main import create_app
from almena_agent.registry import RegistryRefused, RegistryUnavailable, Toolbox, ToolOutcome


class FakeModel:
    """Answers in two chunks, and keeps what it was sent and the toolbox it had."""

    def __init__(self) -> None:
        self.calls: list[list[BetaMessageParam]] = []
        self.toolboxes: list[Toolbox | None] = []
        self.refuse = False
        self.unavailable = False

    async def reply(
        self,
        messages: Sequence[BetaMessageParam],
        on_text: OnText,
        toolbox: Toolbox | None = None,
    ) -> Reply:
        self.calls.append(list(messages))
        self.toolboxes.append(toolbox)
        if self.unavailable:
            raise ModelUnavailable("no credentials at /home/someone/.config")
        if self.refuse:
            return Reply(turns=[], text="", refused=True)
        await on_text("Hello ")
        await on_text("from Almena.")
        text = "Hello from Almena."
        content = [BetaTextBlock(type="text", text=text, citations=None)]
        return Reply(turns=[{"role": "assistant", "content": content}], text=text, refused=False)


class FakeToolbox:
    def __init__(self, token: str) -> None:
        self.token = token
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @property
    def tools(self) -> Sequence[BetaToolParam]:
        return [{"name": "list_tenants", "input_schema": {"type": "object"}}]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        self.calls.append((name, arguments))
        return ToolOutcome(text='[{"id": "t1"}]', is_error=False)


class FakeRegistry:
    """Accepts the token ``good``; ``down`` makes it unreachable."""

    def __init__(self) -> None:
        self.down = False
        self.opened: list[str] = []

    async def open(self, token: str) -> Toolbox:
        self.opened.append(token)
        if self.down:
            raise RegistryUnavailable("connection refused")
        if token != "good":
            raise RegistryRefused()
        return FakeToolbox(token)


@pytest.fixture
def model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def registry() -> FakeRegistry:
    return FakeRegistry()


@pytest.fixture
def app(model: FakeModel, registry: FakeRegistry) -> FastAPI:
    return create_app(model, registry)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"A2A-Version": "1.0"},
    ) as client:
        yield client
