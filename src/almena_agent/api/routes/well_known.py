"""security.txt (RFC 9116): where to report a vulnerability."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/.well-known", tags=["security"])

# Where vulnerabilities are reported: privately, through the repository's GitHub.
REPOSITORY = "https://github.com/almena-id/agent"
# security.txt must expire, in less than a year; written on each request, it
# stays this far ahead while the agent runs.
SECURITY_TXT_TTL = timedelta(days=180)


@router.get(
    "/security.txt",
    summary="Where to report a vulnerability (RFC 9116)",
    response_class=PlainTextResponse,
)
async def security_txt() -> PlainTextResponse:
    expires = (datetime.now(UTC) + SECURITY_TXT_TTL).replace(microsecond=0)
    return PlainTextResponse(
        f"Contact: {REPOSITORY}/security/advisories/new\n"
        f"Expires: {expires.isoformat().replace('+00:00', 'Z')}\n"
        f"Policy: {REPOSITORY}/security/policy\n"
        "Preferred-Languages: en, es\n"
    )
