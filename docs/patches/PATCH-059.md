# PATCH-059 — Commercial Package Configuration, Seats & Signed Entitlements

Status: REGISTERED / OPEN — DISCOVERY AUTHORIZED

Date registered: 2026-09-30

## Human authority

The Human Authority explicitly authorized PATCH-059 registration and Discovery
on 2026-09-30 after PATCH-058 reached DONE / CLOSED.

This authorization permits Discovery only. It does not grant Architecture, ADR,
EDS, IDS, migration, implementation, deployment, release or PATCH-060
authority.

## Frozen capability boundary

PATCH-059 delivers Commercial Package Configuration, Seats & Signed
Entitlements for the supported SATCO-managed dedicated single-customer
deployment profile.

Commercial V1 uses signed offline entitlements. The accepted entitlement model
must support Core plus Electrical, Instrumentation and Control & Automation
individually and in supported combinations, including integrated E/I/C.

The governed PATCH-059 scope includes:

- signed offline dedicated-deployment entitlement/license;
- Organization/deployment binding as appropriate;
- enabled Core and supported E/I/C package combinations;
- seat entitlement and enforcement;
- validity period and governed grace behavior;
- support/update entitlement;
- signature verification and fail-closed backend/API enforcement;
- rollback resistance / anti-rollback behavior;
- administrator-facing entitlement configuration/status UX; and
- preservation of authorized historical read/export behavior across disabling
  or expiry according to the later accepted design.

## Frozen dependencies

PATCH-059 depends on the accepted package foundations from PATCH-051 and
PATCH-052 and on the immutable release identity established by PATCH-058.

PATCH-058 is DONE / CLOSED. Its immutable delivery candidate remains
`8c37dcfa8235490408fb5d9c2c2d4e24857d149a`, and its closure commit/tag target
is `a15daa081b952a9195a5de3f87ad09ffe9ad85e7`.

PATCH-059 must not require source forks for different commercial package
combinations.

## Explicit exclusions

PATCH-059 excludes:

- billing and payment processing;
- subscription automation;
- usage metering;
- advanced licensing analytics;
- SaaS orchestration;
- new product domains or Discipline Packages;
- PATCH-060 deployment qualification and Commercial V1 certification; and
- post-V1 licensing capabilities not separately re-baselined by Human
  authority.

## Frozen exit intent

PATCH-059 may reach DONE / CLOSED only when the accepted package, seat, expiry,
grace and upgrade/update matrices pass backend/API and administrator-UX
enforcement, rollback resistance is proven, and disabling/expiry neither
erases authorized historical records nor exposes unauthorized information.

Exact architecture, cryptographic format, trust/key model, anti-rollback state,
seat semantics, grace semantics, update-right semantics, failure behavior,
migration/storage model and UX contracts remain Discovery/Architecture
questions. They are not invented by this registration.

Human authority remains controlling. AI is advisory and non-authoritative.

## Governance state

- PATCH-058: DONE / CLOSED.
- PATCH-059: REGISTERED / OPEN — DISCOVERY AUTHORIZED.
- PATCH-059 Architecture authority: NOT GRANTED.
- PATCH-059 ADR authority: NOT GRANTED.
- PATCH-059 EDS authority: NOT GRANTED.
- PATCH-059 IDS authority: NOT GRANTED.
- PATCH-059 implementation authority: NOT GRANTED.
- PATCH-060: NOT STARTED / NOT AUTHORIZED.

**PATCH-059: REGISTERED / OPEN — DISCOVERY AUTHORIZED.**
