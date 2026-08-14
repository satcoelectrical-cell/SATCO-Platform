"""Shared AuditLog mapping for PATCH-035 metadata-only records."""

import json

from app.models.audit_log import AuditLog


class SharedAICaptureAuditRecorder:
    def __init__(self, session) -> None:
        self._session = session

    def record(self, record) -> None:
        details = {
            "schema_version": 1,
            "outcome": record.outcome,
            "instruction_digest": record.instruction_digest,
            "context_digest": record.context_digest,
            "output_digest": record.output_digest,
            "provider_id": record.provider_id,
            "model_id": record.model_id,
            "has_workspace_scope": record.has_workspace_scope,
        }
        if len(json.dumps(details, sort_keys=True, separators=(",", ":")).encode()) > 1024:
            raise ValueError("audit details exceed bound")
        try:
            self._session.add(AuditLog(
                user_id=record.actor_id, action=record.action,
                entity="AI_CAPTURE_ASSISTANT", entity_id=None,
                entity_uuid=record.request_id, details=details,
            ))
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
