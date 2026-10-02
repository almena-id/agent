from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


async def test_serves_security_txt(client: AsyncClient) -> None:
    response = await client.get("/.well-known/security.txt")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    fields = dict(line.split(": ", 1) for line in response.text.splitlines())
    assert fields["Contact"] == "https://github.com/almena-network/agent/security/advisories/new"
    expires = datetime.fromisoformat(fields["Expires"])
    assert timedelta(0) < expires - datetime.now(UTC) < timedelta(days=365)
