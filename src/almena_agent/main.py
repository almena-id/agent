"""FastAPI application: the health probe and the A2A interface."""

from fastapi import FastAPI
from scalar_fastapi import add_scalar_reference

from almena_agent import __version__
from almena_agent.a2a.routes import add_a2a_routes
from almena_agent.api.routes import health
from almena_agent.config import get_settings
from almena_agent.llm import Model, get_model


def create_app(model: Model | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.name,
        version=__version__,
        # The reference is Scalar's (below), not Swagger UI or ReDoc.
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        servers=[
            {"url": settings.public_url, "description": "Public"},
            {"url": "/", "description": "This server"},
        ],
    )
    if settings.docs_enabled:
        add_scalar_reference(app, route="/docs")
    app.include_router(health.router)
    add_a2a_routes(app, settings, model or get_model())
    return app


app = create_app()
