#!/usr/bin/env python3
"""Fail-closed PATCH-058 release-dossier generator and validator."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, pathlib, re, sys
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
REV = re.compile(r"^[0-9a-f]{40}$")

def digest(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return "sha256:"+h.hexdigest()

def timestamp(value):
    x=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if x.tzinfo is None: raise ValueError("timestamp must include timezone")
    return x.astimezone(dt.timezone.utc)

def pairs(values):
    out={}
    for value in values:
        if "=" not in value: raise ValueError("expected NAME=PATH")
        name,raw=value.split("=",1); p=pathlib.Path(raw)
        if not name or name in out or not p.is_file(): raise ValueError(f"invalid evidence: {value}")
        out[name]={"reference":raw,"digest":digest(p)}
    return out

def approval(raw):
    status,ref=raw.split("=",1)
    if status not in {"pending","approved","rejected"}: raise ValueError("invalid approval status")
    item={"status":status,"reference":ref}
    if status=="approved":
        p=pathlib.Path(ref)
        if not p.is_file(): raise ValueError("approved evidence file missing")
        item["digest"]=digest(p)
    return item
def validate(d, now):
    required={"schema_version","release_id","source_commit","artifacts","build_inputs","qualification_evidence","security_evidence","exceptions","sboms","provenance","signature_verification","human_signing_authorization","human_release_approval","created_at"}
    if set(d)!=required: raise ValueError(f"dossier keys mismatch: missing={sorted(required-set(d))} extra={sorted(set(d)-required)}")
    if d["schema_version"]!="v1" or not d["release_id"] or not REV.fullmatch(d["source_commit"]): raise ValueError("invalid dossier identity")
    timestamp(d["created_at"])
    for section in ("artifacts","build_inputs","qualification_evidence","security_evidence","exceptions","sboms"):
        if not isinstance(d[section],dict) or not d[section]: raise ValueError(f"{section} must be non-empty")
        for name,item in d[section].items(): verify_evidence(section+"."+name,item)
    verify_evidence("provenance",d["provenance"]); verify_evidence("signature_verification",d["signature_verification"])
    for key in ("human_signing_authorization","human_release_approval"):
        a=d[key]
        if a.get("status") not in {"pending","approved","rejected"} or not a.get("reference"): raise ValueError(f"invalid {key}")
        if a["status"]=="approved": verify_evidence(key,a)
    gate=json.loads(pathlib.Path(d["security_evidence"]["vulnerability_gate"]["reference"]).read_text())
    if gate.get("result")!="PASS" or gate.get("blockingFindings"): raise ValueError("vulnerability gate is not PASS with zero blockers")
    backend=d["artifacts"]["backend"]["digest"]
    if gate.get("artifactDigest")!=backend: raise ValueError("vulnerability gate artifact mismatch")
    exceptions=json.loads(pathlib.Path(d["exceptions"]["high_findings"]["reference"]).read_text())
    for e in exceptions:
        if e.get("status")!="active" or e.get("artifact_digest")!=backend or timestamp(e["expires_at"])<=now: raise ValueError("inactive, mismatched or expired High exception")
    return True

def verify_evidence(name,item):
    if set(item)-{"reference","digest","status"}: raise ValueError(f"unexpected evidence fields: {name}")
    ref=item.get("reference"); expected=item.get("digest")
    if not ref or not SHA.fullmatch(expected or ""): raise ValueError(f"invalid evidence descriptor: {name}")
    p=pathlib.Path(ref)
    if not p.is_file() or digest(p)!=expected: raise ValueError(f"missing or substituted evidence: {name}")
def make_parser():
    root=argparse.ArgumentParser(); sub=root.add_subparsers(dest="command",required=True)
    g=sub.add_parser("generate"); g.add_argument("--release-id",required=True); g.add_argument("--source-commit",required=True); g.add_argument("--created-at",required=True); g.add_argument("--output",required=True)
    for flag in ("artifact","build-input","qualification-evidence","security-evidence","exception","sbom"): g.add_argument("--"+flag,action="append",default=[])
    g.add_argument("--provenance",required=True); g.add_argument("--signature-verification",required=True); g.add_argument("--human-signing-authorization",required=True); g.add_argument("--human-release-approval",required=True)
    v=sub.add_parser("verify"); v.add_argument("--dossier",required=True); v.add_argument("--now",required=True)
    return root

def main():
    a=make_parser().parse_args()
    try:
        if a.command=="generate":
            d={"schema_version":"v1","release_id":a.release_id,"source_commit":a.source_commit,"artifacts":pairs(a.artifact),"build_inputs":pairs(a.build_input),"qualification_evidence":pairs(a.qualification_evidence),"security_evidence":pairs(a.security_evidence),"exceptions":pairs(a.exception),"sboms":pairs(a.sbom),"provenance":pairs(["x="+a.provenance])["x"],"signature_verification":pairs(["x="+a.signature_verification])["x"],"human_signing_authorization":approval(a.human_signing_authorization),"human_release_approval":approval(a.human_release_approval),"created_at":timestamp(a.created_at).isoformat().replace("+00:00","Z")}
            pathlib.Path(a.output).write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); print("dossier-generated",digest(a.output)); return 0
        d=json.loads(pathlib.Path(a.dossier).read_text()); validate(d,timestamp(a.now)); print("dossier-verified",digest(a.dossier)); return 0
    except (OSError,ValueError,json.JSONDecodeError,KeyError) as e:
        print("BLOCK:",e,file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())