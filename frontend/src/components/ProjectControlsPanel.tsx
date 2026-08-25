import { useEffect, useMemo, useState, type FormEvent } from "react";
import { CheckCircle2, ClipboardCheck, GitBranch, Plus, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, ChangeImpactTargetKind, ProjectControl, ProjectControlHistory, ProjectControlKind, Workspace } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

const kinds: { value: ProjectControlKind; label: string; detail: string }[] = [
  { value: "risk", label: "Risks", detail: "Uncertain future engineering impact" },
  { value: "issue", label: "Issues", detail: "Observed current problem — never an Activity blocker" },
  { value: "decision", label: "Decisions", detail: "Human-authoritative engineering choice" },
  { value: "change", label: "Changes", detail: "Human-recorded engineering change and bounded impacts" },
];
const targetKinds: { value: ChangeImpactTargetKind; label: string }[] = [
  { value: "activity", label: "Activity" }, { value: "milestone", label: "Milestone" },
  { value: "deliverable", label: "Deliverable" }, { value: "deliverable_revision", label: "Deliverable revision" },
  { value: "evidence", label: "Evidence" }, { value: "supporting_file", label: "Supporting file" },
];
const transitions: Record<ProjectControlKind, string[]> = { risk:["treated","accepted","closed"], issue:["resolved","closed"], decision:["accepted","superseded"], change:["confirmed","withdrawn"] };
const date = (value: string | null) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not recorded";

function ResultState({ result, retry }: { result: ApiResult<unknown> | null; retry?: () => void }) {
  if (!result) return <LoadingState label="Loading authorized Project controls…" />;
  if (result.state === "protected" || result.state === "invalid") return <ProtectedState />;
  if (result.state !== "success") return <ErrorState unavailable={result.state === "unavailable"} retry={retry} />;
  return null;
}

