# PATCH-059 Batch D Checkpoint

**Date:** 2026-10-01
**Batch:** D — frontend commercial administration
**Branch:** `patch-059-implementation`
**Accepted implementation parent:** `18a788c71b1cad37885bb5965e197f957f3d935b`
**Disposition:** PASS — Human Batch D Implementation Acceptance APPROVED

The formal checkpoint commit containing this record atomically preserves the
accepted Batch D implementation and its evidence. This checkpoint is not
PATCH-059 release approval, deployment approval, closure, tag authorization,
push authorization, authorization to begin Batch E, or authorization to begin
PATCH-060.

## Implemented frontend scope

Batch D adds the bounded commercial administration presentation layer under the
existing `OrganizationAdminPage`:

- `CommercialEntitlementPanel` displays server-derived effective entitlement
  state, current-Organization/configured-deployment binding, entitlement
  identity, revision, digest prefix, entitled package combination, seat
  capacity, validity/grace boundaries and support boundary.
- The signed-entitlement flow accepts a complete signed JSON envelope by file
  or paste, sends the original text to server validation without browser
  parsing or canonicalization, presents the bounded server preview, and
  requires a separate explicit Human activation confirmation.
- `CommercialSeatsPanel` displays server-returned capacity, consuming count,
  over-capacity state, ASSIGNED/RESERVED/RETAINED state and executable status.
  It supports current-Organization seat assignment and release.
- Over-capacity reconciliation submits the explicitly selected complete
  retained-user set. The browser does not choose a winner, calculate a retained
  set or decide whether capacity has been resolved.
- The existing discipline-package configuration panel displays bounded
  server-returned commercial status and backend denial. Obvious unavailable or
  not-entitled package choices are disabled only as a usability projection of
  current server state; the backend re-evaluates every save.
- Existing loading, empty, protected and unavailable presentation patterns,
  accessible status/alert semantics, responsive layout and Organization-admin
  styling are reused.

The accepted implementation is limited to these eight frontend files:

- `frontend/src/api/client.ts`
- `frontend/src/api/types.ts`
- `frontend/src/components/CommercialEntitlementPanel.tsx`
- `frontend/src/components/CommercialSeatsPanel.tsx`
- `frontend/src/components/OrganizationPackageConfigurationPanel.tsx`
- `frontend/src/pages/OrganizationAdminPage.tsx`
- `frontend/src/styles.css`
- `frontend/src/test/patch059-commercial-admin.test.tsx`

## API integration

The frontend uses only the accepted current-Organization C2 contracts:

- `GET /organizations/current/commercial-entitlement`
- `POST /organizations/current/commercial-entitlement/validate`
- `POST /organizations/current/commercial-entitlement/activate`
- `GET /organizations/current/commercial-seats`
- `POST /organizations/current/commercial-seats/{user_id}`
- `DELETE /organizations/current/commercial-seats/{user_id}`
- `PUT /organizations/current/commercial-seats/retained`

No Organization identifier or deployment identifier is supplied by the
browser. Signed Validate and Activate bodies are the unchanged administrator-
supplied envelope text. Exact retained selection sends only the selected
current-Organization user identifiers. HTTP failure presentation is bounded;
raw backend details are not rendered.

Sensitive commercial requests reuse bearer session handling and the PATCH-058
CSRF cookie/header contract. A server response with the exact accepted recent-
authentication requirement is represented as `step_up_required`, focuses the
existing PATCH-058 Sensitive security administration flow, and requires the
administrator to retry the original operation normally after successful
step-up. No browser timer or local recent-authentication decision authorizes a
commercial mutation.

## Security and authority boundaries

The browser is presentation and request orchestration only. It does not:

- verify signatures, keys or canonical JSON;
- calculate authoritative validity, expiry, grace or trusted time;
- infer entitlement binding, package authority or effective state;
- calculate seat consumption/capacity or automatically select retained seats;
- derive update eligibility or release-sequence compatibility;
- accept Organization/deployment scope from an administrator;
- create signing/private-key UI; or
- persist entitlement material, access tokens or step-up authority in browser
  storage.

Displayed dates are formatting of server-returned values only and are never
compared with browser time for an authority decision. Validation previews and
package/seat usability state remain non-authoritative; the server repeats all
canonical authorization, binding, signature/trust, trusted-time, revision,
package and seat evaluation.

The final security and tenant review covered current-Organization paths,
administrator-only page placement, CSRF, explicit server-required step-up,
bounded error handling, sensitive material retention, raw-envelope transport,
package denial, retained-set semantics and absence of duplicated commercial or
release authority.

Findings:

- Critical: 0
- Major: 0
- open security/tenant findings: 0

## Qualification evidence

Focused Batch D command:

```text
npm run test:run -- src/test/patch059-commercial-admin.test.tsx
```

Result:

- 11 passed
- 0 failed

Related Organization administration, PATCH-058 security and typed API
regression command:

```text
npm run test:run -- src/test/organization-admin.test.tsx \
  src/test/patch058-c4-security-ui.test.tsx src/test/api.test.ts
```

Result:

- 27 passed
- 0 failed

Full frontend qualification command:

```text
npm run test:run
```

Result:

- 37 test files passed
- 217 tests passed
- 0 failed

Additional guards:

- `npm run typecheck`: PASS
- `npm run build`: PASS
- production bundle-size warning above 500 kB: non-blocking
- lint: not configured in the accepted frontend toolchain
- `git diff --check`: PASS

The production build warning recommends optional future code splitting. It did
not represent a correctness, security, tenant-boundary or build failure.
Qualification did not require a database; neither disposable port 55432 nor the
real PostgreSQL service on port 5432 was touched during Batch D.

## Batch E dependency and explicit deferral

Update eligibility and release-sequence integration remain explicitly deferred
to Batch E. Batch D does not call or expose an update-eligibility API, display
release-sequence controls, accept a client-supplied installed/candidate release
sequence, hard-code a release sequence, or create a second release authority.
PATCH-058 Release Manifest evidence remains unchanged and authoritative until
the governed Batch E work is separately authorized and accepted.

## Human decision and checkpoint boundary

Human Batch D Implementation Acceptance: **APPROVED**.

Batch D implementation qualification: PASS.

Checkpoint D finalization is authorized. No push, tag, release or PATCH-059
closure is authorized. This checkpoint does not authorize automatic progression
into Batch E or any work on PATCH-060.
