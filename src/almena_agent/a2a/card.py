"""The agent card: who the agent is, what it can do and where to reach it.

Served at ``/.well-known/agent-card.json``; peers read it first.
"""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
)
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol

from almena_agent import __version__
from almena_agent.config import Settings

# Where the two A2A bindings are mounted, under the public origin.
JSONRPC_PATH = "/a2a/jsonrpc"
REST_PATH = "/a2a/rest"


def build_agent_card(settings: Settings) -> AgentCard:
    origin = settings.public_url.rstrip("/")
    return AgentCard(
        name=settings.name,
        description=settings.description,
        version=__version__,
        provider=AgentProvider(
            organization=settings.provider_organization, url=settings.provider_url
        ),
        # The first interface is the preferred one.
        supported_interfaces=[
            AgentInterface(
                url=f"{origin}{JSONRPC_PATH}",
                protocol_binding=TransportProtocol.JSONRPC.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
            AgentInterface(
                url=f"{origin}{REST_PATH}",
                protocol_binding=TransportProtocol.HTTP_JSON.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
        ],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain", "text/markdown"],
        skills=[
            AgentSkill(
                id="almena-assistant",
                name="Almena ID assistant",
                description=(
                    "Answers questions about Almena ID: its identities, "
                    "issuers, verifiers, mediators and registry."
                ),
                tags=["almena", "identity", "did", "didcomm"],
                examples=["What is a did:web identity in Almena ID?"],
            ),
        ],
    )
