# PATCH-035 Batch 1 Authorized File Manifest

Status: ACCEPTED

Batch: Contracts and Provider Boundary — S01–S03

Authorized files:

- CREATE `backend/app/enums/ai_capture_assistant.py` — closed enums;
- CREATE `backend/app/ports/ai_capture_assistant.py` — inward/outward contracts;
- CREATE `backend/app/schemas/ai_capture_assistant.py` — strict wire DTOs;
- CREATE `backend/app/exceptions/ai_capture_assistant.py` — inward exceptions;
- CREATE `backend/app/ai/capture_assistant.py` — provider-neutral HTTPS adapter;
- CREATE `backend/app/adapters/ai_capture_assistant.py` — canonical Capture adapter;
- CREATE `backend/tests/test_ai_capture_assistant_contracts.py` — closure evidence;
- CREATE `backend/tests/test_ai_capture_assistant_provider.py` — provider evidence;
- CREATE `backend/tests/test_ai_capture_assistant_security.py` — boundary evidence.

No service, Audit persistence, composition, router, main, migration, frontend,
or deferred behavior is authorized. Dependencies are accepted IDS-035 and the
canonical Capture service. Stop on field mismatch, direct repository/UoW use,
unbounded payload, provider secret persistence, or new authority.
