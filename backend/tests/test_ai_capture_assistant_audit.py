from uuid import uuid4

from app.adapters.ai_capture_audit import SharedAICaptureAuditRecorder
from app.ports.ai_capture_assistant import CopilotAuditRecord


class Session:
    def __init__(self): self.values, self.commits, self.rollbacks = [], 0, 0
    def add(self, value): self.values.append(value)
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def test_audit_mapping_is_bounded_and_plaintext_free():
    session = Session()
    SharedAICaptureAuditRecorder(session).record(CopilotAuditRecord(
        uuid4(), 4, "AI_CAPTURE_ADVICE_COMPLETED", "success", "a" * 64,
        "b" * 64, "c" * 64, "provider", "model", True,
    ))
    value = session.values[0]
    assert value.entity == "AI_CAPTURE_ASSISTANT" and session.commits == 1
    rendered = repr(value.details)
    for plaintext in ("instruction", "Original", "Suggested", "limitation"):
        assert plaintext not in rendered.replace("instruction_digest", "")
