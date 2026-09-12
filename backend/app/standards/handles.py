"""Reserved handle module; protected material handles are intentionally Batch-2+ only."""

from __future__ import annotations


class OpaqueAuthorizedHandleUnavailable(RuntimeError):
    """Raised rather than issuing a material handle before Batch 2 authorization."""
