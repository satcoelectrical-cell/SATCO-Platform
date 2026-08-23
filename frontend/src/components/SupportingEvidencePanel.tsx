import { useEffect, useRef, useState, type FormEvent } from "react";
import { Download, FileUp, Link2, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, EvidenceRecord, SupportingFilePage } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

const MAX_BYTES = 26_214_400;
const ACCEPTED = ".pdf,.txt,.csv,.png,.jpg,.jpeg,.docx,.xlsx";

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click();
  URL.revokeObjectURL(url);
}

export function SupportingEvidencePanel({ projectId, workspaceId }: { projectId: number; workspaceId: number }) {
  const [files, setFiles] = useState<ApiResult<SupportingFilePage> | null>(null);
  const [evidence, setEvidence] = useState<ApiResult<{ items: EvidenceRecord[] }> | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [evidenceId, setEvidenceId] = useState("");
  const [uploadRationale, setUploadRationale] = useState("");
  const [linkRationale, setLinkRationale] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = () => {
    setFiles(null); setEvidence(null);
    void api.supportingFiles(projectId, workspaceId).then(setFiles);
    void api.evidence(projectId, workspaceId).then(setEvidence);
  };
  useEffect(refresh, [projectId, workspaceId]);

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile || !uploadRationale.trim()) return;
    if (selectedFile.size > MAX_BYTES) { setMessage("The selected file exceeds the 25 MiB limit."); return; }
    setBusy(true); setMessage("Uploading to private quarantine…");
    const result = await api.uploadSupportingFile(projectId, workspaceId, selectedFile, uploadRationale.trim());
    if (result.state === "success") {
      setMessage("Upload received. Availability follows the independent scanner result; it is not engineering approval.");
      setSelectedFile(null); setUploadRationale("");
      if (fileInput.current) fileInput.current.value = "";
      refresh();
    } else setMessage(result.state === "protected" ? "This upload is not available in the current scope." : result.state === "invalid" ? "The file or upload details are invalid." : "The private upload service is unavailable.");
    setBusy(false);
  }

  async function link(event: FormEvent) {
    event.preventDefault();
    const record = evidence?.state === "success" ? evidence.data.items.find((item) => item.id === evidenceId) : undefined;
    if (!record || !selectedAssets.length || !linkRationale.trim()) return;
    setBusy(true); setMessage("Reauthorizing the exact Evidence and Supporting File set…");
    const result = await api.linkSupportingFiles(record.id, record.version, selectedAssets, linkRationale.trim());
    setMessage(result.state === "success" ? "Supporting Files linked to proposed Evidence. This does not accept the Evidence or approve its content." : result.state === "protected" ? "The Evidence or Supporting File set is no longer available." : result.state === "conflict" ? "The Evidence changed. Refresh and review its current version." : "The link operation could not be completed.");
    if (result.state === "success") { setSelectedAssets([]); setLinkRationale(""); refresh(); }
    setBusy(false);
  }

  async function download(assetId: string, filename: string) {
    setMessage("Reauthorizing attachment download…");
    const result = await api.downloadSupportingFile(assetId, projectId, workspaceId);
    if (result.state === "success") { saveBlob(result.data, filename); setMessage("Authorized attachment download started."); }
    else setMessage(result.state === "protected" ? "This attachment is not available." : "The attachment could not be downloaded.");
  }

  const visible = files?.state === "success" ? files.data.items : [];
  const proposed = evidence?.state === "success" ? evidence.data.items.filter((item) => item.lifecycle === "proposed") : [];
  const available = visible.filter((item) => item.lifecycle === "available");
  const toggle = (id: string) => setSelectedAssets((now) => now.includes(id) ? now.filter((item) => item !== id) : [...now, id].sort());

  return <section className="supporting-evidence" aria-labelledby="supporting-evidence-title">
    <div className="supporting-evidence-heading"><div><span className="eyebrow">Governed source intake</span><h2 id="supporting-evidence-title">Supporting Evidence</h2><p>Files remain non-authoritative supporting material. “Available” means scanner-cleared for governed use, not accepted engineering knowledge.</p></div><ShieldCheck aria-hidden="true" /></div>
    <div className="supporting-evidence-grid">
      <Surface title="Private upload" subtitle="One bounded file; explicit Human rationale"><form className="supporting-form" onSubmit={upload}><label>Supporting file<input ref={fileInput} type="file" accept={ACCEPTED} required onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} /></label><span className="form-hint">PDF, text, CSV, PNG, JPEG, DOCX or XLSX · maximum 25 MiB · no executable or macro content.</span><label>Upload rationale<textarea required minLength={1} maxLength={2000} rows={3} value={uploadRationale} onChange={(event) => setUploadRationale(event.target.value)} /></label><button className="button primary" disabled={busy || !selectedFile || !uploadRationale.trim()}><FileUp size={16} />Upload to quarantine</button></form></Surface>
      <Surface title="Authorized Supporting Files" subtitle="Current Project / Workspace only">{!files ? <LoadingState label="Loading authorized Supporting Files…" /> : files.state === "protected" ? <ProtectedState /> : files.state !== "success" ? <ErrorState unavailable={files.state === "unavailable"} /> : !visible.length ? <EmptyState title="No Supporting Files yet" detail="Upload a real engineering source to begin the governed intake flow." /> : <div className="supporting-file-list">{visible.map((item) => <article key={item.id}><label><input type="checkbox" disabled={item.lifecycle !== "available"} checked={selectedAssets.includes(item.id)} onChange={() => toggle(item.id)} aria-label={`Select ${item.safe_filename} for Evidence`} /><span><strong>{item.safe_filename}</strong><small>{item.media_type} · {(item.byte_size / 1024).toFixed(1)} KiB · Version {item.version}</small></span></label><StatusBadge value={item.lifecycle} />{item.lifecycle === "available" ? <button type="button" className="button secondary compact" onClick={() => void download(item.id, item.safe_filename)}><Download size={15} />Download</button> : null}</article>)}</div>}</Surface>
      <Surface title="Link to proposed Evidence" subtitle="Exact current set; linkage is not acceptance"><form className="supporting-form" onSubmit={link}><label>Proposed Evidence<select value={evidenceId} onChange={(event) => setEvidenceId(event.target.value)} required><option value="">Select proposed Evidence</option>{proposed.map((item) => <option key={item.id} value={item.id}>{item.supported_fact}</option>)}</select></label>{evidence?.state === "success" && !proposed.length ? <p className="form-hint">Create proposed Evidence in this Workspace before linking Supporting Files.</p> : null}<p className="form-hint">{selectedAssets.length} of {available.length} available file(s) selected.</p><label>Link rationale<textarea required minLength={1} maxLength={2000} rows={3} value={linkRationale} onChange={(event) => setLinkRationale(event.target.value)} /></label><button className="button secondary" disabled={busy || !evidenceId || !selectedAssets.length || !linkRationale.trim()}><Link2 size={16} />Link exact set</button></form></Surface>
    </div><p className="supporting-live" aria-live="polite" role="status">{message}</p>
  </section>;
}
