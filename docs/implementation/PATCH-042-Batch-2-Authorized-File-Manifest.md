# PATCH-042 Batch 2 Authorized File Manifest

Scope: production Compose/images, Nginx TLS edge, private networks, reproducible
frontend/backend build, and edge security only.

Authorized: CREATE `docker-compose.production.yml`, `backend/Dockerfile.production`,
`backend/requirements.production.lock`, `frontend/Dockerfile.production`,
`ops/nginx/nginx.conf`, `ops/nginx/default.conf`, `ops/nginx/frontend.conf`,
`ops/scripts/validate-production-topology.sh`, `backend/tests/test_production_topology.py`;
MODIFY `frontend/package.json` only if needed for reproducible build validation.

`backend/requirements.production.lock` is generated from the repository's
accepted `backend/requirements.txt` input using
`pip-compile --generate-hashes`; it is never hand-authored. The backend image
must install it using pip's `--require-hashes` mode. This reconciliation closes
the previously omitted accepted supply-chain artifact without changing
dependency intent.

Prohibited: domain routes, object data plane, backup/recovery, external deployment
claim. Stop for public backend/database exposure or unpinned build path.
