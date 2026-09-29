"""The A2A executor: turns each incoming message into a task Claude answers.

A message opens (or continues) a task; Claude's text streams into the task as
one artifact, and the task ends completed, rejected when Claude declines or
the conversation is full, or failed when Claude cannot be reached. A2A
contexts are conversations: messages sharing a ``contextId`` see the turns
before them.
"""

import asyncio
import logging
import uuid
from collections import defaultdict

from a2a.helpers import new_task_from_user_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message
from anthropic.types.beta import BetaMessageParam

from almena_agent.conversations import Conversations
from almena_agent.llm import Model, ModelUnavailable

logger = logging.getLogger(__name__)

RESPONSE_ARTIFACT = "response"


class ClaudeAgentExecutor(AgentExecutor):
    def __init__(self, model: Model, conversations: Conversations) -> None:
        self._model = model
        self._conversations = conversations
        # One message at a time per conversation, so turns stay in order.
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message = context.message
        if message is None:
            raise ValueError("the request carries no message")
        task = context.current_task
        if task is None:
            task = new_task_from_user_message(message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        text = context.get_user_input().strip()
        if not text:
            await updater.reject(self._say(updater, "Send the request as text."))
            return

        async with self._locks[task.context_id]:
            if self._conversations.is_full(task.context_id):
                await updater.reject(
                    self._say(updater, "This conversation is full: start a new context.")
                )
                return
            await updater.start_work()
            user: BetaMessageParam = {"role": "user", "content": text}
            history = [*self._conversations.history(task.context_id), user]
            artifact_id = str(uuid.uuid4())
            first = True

            async def on_text(chunk: str) -> None:
                nonlocal first
                await updater.add_artifact(
                    [new_text_part(chunk)],
                    artifact_id=artifact_id,
                    name=RESPONSE_ARTIFACT,
                    append=not first,
                )
                first = False

            try:
                reply = await self._model.reply(history, on_text)
            except ModelUnavailable:
                # The cause is logged, never sent: it can hold internal details.
                logger.exception("Claude could not answer in context %s", task.context_id)
                await updater.failed(self._say(updater, "The agent is unavailable; try again."))
                return
            if reply.refused:
                logger.info("Claude declined a request in context %s", task.context_id)
                await updater.reject(self._say(updater, "The agent cannot help with this request."))
                return
            self._conversations.record(
                task.context_id, [user, {"role": "assistant", "content": reply.content}]
            )
            await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # The framework has already cancelled execute(); record the new state.
        task = context.current_task
        if task is None:
            return
        await TaskUpdater(event_queue, task.id, task.context_id).cancel()

    @staticmethod
    def _say(updater: TaskUpdater, text: str) -> Message:
        return updater.new_agent_message([new_text_part(text)])
