"""PATCH-053 read-only standards projection seam.

It consumes an already-retained Finding/report projection and returns only
safe, non-authoritative standards advisory metadata.  It deliberately has no
database dependency and cannot affect PATCH-053 evaluation or history.
"""
from __future__ import annotations
from app.ai.standards_intelligence import canonical_bytes

def project_standards_advisory(*, retained_context: dict, deterministic: dict) -> dict:
    if not isinstance(retained_context, dict) or not isinstance(deterministic, dict):
        raise ValueError("invalid retained projection")
    safe = {key: retained_context[key] for key in ("assessment_id", "finding_id", "report_id") if isinstance(retained_context.get(key), str)}
    return {"advisory": True, "human_authority_required": True, "retained_context": safe,
            "deterministic_digest": __import__("hashlib").sha256(canonical_bytes(deterministic)).hexdigest(),
            "message": "Reference-only standards context may assist Human interpretation; it changes no finding, rule, outcome, or history."}
