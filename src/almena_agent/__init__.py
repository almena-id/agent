"""AI agent of Almena ID, reachable over the Agent2Agent (A2A) protocol."""

import os
from importlib.metadata import version

# ALMENA_VERSION when the image sets it (year.month.sequence, see
# .github/workflows/docker.yml), else the package version.
__version__ = os.environ.get("ALMENA_VERSION") or version("almena-agent")
