"""AITP v5 kernel primitives.

This package is intentionally independent from the legacy MCP tool surface.
MCP, CLI, hooks, and skills should call into these modules instead of
duplicating protocol logic.
"""

from brain.v5.paths import WorkspacePaths
from brain.v5.workspace import init_workspace

__version__ = "0.5.0"
KERNEL_VERSION = __version__
PROTOCOL_IMPLEMENTATION = "v5"
IMPLEMENTATION_GENERATION = "v5"

__all__ = [
    "__version__",
    "KERNEL_VERSION",
    "PROTOCOL_IMPLEMENTATION",
    "IMPLEMENTATION_GENERATION",
    "WorkspacePaths",
    "init_workspace",
]
