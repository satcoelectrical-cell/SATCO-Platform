# IDS-043 Focused Scanner Security Amendment

## Reconciliation basis

Implementation exposed that the accepted IDS named an authenticated scanner
principal without specifying its verifier. Repository discovery found the
existing PATCH-042 secret-file pattern and constant-time service-token verifier,
plus the already reserved `SUPPORTING_FILE_SCANNER_TOKEN_FILE` setting.

## Decision

IDS-043 now fixes a dedicated scanner-only high-entropy service credential,
server-side constant-time verification, a non-Human/non-Organization principal,
provider-neutral result attestation, explicit attempt binding, replay/stale
protection and three-attempt bounded retry. This is implementation mechanics
inside accepted EDS authority; Architecture and EDS remain unchanged.

## Historical preservation

B2-RR-MAJ-01 and B2-RR-MAJ-02 remain recorded as implementation-time blockers.
The earlier IDS review is not rewritten; this artifact records the subsequent
focused correction.
