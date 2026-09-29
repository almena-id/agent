import json
import uuid
from typing import Any

from httpx import AsyncClient

from tests.conftest import FakeModel


def user_message(text: str, context_id: str | None = None) -> dict[str, Any]:
    message: dict[str, Any] = {
        "messageId": str(uuid.uuid4()),
        "role": "ROLE_USER",
        "parts": [{"text": text}],
    }
    if context_id:
        message["contextId"] = context_id
    return message


async def send(client: AsyncClient, message: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        "/a2a/jsonrpc",
        json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": message}},
    )
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert "error" not in body, body
    task: dict[str, Any] = body["result"]["task"]
    return task


def artifact_text(task: dict[str, Any]) -> str:
    (artifact,) = task["artifacts"]
    return "".join(part["text"] for part in artifact["parts"])


async def test_a_message_becomes_a_completed_task(client: AsyncClient, model: FakeModel) -> None:
    task = await send(client, user_message("Hi"))
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert artifact_text(task) == "Hello from Almena."
    assert model.calls == [[{"role": "user", "content": "Hi"}]]


async def test_a_context_is_a_conversation(client: AsyncClient, model: FakeModel) -> None:
    first = await send(client, user_message("Hi"))
    await send(client, user_message("And again", context_id=first["contextId"]))
    second_call = model.calls[1]
    assert [turn["role"] for turn in second_call] == ["user", "assistant", "user"]
    assert second_call[-1] == {"role": "user", "content": "And again"}

    await send(client, user_message("Elsewhere"))
    assert model.calls[2] == [{"role": "user", "content": "Elsewhere"}]


async def test_a_declined_request_is_rejected(client: AsyncClient, model: FakeModel) -> None:
    model.refuse = True
    task = await send(client, user_message("Something off-limits"))
    assert task["status"]["state"] == "TASK_STATE_REJECTED"


async def test_the_rest_binding_answers_too(client: AsyncClient) -> None:
    response = await client.post("/a2a/rest/message:send", json={"message": user_message("Hi")})
    assert response.status_code == 200, response.text
    task = response.json()["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert artifact_text(task) == "Hello from Almena."


async def test_the_reply_streams_as_artifact_chunks(client: AsyncClient) -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "SendStreamingMessage",
        "params": {"message": user_message("Hi")},
    }
    async with client.stream("POST", "/a2a/jsonrpc", json=request) as response:
        assert response.status_code == 200
        events = [
            json.loads(line.removeprefix("data:"))["result"]
            async for line in response.aiter_lines()
            if line.startswith("data:")
        ]
    chunks = [
        e["artifactUpdate"]["artifact"]["parts"][0]["text"] for e in events if "artifactUpdate" in e
    ]
    assert chunks == ["Hello ", "from Almena."]
    states = [e["statusUpdate"]["status"]["state"] for e in events if "statusUpdate" in e]
    assert states == ["TASK_STATE_WORKING", "TASK_STATE_COMPLETED"]


async def test_an_unreachable_model_fails_the_task_without_details(
    client: AsyncClient, model: FakeModel
) -> None:
    model.unavailable = True
    task = await send(client, user_message("Hi"))
    assert task["status"]["state"] == "TASK_STATE_FAILED"
    assert "/home/someone" not in json.dumps(task)
