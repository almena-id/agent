from httpx import AsyncClient

from almena_agent import __version__
from almena_agent.api.routes.home import FONTS
from almena_agent.config import get_settings


async def test_home_is_a_page_in_teal(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "Operational" in html
    assert __version__ in html
    assert get_settings().model not in html
    assert "/.well-known/agent-card.json" in html
    assert "--brand:#0fa3a3" in html
    assert "<header>" in html and "<footer>" in html


async def test_home_is_not_in_the_openapi_document(client: AsyncClient) -> None:
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/" not in paths
    assert "/fonts/{name}" not in paths


async def test_every_font_the_page_asks_for_is_served(client: AsyncClient) -> None:
    html = (await client.get("/")).text
    for name in FONTS:
        assert f"/fonts/{name}" in html
        response = await client.get(f"/fonts/{name}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "font/woff2"
        assert response.content.startswith(b"wOF2")


async def test_unknown_fonts_are_not_found(client: AsyncClient) -> None:
    assert (await client.get("/fonts/OFL-inter.txt")).status_code == 404
    assert (await client.get("/fonts/..%2Fmain.py")).status_code == 404
