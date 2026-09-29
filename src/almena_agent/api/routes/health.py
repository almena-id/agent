"""Liveness probe."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from almena_agent import __version__

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: Literal["ok"]
    version: str


@router.get("/health", summary="Liveness: the process is up")
async def health() -> Health:
    return Health(status="ok", version=__version__)
