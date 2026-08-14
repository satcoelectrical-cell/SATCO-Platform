# PATCH-035 Batch 2 Authorized File Manifest

Status: ACCEPTED

Batch: Application, Audit, Composition, and Transport — S04–S07

Authorized files:

- MODIFY `backend/app/core/config.py` — disableable provider configuration;
- CREATE `backend/app/services/ai_capture_assistant_service.py` — orchestration;
- CREATE `backend/app/adapters/ai_capture_audit.py` — shared Audit mapping;
- CREATE `backend/app/dependencies/ai_capture_assistant.py` — request composition;
- CREATE `backend/app/api/v1/routers/ai_capture_assistant.py` — thin route;
- MODIFY `backend/app/main.py` — single registration;
- CREATE `backend/tests/test_ai_capture_assistant_service.py`;
- CREATE `backend/tests/test_ai_capture_assistant_audit.py`;
- CREATE `backend/tests/test_ai_capture_assistant_api.py`;
- MODIFY `backend/tests/test_ai_capture_assistant_security.py`.

No migration, AI-output persistence, canonical mutation, frontend, autonomous
action, EKG/Memory expansion, or future batch evidence packaging is authorized.
Stop on new role design, direct foreign persistence, unaudited provider call,
client-derived authority, or accepted-contract change.
