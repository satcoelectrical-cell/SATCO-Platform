# SATCO Backend Blueprint

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Goal

Build a scalable, maintainable and modular backend using FastAPI.

---

# Folder Structure

app/

api/

core/

config/

db/

models/

schemas/

repositories/

services/

ai/

jobs/

workflows/

storage/

auth/

permissions/

utils/

tests/

---

# Layer Responsibilities

## API

Receive requests.

Return responses.

No business logic.

---

## Services

Business logic.

Project workflow.

Engineering logic.

AI orchestration.

---

## Repositories

Database access only.

---

## Models

SQLAlchemy models.

---

## Schemas

Pydantic request/response models.

---

## AI

Context Builder

Prompt Builder

AI Router

Engineering Analyzer

Planner

Reviewer

Knowledge Manager

---

## Jobs

Background processing.

Long-running AI tasks.

Document analysis.

---

## Storage

File upload.

File versioning.

Document retrieval.

---

## Auth

Authentication.

Authorization.

JWT.

---

## Rule

Business logic belongs ONLY inside Services.

Database logic belongs ONLY inside Repositories.

