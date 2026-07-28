# ADR-016 Dual-Use Platform Operating Model

## Status

Accepted

## Context

SATCO originated as the operational foundation for SATCO Engineering: a
technical engineering company in which Human engineers work with
AI-assisted engineering capabilities to receive requests, execute projects,
review technical information, coordinate disciplines, and produce governed
engineering outputs.

During product development, a second valid operating model became clear.
The same platform can also be deployed as an independent engineering
software product for petrochemical companies, industrial organizations,
EPC contractors, consultants, and other engineering departments.

These two operating models must share one governed product architecture.
SATCO must not require separate codebases, duplicated domain models, or
customer-specific architectural forks.

## Decision

SATCO Platform shall be designed as an operator-neutral engineering
platform supporting both of the following operating models:

1. SATCO Engineering uses the platform as its internal operating system for
   delivering engineering services to its own customers.
2. External engineering organizations deploy or subscribe to the platform
   as software used by their own engineering personnel.

Every generally applicable capability shall support both operating models
through configuration, authorization, organizational scope, deployment
choice, and user responsibility rather than through source-code forks.

SATCO Engineering may be one operator of SATCO Platform, but the platform
domain shall not assume that SATCO Engineering is always the operator,
service provider, approver, Customer, or final engineering authority.

## Product Structure

The long-term product architecture consists of three principal capability
layers.

### Core Platform

The Core Platform provides the governed operational foundation, including:

- identity and authentication;
- Customers, Projects, and Workspaces;
- authorization and confidentiality;
- audit and traceability;
- Engineering Context;
- Context relationships;
- Interface Commitments;
- lifecycle, responsibility, and concurrency foundations.

### Engineering Intelligence

Engineering Intelligence provides deterministic and governed engineering
assistance, including future capabilities such as:

- Derived Context;
- Missing Information;
- conflict identification;
- technical proposal review;
- design review;
- vendor evaluation;
- engineering knowledge support;
- engineering decision assistance.

Engineering Intelligence shall preserve Human engineering authority and
shall not silently promote findings into approved engineering decisions.

### AI Workforce

The AI Workforce provides authorized AI-assisted roles operating over the
governed platform Context, including potential future assistants for:

- electrical engineering;
- instrumentation engineering;
- mechanical engineering;
- process engineering;
- document control;
- QA/QC;
- proposal review;
- project coordination.

AI Workforce capabilities assist Human users and do not replace accountable
engineering judgment, review, approval, or organizational authority.

## Operating Principles

### One Product, Multiple Operators

SATCO Engineering and external organizations use the same product
architecture.

Operator-specific behavior shall be expressed through configuration,
organizational ownership, permissions, deployment, branding, and governed
extensions.

### No Code Forks

A capability shall not require separate SATCO-internal and customer-product
implementations unless a future ADR explicitly authorizes an exceptional
technical boundary.

### Human Engineering Authority

AI assistance, Engineering Intelligence, and automated analysis shall remain
subordinate to authorized Human engineering review and approval.

### Context Before AI

AI capabilities shall consume authorized, traceable, scoped Engineering
Context. AI shall not become an alternative source of truth outside the
governed platform model.

### Product and Service Compatibility

Capabilities created for SATCO Engineering should be reusable by external
engineering organizations where the underlying engineering need is general.

Capabilities created for external customers should remain usable by SATCO
Engineering where applicable.

### Deployment Neutrality

The architecture shall remain compatible with future SaaS, dedicated-hosted,
and on-premise deployment models without embedding one deployment model into
the engineering domain.

## Consequences

### Positive Consequences

- SATCO Engineering becomes the first operational user of the product.
- Real engineering projects can validate product capabilities.
- The same development investment supports service delivery and software
  sales.
- Product capabilities remain reusable across industrial organizations.
- Customer adoption does not require a separate platform architecture.
- SATCO gains a practical path from internal engineering operations to a
  commercial engineering software product.

### Costs and Constraints

- Organizational scope and authorization must remain explicit.
- Product terminology must not assume SATCO is always the service provider.
- Branding and deployment concerns must remain outside core engineering
  semantics.
- Customer data isolation and confidentiality require strict enforcement.
- AI assistants must operate only through authorized Context access.
- New modules must be evaluated against both operating models.

## Required Design Check

For every future major capability, design and review shall answer:

1. Can SATCO Engineering use this capability while delivering engineering
   services?
2. Can an external engineering organization use the same capability for its
   own internal work?
3. Does the design avoid assuming SATCO is always the operator or approver?
4. Are organizational scope, confidentiality, authority, and deployment
   boundaries preserved?
5. Does the capability avoid creating separate internal and commercial code
   paths?

A negative answer requires explicit design justification and, when
architecturally significant, a separate ADR.

## Scope Boundaries

This ADR does not authorize:

- AI Workforce implementation;
- autonomous engineering approval;
- new engineering modules;
- frontend implementation;
- SaaS billing;
- tenant provisioning;
- deployment automation;
- customer-specific code forks;
- changes to existing PATCH scope.

Each capability still requires its own approved lifecycle artifacts and
implementation authorization.

## Alignment

This decision preserves:

- PostgreSQL as the governed system of record;
- Context-first architecture;
- Human engineering authority;
- manual review and approval boundaries;
- operator and Customer confidentiality;
- modular future-domain development;
- documentation-first governance.

## Final Decision

SATCO shall be developed as one operator-neutral Engineering Operating
System that serves both as the internal operating platform of SATCO
Engineering and as a commercial software product for external engineering
organizations.
