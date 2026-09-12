"""Static, non-browser Batch-2 provider contracts and test provider."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True, slots=True)
class ProviderFragment:
    location: str
    content: bytes | None
    media_type: str | None
    provider_token: str | None = None
    version_digest: str | None = None

class AuthorizedStandardSourceProvider(Protocol):
    provider_id: str
    adapter_policy_id: str
    adapter_policy_version: str
    def retrieve(self, *, location: str, purpose: str, provider_token: str | None = None) -> ProviderFragment: ...

class StaticStandardSourceProvider:
    """Deterministic test/local provider; never accepts URLs or navigation."""
    provider_id = "registry_metadata"
    adapter_policy_id = "static_allowlisted_v1"
    adapter_policy_version = "1"
    def __init__(self, fragments=None): self.fragments = fragments or {}
    def retrieve(self, *, location, purpose, provider_token=None):
        if not location or "://" in location or location.startswith("/") or ".." in location or "\\" in location:
            raise ValueError("INVALID_REQUEST")
        value = self.fragments.get((location, provider_token), self.fragments.get(location))
        if value is None: raise LookupError("CONTENT_UNAVAILABLE")
        if value.location != location or value.content is not None and len(value.content) > 8192:
            raise ValueError("INVALID_REQUEST")
        return value
