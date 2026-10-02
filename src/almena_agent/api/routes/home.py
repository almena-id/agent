"""The page a browser shows at the agent's root (agent.almena.id).

What `/health` and the agent card already make public — status, version, the
A2A protocol and where the card is — under the header and footer of
Almena's portals, in the agent's identity colour, teal. Nothing about tasks or
conversations.

The typefaces are the portals' (SIL Open Font License, in `assets/fonts`),
served by the agent itself from `/fonts/{name}`.
"""

from datetime import UTC, datetime
from html import escape
from importlib.resources import files
from string import Template
from typing import Annotated
from urllib.parse import quote

from a2a.utils.constants import PROTOCOL_VERSION_CURRENT
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse

from almena_agent import __version__
from almena_agent.config import Settings, get_settings

router = APIRouter(include_in_schema=False)

FONTS = (
    "chakra-petch-500.woff2",
    "chakra-petch-600.woff2",
    "chakra-petch-700.woff2",
    "inter.woff2",
    "jetbrains-mono.woff2",
)

# The Almena mark (three nodes and their links), in the current colour.
_MARK = (
    '<svg width="{size}" height="{size}" viewBox="136 136 752 752" aria-hidden="true">'
    '<g stroke="currentColor" stroke-width="24" stroke-linecap="round">'
    '<line x1="512" y1="237" x2="237" y2="785"/><line x1="512" y1="237" x2="785" y2="785"/>'
    '<line x1="237" y1="785" x2="646" y2="507"/></g><g fill="currentColor">'
    '<circle cx="512" cy="237" r="94"/><circle cx="237" cy="785" r="94"/>'
    '<circle cx="785" cy="785" r="94"/></g></svg>'
)

BRAND = "#0fa3a3"


def _mark(size: int) -> str:
    return _MARK.format(size=size)


# The favicon is the mark itself, in teal, so the agent needs no icon file.
_FAVICON = "data:image/svg+xml," + quote(
    _MARK.format(size=64)
    .replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"')
    .replace("currentColor", BRAND)
)

# The page and its styles live in `assets/`: home.html, a `string.Template`,
# and home.css, the wallet's dark tokens with the agent's teal (green carries
# the status only) under the portals' header and footer.
_ASSETS = files("almena_agent") / "assets"
_TEMPLATE = Template((_ASSETS / "home.html").read_text(encoding="utf-8"))
_CSS = (_ASSETS / "home.css").read_text(encoding="utf-8")


def page(*, version: str, settings: Settings, year: int) -> str:
    """The root page, whole."""
    return _TEMPLATE.substitute(
        name=escape(settings.name),
        description=escape(settings.description),
        favicon=_FAVICON,
        css=_CSS,
        logo=_mark(28),
        small=_mark(18),
        version=escape(version),
        protocol=escape(PROTOCOL_VERSION_CURRENT),
        card_url=escape(f"{settings.public_url}/.well-known/agent-card.json"),
        year=year,
    )


@router.get("/", response_class=HTMLResponse)
async def home(settings: Annotated[Settings, Depends(get_settings)]) -> HTMLResponse:
    return HTMLResponse(page(version=__version__, settings=settings, year=datetime.now(UTC).year))


@router.get("/fonts/{name}")
async def font(name: str) -> Response:
    if name not in FONTS:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    data = (_ASSETS / "fonts" / name).read_bytes()
    return Response(
        data,
        media_type="font/woff2",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