export function ProjectControlsPanel({ projectId, workspaces }: { projectId: number; workspaces: Workspace[] }) {
  const [active, setActive] = useState<ProjectControlKind>("risk");
  const [lists, setLists] = useState<Record<ProjectControlKind, ApiResult<{ items: ProjectControl[] }> | null>>({ risk: null, issue: null, decision: null, change: null });
  const [mutation, setMutation] = useState<ApiResult<unknown> | null>(null);
  const [history, setHistory] = useState<ApiResult<ProjectControlHistory> | null>(null);
  const [statement, setStatement] = useState(""); const [rationale, setRationale] = useState("");
  const [category, setCategory] = useState("engineering"); const [severity, setSeverity] = useState("medium"); const [observed, setObserved] = useState("");
  const [workspaceId, setWorkspaceId] = useState(""); const [changeId, setChangeId] = useState(""); const [impactKind, setImpactKind] = useState<ChangeImpactTargetKind>("activity"); const [targetId, setTargetId] = useState(""); const [impactStatement, setImpactStatement] = useState(""); const [impactRationale, setImpactRationale] = useState(""); const [confirmationRationale, setConfirmationRationale] = useState(""); const [transitionStanding, setTransitionStanding] = useState(""); const [transitionRationale, setTransitionRationale] = useState("");
  const [candidates, setCandidates] = useState<{ id: string; kind: ChangeImpactTargetKind; label: string; deliverableId?: string }[]>([]);
  const [busy, setBusy] = useState(false);

  const load = () => { void Promise.all(kinds.map(async ({ value }) => [value, await api.projectControls(projectId, value)] as const)).then((items) => setLists(Object.fromEntries(items) as typeof lists)); };
  useEffect(load, [projectId]);
  const controls = lists[active]; const changes = lists.change?.state === "success" ? lists.change.data.items : [];

  useEffect(() => {
    const workspace = workspaceId ? Number(workspaceId) : null;
    if (!workspace) { setCandidates([]); return; }
    void Promise.all([api.executionPlan(projectId), api.deliverables(projectId), api.evidence(projectId, workspace), api.supportingFiles(projectId, workspace)]).then(([plan, deliverables, evidence, files]) => {
      const next: { id: string; kind: ChangeImpactTargetKind; label: string; deliverableId?: string }[] = [];
      if (plan.state === "success" && plan.data.availability === "established") {
        plan.data.activities.filter((item) => item.workspace_id === null || item.workspace_id === workspace).forEach((item) => next.push({ id: item.id, kind: "activity", label: `Activity · ${item.title}` }));
        plan.data.milestones.forEach((item) => next.push({ id: item.id, kind: "milestone", label: `Milestone · ${item.title}` }));
      }
      if (deliverables.state === "success") deliverables.data.items.filter((item) => item.workspace_id === null || item.workspace_id === workspace).forEach((item) => { next.push({ id: item.id, kind: "deliverable", label: `Deliverable · ${item.code} — ${item.title}` }); next.push({ id: item.current_revision.id, kind: "deliverable_revision", deliverableId: item.id, label: `Deliverable revision · ${item.code} · ${item.current_revision.external_label}` }); });
      if (evidence.state === "success") evidence.data.items.forEach((item) => next.push({ id: item.id, kind: "evidence", label: `Evidence · ${item.source_reference}` }));
      if (files.state === "success") files.data.items.forEach((item) => next.push({ id: item.id, kind: "supporting_file", label: `Supporting file · ${item.safe_filename}` }));
      setCandidates(next); setTargetId("");
    });
  }, [projectId, workspaceId]);
  const eligibleTargets = useMemo(() => candidates.filter((item) => item.kind === impactKind), [candidates, impactKind]);

  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMutation(null);
    const common = { statement, rationale, workspace_id: workspaceId ? Number(workspaceId) : null };
    const payload = active === "risk" ? { ...common, category, likelihood: severity, impact: severity } : active === "issue" ? { ...common, observed_context: observed, severity } : active === "decision" ? { ...common, alternatives: [] } : common;
    const result = await api.createProjectControl(projectId, active, payload); setMutation(result); setBusy(false);
    if (result.state === "success") { setStatement(""); setRationale(""); setObserved(""); load(); }
  }
  async function createImpact(event: FormEvent) {
    event.preventDefault(); const selected = eligibleTargets.find((item) => item.id === targetId); if (!changeId || !selected) return;
    setBusy(true); const result = await api.createChangeImpact(projectId, changeId, { change_id: changeId, target_kind: selected.kind, target_id: selected.id, deliverable_id: selected.deliverableId, statement: impactStatement, rationale: impactRationale, expected_version: changes.find((item) => item.id === changeId)?.version }); setMutation(result); setBusy(false);
    if (result.state === "success") { setImpactStatement(""); setImpactRationale(""); load(); }
  }
  async function confirmImpact(control: ProjectControl, impact: ProjectControl["impacts"][number]) {
    if (!confirmationRationale.trim()) return;
    setBusy(true); const result = await api.confirmChangeImpact(projectId, impact.id, { expected_change_version: control.version, ...(impact.target_kind === "deliverable_revision" ? { deliverable_id: candidates.find((item) => item.id === impact.target_id)?.deliverableId } : {}), rationale: confirmationRationale }); setMutation(result); setBusy(false); if (result.state === "success") { setConfirmationRationale(""); load(); }
  }
  async function transition(control: ProjectControl) {
    if (!transitionStanding || !transitionRationale.trim()) return;
    setBusy(true); const result = await api.transitionProjectControl(projectId, active, control.id, { target_standing: transitionStanding, expected_version: control.version, rationale: transitionRationale }); setMutation(result); setBusy(false);
    if (result.state === "success") { setTransitionRationale(""); load(); }
  }

  return <section className="project-controls" aria-labelledby="project-controls-title">
    <div className="project-controls-heading"><div><span className="eyebrow">Governed Project controls</span><h2 id="project-controls-title">Risks, Issues, Decisions and Changes</h2><p>These are distinct engineering facts. Issues do not create or clear Activity blockers; potential impacts never mutate their target.</p></div><button className="button secondary compact" type="button" onClick={load}><RefreshCw size={15} />Reload</button></div>
    <div className="control-tabs" role="tablist" aria-label="Project control records">{kinds.map((item) => <button type="button" role="tab" aria-selected={active === item.value} className={active === item.value ? "active" : ""} key={item.value} onClick={() => { setActive(item.value); setHistory(null); }}>{item.label}</button>)}</div>
    <div className="project-controls-grid"><Surface title={`Record a ${kinds.find((item) => item.value === active)?.label.slice(0, -1)}`} subtitle="Human-authored, attributed and canonical"><form className="control-form" onSubmit={create}><label>Engineering statement<textarea value={statement} onChange={(event) => setStatement(event.target.value)} rows={3} maxLength={active === "risk" || active === "issue" ? 2000 : 4000} required /></label>{active === "issue" ? <label>Observed current context<textarea value={observed} onChange={(event) => setObserved(event.target.value)} rows={3} maxLength={4000} required /></label> : null}{active === "risk" ? <label>Risk category<input value={category} onChange={(event) => setCategory(event.target.value)} maxLength={80} required /></label> : null}{active === "risk" || active === "issue" ? <label>{active === "risk" ? "Likelihood and impact" : "Severity"}<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label> : null}<label>Engineering Workspace <span>(optional)</span><select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}><option value="">Project-wide</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.display_name}</option>)}</select></label><label>Human rationale<textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={2} maxLength={4000} required /></label><button className="button primary" disabled={busy}><Plus size={15} />Record {active}</button></form>{mutation && mutation.state !== "success" ? <p role="alert" className="form-message">{mutation.state === "protected" ? "This action is not available." : mutation.state === "invalid" ? "Check the Human-authored control details." : "The control could not be completed."}</p> : null}</Surface>
      <Surface title={kinds.find((item) => item.value === active)?.label ?? "Controls"} subtitle={kinds.find((item) => item.value === active)?.detail}>{controls?.state === "success" ? controls.data.items.length ? <div className="control-record-list">{controls.data.items.map((item) => <article key={item.id}><div><strong>{item.statement}</strong><span><StatusBadge value={item.standing} /> · Version {item.version}</span><p>{active === "issue" ? item.observed_context : item.rationale || item.disposition || "No further disposition recorded."}</p>{item.predecessor_id ? <p className="control-lineage"><GitBranch size={14} />Historical successor relationship preserved.</p> : null}</div><div className="record-actions"><button type="button" className="button secondary compact" onClick={() => void api.projectControlHistory(projectId, active, item.id).then(setHistory)}>History</button></div>{!(["closed","withdrawn","superseded"] as string[]).includes(item.standing) ? <div className="control-transition"><label>Human lifecycle action<select aria-label={`Human lifecycle action for ${item.statement}`} value={transitionStanding} onChange={(event) => setTransitionStanding(event.target.value)}><option value="">Select authorized transition</option>{transitions[active].filter((standing) => standing !== item.standing).map((standing) => <option key={standing} value={standing}>{standing}</option>)}</select></label><label>Human transition rationale<textarea aria-label={`Human transition rationale for ${item.statement}`} value={transitionRationale} onChange={(event) => setTransitionRationale(event.target.value)} rows={2} maxLength={4000} required /></label><button type="button" className="button secondary compact" disabled={busy || !transitionStanding || !transitionRationale.trim()} onClick={() => void transition(item)}>Record Human transition</button></div> : null}{active === "change" ? <div className="impact-list">{item.impacts.length ? item.impacts.map((impact) => <div key={impact.id} className="impact-item"><span><StatusBadge value={impact.standing} /> {impact.target_kind.replaceAll("_", " ")} · protected canonical reference</span><p>{impact.statement}</p>{impact.standing === "potential" ? <><p className="form-hint">Potential impact is not confirmed engineering truth and does not mutate the target.</p><label className="impact-confirmation">Human confirmation rationale<textarea value={confirmationRationale} onChange={(event) => setConfirmationRationale(event.target.value)} rows={2} maxLength={4000} required /></label><button type="button" className="button secondary compact" disabled={busy || !confirmationRationale.trim()} onClick={() => void confirmImpact(item, impact)}><CheckCircle2 size={14} />Human confirm impact</button></> : <p className="form-hint"><ShieldCheck size={14} />Explicit Human confirmation recorded.</p>}</div>) : <p className="form-hint">No Change Impacts recorded.</p>}</div> : null}</article>)}</div> : <EmptyState title={`No ${active}s recorded`} detail="Use the Human-authored form to record the first authorized Project control." /> : <ResultState result={controls} retry={load} />}</Surface></div>
    {active === "change" ? <Surface title="Add potential Change Impact" subtitle="Choose an already authorized canonical target; the server reauthorizes it before persistence."><form className="control-form impact-form" onSubmit={createImpact}><label>Change<select value={changeId} onChange={(event) => setChangeId(event.target.value)} required><option value="">Select Change</option>{changes.map((item) => <option key={item.id} value={item.id}>{item.statement}</option>)}</select></label><label>Engineering Workspace<select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)} required><option value="">Select Workspace</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.display_name}</option>)}</select></label><label>Target type<select value={impactKind} onChange={(event) => setImpactKind(event.target.value as ChangeImpactTargetKind)}>{targetKinds.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>Authorized target<select value={targetId} onChange={(event) => setTargetId(event.target.value)} required><option value="">Select authorized target</option>{eligibleTargets.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label><label>Potential impact statement<textarea value={impactStatement} onChange={(event) => setImpactStatement(event.target.value)} maxLength={2000} rows={3} required /></label><label>Human rationale<textarea value={impactRationale} onChange={(event) => setImpactRationale(event.target.value)} maxLength={4000} rows={2} required /></label><button className="button primary" disabled={busy || !targetId}><ClipboardCheck size={15} />Record potential impact</button></form></Surface> : null}
    {history?.state === "success" ? <Surface title="Immutable control history" subtitle="Historical records are not editable"><ol className="control-history">{history.data.items.map((item) => <li key={`${item.aggregate_version}-${item.event_type}`}><strong>Version {item.aggregate_version}</strong><span>{item.event_type.replaceAll("_", " ")} · {date(item.occurred_at)}</span></li>)}</ol></Surface> : history ? <ResultState result={history} /> : null}
  </section>;
}
