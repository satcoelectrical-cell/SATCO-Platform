# PATCH-042 Operational Runbooks

All procedures use non-customer inputs, individually attributable Human authority,
bounded evidence, and the stated stop/escalation path. No procedure grants
engineering or Organization-business authority, permits schema stamping, or
uses a local/unrecorded break-glass path.

| Runbook | Trigger and authority | Steps/evidence | Failure route / prohibited shortcut |
|---|---|---|---|
| Deployment | Approved immutable release; elevated Human Operations | preflight, verified set, image/asset digests, readiness, reopen record | hold traffic; no mutable tag deploy |
| Configuration | configuration change; authorized operator | validate secret refs/config categories, restart affected service, record | fail closed; no defaults/raw env dump |
| Bootstrap | approved bounded bootstrap; operator plus PATCH-041 application checks | enable config/secret/window, execute protected bootstrap, disable/revoke, Audit | deny ineligible/second Organization; no config override |
| Startup/shutdown | planned maintenance/incident; elevated operator | drain, stop/start, live/ready checks, timestamps | keep traffic closed; no force serve |
| Migration | approved release; schema owner | backup, preflight, one-shot migration, guard/head verification | restore/recovery; no `alembic stamp` |
| Upgrade | approved immutable release; Human Operations | deployment sequence in `upgrade.sh`, smoke, reopen evidence | compatible rollback or recovery set |
| Backup | hourly scheduler; backup principal | encrypt, checksum, recovery manifest, off-host target, retention evidence | incident/RPO mode; runtime credentials prohibited |
| Restore | recovery candidate; Human recovery authority | isolated restore, manifest/schema/release/guard verification | select another verified set; no production overwrite |
| Recovery | P1/P2 incident; Human promotion authority | isolate, restore, verify, record data-loss window and promotion | preserve failed instance; no automatic destructive recovery |
| Rollback | failed release; Human Operations | verify compatibility, read-only drain, redeploy or restore | no downgrade assumption/schema stamp |
| Health/diagnostics | alert/support request; normal support | generic health, protected bounded diagnostics, safe bundle | escalate dependency; no customer/raw config disclosure |
| Operator access | support/elevation request; approving Human | individual identity, scope, expiry, action set, revocation evidence | deny missing/expired scope; no shared credential |
| Incident | P1–P4 detection; Human incident lead | detect/triage/contain/recover/verify/close/review with safe evidence | escalate severity; no customer content in incident record |
| Break glass | active P1/P2, Human authorization | primary recorder; if unavailable pre-established mTLS WORM alternate; revoke/reconcile | deny if both recorders unavailable; no verbal/local path |
| Secret rotation | scheduled/compromise; authorized operator | stage new secret, validate/restart, revoke old, evidence | deny unsafe overlap; no plaintext artifact |
| Unsupported environment | unsupported deployment detected; Human Operations | close traffic, preserve evidence, return to supported profile | no compatibility waiver/customer fork |
| TLS lifecycle | issuance/renewal/expiry warning; authorized operator | stage cert/key, hostname/chain/expiry verify, reload edge | P2/close expired edge; no unverified certificate |
| Monitoring fallback | monitor loss; Human Operations | incident, hourly edge/backend/DB/disk/storage/backup/TLS/release checks, <=4h | at expiry block writes/read-only only if dual gate; no renewal by silence |
| Vulnerability disposition | scan finding; Human Security Approver | Critical block; validate High exception scope/digest/expiry/retest, close/revoke | non-deployable; AI/scanner cannot approve |

## Evidence format

Each execution records safe runbook name, release/deployment reference, Human
authority reference, start/end, bounded outcome, correlation/incident reference,
and recovery/abort decision. It excludes secrets, object identities, customer
engineering content, request/response bodies, and raw exception detail.
