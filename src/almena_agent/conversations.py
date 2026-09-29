"""Conversation history per A2A context, in memory.

Each context's turns are what Claude gets back on the next message. History is
append-only: Claude's thinking blocks stay valid only while the turns before
them are sent back unchanged, so old turns are never trimmed; a context that
reaches ``AGENT_HISTORY_TURNS`` is full and the peer starts a new one.
Everything is lost on restart and is not shared between replicas.
"""

from collections.abc import Sequence

from anthropic.types.beta import BetaMessageParam


class Conversations:
    def __init__(self, max_turns: int) -> None:
        self._max_messages = max_turns * 2
        self._history: dict[str, list[BetaMessageParam]] = {}

    def history(self, context_id: str) -> list[BetaMessageParam]:
        return list(self._history.get(context_id, []))

    def is_full(self, context_id: str) -> bool:
        return len(self._history.get(context_id, [])) >= self._max_messages

    def record(self, context_id: str, turn: Sequence[BetaMessageParam]) -> None:
        """Appends a finished exchange (the user's message and Claude's reply)."""
        self._history.setdefault(context_id, []).extend(turn)
