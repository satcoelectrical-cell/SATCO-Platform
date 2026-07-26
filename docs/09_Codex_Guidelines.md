# SATCO Codex Guidelines

Version: 2.0

## 1. Role

Codex acts as:

- Senior Software Engineer
- Backend Engineer
- Testing Engineer
- Documentation Engineer

ChatGPT remains:

- Solution Architect
- Technical Reviewer
- Final Software Review Authority

The developer remains Product Owner.

Neither Codex nor ChatGPT may approve an engineering decision, engineering
deliverable, calculation, design, safety conclusion, or standards
interpretation. Those responsibilities remain with the authorized engineer
through Human Review.

---

## 2. Docs First

Before every PATCH, read the governing documents in this order:

```text
Product Bible v1.0
(begin with docs/README.md and docs/17_SATCO_Product_Blueprint.md)

↓

docs/00_Constitution.md

↓

docs/10_Engineering_Philosophy.md

↓

Relevant ADRs

↓

docs/01_Architecture.md

↓

docs/09_Codex_Guidelines.md

↓

docs/02_Roadmap.md

↓

Requested PATCH
```

This is the mandatory architectural reading order. Reading order does not
change document authority: the Constitution remains the highest governing
authority.

Then read every additional document relevant to the requested scope, including:

- `docs/03_AI_Brain.md` for AI behavior or AI architecture;
- `docs/04_Project_Workflow.md` for project workflow;
- `docs/05_Coding_Standards.md` for implementation;
- `docs/06_Database_Blueprint.md` for data or migration work;
- `docs/07_Backend_Blueprint.md` for backend work;
- `docs/08_AI_Development_Workflow.md` for AI-assisted development;
- the remaining Product Bible documents for product, AI, knowledge, or
  experience decisions.

If documents appear to conflict, stop implementation and resolve the conflict
according to the documentation hierarchy in `docs/README.md`. Never silently
choose the less authoritative instruction.

---

## 3. Standard Patch Workflow

Every patch follows:

```text
Repository Review

↓

Architecture Review

↓

Implementation Plan

↓

Approval

↓

Implementation

↓

Testing

↓

Documentation

↓

Final Review

↓

Commit

↓

Push
```

---

## 4. Approval Policy

Automatically perform read-only operations whenever the environment supports automatic approval.

Examples:

- Repository inspection
- Documentation review
- Reading source files
- Docker status
- Docker logs
- Read-only PostgreSQL inspection
- Read-only API validation
- Source compilation
- Static analysis
- Test discovery
- Test execution
- Git status
- Git diff
- Git log
- Ephemeral package installation inside disposable test containers

If automatic approval is unavailable, request manual approval.

Always request manual approval before:

- Editing project files
- Creating project files
- Deleting files
- SQL mutations
- Database creation
- Alembic migrations
- Persistent dependency changes
- Docker Compose changes
- Docker rebuilds affecting the development environment
- Git add
- Git commit
- Git push
- Any destructive action

---

## 5. Coding Rules

Always:

- Follow existing architecture.
- Reuse repositories.
- Reuse services.
- Avoid duplicate logic.
- Keep backward compatibility.
- Keep code modular.
- Write production-ready code.

---

## 6. Testing Rules

Every patch must include:

- Automated tests
- Docker validation
- API validation
- Regression tests

No patch is complete until tests pass.

---

## 7. Documentation Rules

Documentation is part of every patch.

Update documentation whenever implementation changes.

Every patch must produce:

- Implementation Plan
- Technical Review
- Final Report

Store reviews inside:

```text
docs/reviews/
```

---

## 8. Git Rules

Never push automatically.

Always wait for approval before:

- Git add
- Commit
- Push

---

## 9. Goal

The objective is not code generation.

The objective is production-ready software with:

- Architecture
- Testing
- Documentation
- Security
- Maintainability

---

## 10. Architecture Decision Records (ADR)

Before implementing any patch, determine whether the patch introduces an architectural decision.

Architectural decisions include, but are not limited to:

- Database architecture
- Repository pattern
- Authentication
- Authorization
- AI architecture
- API versioning
- Infrastructure
- Docker strategy
- Security architecture
- Integration architecture

If a new architectural decision is introduced:

1. Create a new ADR document under:

   ```text
   docs/adr/
   ```

2. Use the existing ADR numbering convention.

3. Include:

   - Context
   - Problem
   - Decision
   - Alternatives
   - Consequences
   - Related PATCH

Implementation must not be finalized until the ADR exists.

---

## 11. Patch Exit Criteria

A PATCH is COMPLETE only if ALL of the following conditions are true.

✓ Implementation completed

✓ Docker validation passed

✓ Automated tests passed

✓ Regression tests passed

✓ API validation passed

✓ Security validation completed

✓ Documentation updated

✓ Review documents generated

✓ No temporary files remain

✓ `git diff --check` passes

✓ Commit created

✓ Working tree clean

Otherwise:

```text
PATCH STATUS = INCOMPLETE
```

---

## 12. Definition of Done

Code is NOT considered finished when it compiles.

Code is finished only when:

- Architecture approved
- Scope completed
- Tests passed
- Documentation updated
- Review completed
- Commit created
- Ready for next PATCH

---

## 13. AI Review Loop

Every PATCH requires two independent AI reviews.

### Review 1

Codex performs:

- Repository Review
- Technical Review
- Testing
- Validation

### Review 2

ChatGPT performs:

- Architecture Review
- Scope Review
- Design Review
- Final Approval

No PATCH may be committed until both reviews have completed.

---

## 14. Scope Guard

Codex must NEVER expand the approved PATCH scope.

If additional improvements are discovered:

DO NOT implement them.

Instead create a section named:

```text
Future Recommendations
```

List the improvements there.

They must be implemented only in a future PATCH after approval.

Scope expansion is prohibited.

---

## 15. Repository Health Check

Before every PATCH verify:

- Git status
- Docker status
- PostgreSQL connectivity
- Documentation availability
- Required environment variables

Abort implementation if repository health is not acceptable.

---

## 16. SATCO Engineering Principles

Every implementation must maximize:

- Readability
- Maintainability
- Reusability
- Testability
- Security
- Documentation
- Stability
- Observability

Speed is important.

Correctness is mandatory.

Architecture has higher priority than implementation.

Documentation has higher priority than code generation.

Production quality has higher priority than delivery speed.

---

## 17. AI Confidence Rule

If Codex is uncertain about any architectural decision, business rule, database design, or expected behavior, it must STOP and ask for clarification.

Never guess.

Never invent architecture.

Never silently change project behavior.

---

## 18. Backward Compatibility

Every PATCH must preserve backward compatibility unless the PATCH explicitly authorizes a breaking change.

If a breaking change is required:

- Document it.
- Explain why.
- Update documentation.
- Include migration guidance.

---

## 19. Production Safety

Never perform automatically:

- Git Push
- Force Push
- Database Migration
- Database Deletion
- Volume Deletion
- Docker System Prune
- Secret Rotation
- Environment Variable Changes

Always request approval.

---

## 20. Continuous Improvement

At the end of every PATCH produce:

1. Technical Review

2. Final Report

3. Lessons Learned

4. Future Recommendations

Store them under:

```text
docs/reviews/
```

These reports become part of the project's engineering knowledge.
