import copy, datetime as dt, hashlib, importlib.util, json, pathlib, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("dossier",ROOT/"ops/scripts/patch058-release-dossier.py")
M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
NOW=dt.datetime(2026,9,27,9,0,tzinfo=dt.timezone.utc)

def ev(path): return {"reference":str(path),"digest":M.digest(path)}
class DossierTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.p=pathlib.Path(self.t.name)
  def f(name,data):
   x=self.p/name; x.write_text(json.dumps(data) if not isinstance(data,str) else data); return x
  self.backend=f("backend","candidate"); self.lock=f("lock","lock")
  self.qual=f("qual",{"result":"PASS"}); self.sbom=f("sbom",{"bomFormat":"CycloneDX"})
  self.prov=f("prov",{"_type":"https://in-toto.io/Statement/v1"}); self.sig=f("sig",{"verified":True})
  self.exc=f("exc",[{"status":"active","artifact_digest":M.digest(self.backend),"expires_at":"2026-10-27T07:58:25Z"}])
  self.gate=f("gate",{"result":"PASS","blockingFindings":[],"artifactDigest":M.digest(self.backend)})
  self.d={"schema_version":"v1","release_id":"p058-test","source_commit":"a"*40,
   "artifacts":{"backend":ev(self.backend)},"build_inputs":{"lock":ev(self.lock)},
   "qualification_evidence":{"backend":ev(self.qual)},"security_evidence":{"vulnerability_gate":ev(self.gate)},
   "exceptions":{"high_findings":ev(self.exc)},"sboms":{"backend":ev(self.sbom)},"provenance":ev(self.prov),
   "signature_verification":ev(self.sig),"human_signing_authorization":{"status":"pending","reference":"protected-environment"},
   "human_release_approval":{"status":"pending","reference":"human-release-authority"},"created_at":"2026-09-27T08:00:00Z"}
 def tearDown(self): self.t.cleanup()
 def blocked(self,d):
  with self.assertRaises(ValueError): M.validate(d,NOW)
 def test_valid_candidate(self): self.assertTrue(M.validate(self.d,NOW))
 def test_missing_mandatory_evidence_blocks(self):
  d=copy.deepcopy(self.d); del d["sboms"]; self.blocked(d)
 def test_substituted_evidence_blocks(self):
  d=copy.deepcopy(self.d); self.sbom.write_text("tampered"); self.blocked(d)
 def test_gate_artifact_mismatch_blocks(self):
  d=copy.deepcopy(self.d); self.gate.write_text(json.dumps({"result":"PASS","blockingFindings":[],"artifactDigest":"sha256:"+"0"*64})); d["security_evidence"]["vulnerability_gate"]=ev(self.gate); self.blocked(d)
 def test_blocking_finding_blocks(self):
  d=copy.deepcopy(self.d); self.gate.write_text(json.dumps({"result":"FAIL","blockingFindings":["CVE-X"],"artifactDigest":M.digest(self.backend)})); d["security_evidence"]["vulnerability_gate"]=ev(self.gate); self.blocked(d)
 def test_expired_exception_blocks(self):
  d=copy.deepcopy(self.d); self.exc.write_text(json.dumps([{"status":"active","artifact_digest":M.digest(self.backend),"expires_at":"2026-09-26T00:00:00Z"}])); d["exceptions"]["high_findings"]=ev(self.exc); self.blocked(d)
 def test_exception_for_other_artifact_blocks(self):
  d=copy.deepcopy(self.d); self.exc.write_text(json.dumps([{"status":"active","artifact_digest":"sha256:"+"1"*64,"expires_at":"2026-10-27T00:00:00Z"}])); d["exceptions"]["high_findings"]=ev(self.exc); self.blocked(d)
 def test_approved_human_evidence_requires_digest(self):
  d=copy.deepcopy(self.d); d["human_release_approval"]={"status":"approved","reference":"missing-file"}; self.blocked(d)
 def test_rejected_is_not_silently_approved(self):
  d=copy.deepcopy(self.d); d["human_release_approval"]={"status":"rejected","reference":"human-release-authority"}; self.assertTrue(M.validate(d,NOW))
if __name__=="__main__": unittest.main()