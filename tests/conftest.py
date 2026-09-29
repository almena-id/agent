from collections.abc import AsyncIterator, Sequence

import pytest
from anthropic.types.beta import BetaMessageParam, BetaTextBlock
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from almena_agent.llm import ModelUnavailable, OnText, Reply
from almena_agent.main import create_app


class FakeModel:
    """Answers in two chunks, and keeps what it was sent."""

    def __init__(self) -> None:
        self.calls: list[list[BetaMessageParam]] = []
        self.refuse = False
        self.unavailable = False

    async def reply(self, messages: Sequence[BetaMessageParam], on_text: OnText) -> Reply:
        self.calls.append(list(messages))
        if self.unavailable:
            raise ModelUnavailable("no credentials at /home/someone/.config")
        if self.refuse:
            return Reply(content=[], text="", refused=True)
        await on_text("Hello ")
        await on_text("from Almena.")
        text = "Hello from Almena."
        return Reply(
            content=[BetaTextBlock(type="text", text=text, citations=None)],
            text=text,
            refused=False,
        )


@pytest.fixture
def model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def app(model: FakeModel) -> FastAPI:
    return create_app(model)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"A2A-Version": "1.0"},
    ) as client:
        yield client
