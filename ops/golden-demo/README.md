# SATCO Golden Engineering Demo — isolated infrastructure

This directory codifies only the local qualification boundary. It is not a
production deployment and it does not relax production configuration.

## Fixed isolation boundary

- PostgreSQL: `127.0.0.1:55433`; never port `5432`.
- Backend: `127.0.0.1:18080`.
- Structural test scanner: `127.0.0.1:18082`.
- Versioned S3 test double: `https://127.0.0.1:19000` with a disposable CA.
- Frontend: `127.0.0.1:15173`.
- Semantic provider: local Ollama at `127.0.0.1:11434`, model
  `satco-qwen3-4b:latest`.

The scanner is intentionally labelled
`test-boundary-v1-no-malware-signatures`. It retrieves the exact object
version, verifies SHA-256, and parses the PDF. It is not a substitute for a
production malware scanner.

## Database bootstrap

Run `bootstrap_database.sql` against the disposable database before Alembic,
then again after Alembic. It creates only a non-login, non-privileged `satco`
role required by historical migrations and aligns the four PATCH-032 tables
and five validated functions with that non-login migration owner. Runtime
grants remain the migration-defined least-privilege grants. The bootstrap adds
no login, superuser, database-creation, role-creation, inheritance, or RLS
bypass authority.

The caller must independently guard the target database name and port before
invoking `psql`; the qualified database is
`satco_platform_patch02022_test` on port `55433`.
