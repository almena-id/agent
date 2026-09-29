"""Entry point: ``almena-agent`` or ``python -m almena_agent``."""

import uvicorn

from almena_agent.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "almena_agent.main:app",
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
