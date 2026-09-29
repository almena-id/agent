"""The model behind the agent: Claude, through the Anthropic SDK.

``Model`` is what the A2A executor needs from it, so tests can put a fake in
its place (``get_model`` is the dependency to override).
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from anthropic import AnthropicError, AsyncAnthropic
from anthropic.types.beta import BetaContentBlock, BetaMessageParam

from almena_agent.config import Settings, get_settings
from almena_agent.prompts import SYSTEM_PROMPT

# Server-side fallback: when the model declines for policy reasons, the API
# retries the same request on its default fallback model within the call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

OnText = Callable[[str], Awaitable[None]]


class ModelUnavailable(Exception):
    """The model could not answer: credentials, network, rate limits, API errors."""


@dataclass(frozen=True)
class Reply:
    """A finished assistant turn."""

    # Every block as returned (thinking included), to send back unchanged
    # on the next turn of the conversation.
    content: Sequence[BetaContentBlock]
    text: str
    # The model (and its fallback, if any) declined the request.
    refused: bool


class Model(Protocol):
    async def reply(self, messages: Sequence[BetaMessageParam], on_text: OnText) -> Reply:
        """Answers the conversation's last user turn, streaming its text to ``on_text``.

        Raises ``ModelUnavailable`` when the model cannot be reached.
        """
        ...


class Claude:
    def __init__(self, settings: Settings, client: AsyncAnthropic | None = None) -> None:
        self._settings = settings
        # Made on first use, so that the app starts without credentials.
        self._client = client
        self._system = settings.system_prompt or SYSTEM_PROMPT

    async def reply(self, messages: Sequence[BetaMessageParam], on_text: OnText) -> Reply:
        try:
            return await self._reply(messages, on_text)
        except AnthropicError as error:
            # The SDK has already retried what is worth retrying (429, 5xx, network).
            raise ModelUnavailable(str(error)) from error

    async def _reply(self, messages: Sequence[BetaMessageParam], on_text: OnText) -> Reply:
        if self._client is None:
            self._client = AsyncAnthropic()
        async with self._client.beta.messages.stream(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            system=self._system,
            messages=list(messages),
            thinking={"type": "adaptive"},
            output_config={"effort": self._settings.effort},
            # Caches the system prompt and the conversation so far.
            cache_control={"type": "ephemeral"},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            async for text in stream.text_stream:
                await on_text(text)
            message = await stream.get_final_message()
        text = "".join(block.text for block in message.content if block.type == "text")
        return Reply(content=message.content, text=text, refused=message.stop_reason == "refusal")


@lru_cache
def get_model() -> Model:
    return Claude(get_settings())
