"""Conversation history per A2A context, in memory.

Each context's turns are what Claude gets back on the next message. History is
append-only: Claude's thinking blocks stay valid only while the turns before
them are sent back unchanged, so old turns are never trimmed; a context that
reaches ``AGENT_HISTORY_TURNS`` is full and the peer starts a new one.
A context belongs to whoever started it (by a hash of their registry token,
or no token at all): its history can hold what the registry told them, so
nobody else may continue it.
Everything is lost on restart and is not shared between replicas.
"""

from collections.abc import Sequence

from anthropic.types.beta import BetaMessageParam


class Conversations:
    def __init__(self, max_turns: int) -> None:
        self._max_turns = max_turns
        self._turns: dict[str, int] = {}
        self._history: dict[str, list[BetaMessageParam]] = {}
        self._owners: dict[str, str] = {}

    def belongs_to(self, context_id: str, owner: str) -> bool:
        """Whether ``owner`` may continue the context (anyone may start a new one)."""
        return self._owners.get(context_id, owner) == owner

    def history(self, context_id: str) -> list[BetaMessageParam]:
        return list(self._history.get(context_id, []))

    def is_full(self, context_id: str) -> bool:
        return self._turns.get(context_id, 0) >= self._max_turns

    def record(self, context_id: str, owner: str, turn: Sequence[BetaMessageParam]) -> None:
        """Appends a finished exchange: the user's message and the turns answering it."""
        self._owners.setdefault(context_id, owner)
        self._turns[context_id] = self._turns.get(context_id, 0) + 1
        self._history.setdefault(context_id, []).extend(turn)
