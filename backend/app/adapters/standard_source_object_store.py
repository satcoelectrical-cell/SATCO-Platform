"""Bounded private standards object wrapper; no listing or public URLs."""
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

class StandardSourceObjectStore:
    """Narrow domain wrapper over the existing exact-key private-store port.

    The delegated store accepts only opaque ``objects/<sha256>`` keys.  The
    standards scope is therefore hashed before delegation and is never exposed
    by an API/audit/outbox payload.
    """
    def __init__(self, store):
        self._store = store
    def put_private(self, *, organization_id, project_id, snapshot_id, content: bytes, media_type: str):
        if not 1 <= len(content) <= 8192: raise ValueError("RESOURCE_LIMIT_EXCEEDED")
        key = "objects/" + sha256(f"standards:{organization_id}:{project_id}:{snapshot_id}:{uuid4().hex}".encode()).hexdigest()
        return self._store.put_private(key=key, content=BytesIO(content), media_type=media_type)
    def head_exact(self, key, version): return self._store.head_exact(key, version)
    def open_exact(self, key, version): return self._store.open_exact(key, version)
    def delete_exact(self, key, version): self._store.delete_exact(key, version)
