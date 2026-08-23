import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowDown, ArrowRight, ArrowUp, CheckCircle2, ClipboardList, Plus, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, ProjectFoundation, ProjectFoundationEstablished, ProjectFoundationInput, ProjectFoundationSourceCandidate, ProjectInputStanding, ProjectStage, Workspace } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

const stages: ProjectStage[] = ["definition", "preparation", "execution", "verification", "completion_readiness"];
const standings: ProjectInputStanding[] = ["missing", "received", "clarification_required", "not_applicable"];
const lines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);

function MutationMessage({ result }: { result: ApiResult<unknown> | null }) {
  if (!result || result.state === "success") return null;
  const message = result.state === "protected" ? "This operation is not available." : result.state === "invalid" ? "Check the supplied Project definition details." : result.state === "conflict" ? "The Project definition changed. Reload and try again." : "The Project definition service is unavailable.";
  return <p role="alert" className="form-message">{message}</p>;
}

export function ProjectFoundationPanel({ projectId, workspaces }: { projectId: number; workspaces: Workspace[] }) {
  const [foundation, setFoundation] = useState<ApiResult<ProjectFoundation> | null>(null);
  const [mutation, setMutation] = useState<ApiResult<unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [purpose, setPurpose] = useState("");
  const [basis, setBasis] = useState("");
  const [inScope, setInScope] = useState("");
  const [outScope, setOutScope] = useState("");
  const [criteria, setCriteria] = useState("");
  const [basisRationale, setBasisRationale] = useState("");
  const [editInputId, setEditInputId] = useState("");
  const [inputTitle, setInputTitle] = useState("");
  const [inputDescription, setInputDescription] = useState("");
  const [requiredStage, setRequiredStage] = useState<ProjectStage>("preparation");
  const [inputRationale, setInputRationale] = useState("");
  const [reorderRationale, setReorderRationale] = useState("");
  const [transitionInputId, setTransitionInputId] = useState("");
  const [targetStanding, setTargetStanding] = useState<ProjectInputStanding>("received");
  const [sourceKind, setSourceKind] = useState<"supporting_file" | "evidence">("supporting_file");
  const [sourceWorkspace, setSourceWorkspace] = useState("");
  const [sources, setSources] = useState<ApiResult<{ outcome:"success"; items:ProjectFoundationSourceCandidate[]; visible_count:number }> | null>(null);
  const [sourceId, setSourceId] = useState("");
  const [transitionRationale, setTransitionRationale] = useState("");
  const [targetStage, setTargetStage] = useState<ProjectStage>("preparation");
  const [stageRationale, setStageRationale] = useState("");

  const current = foundation?.state === "success" && foundation.data.availability === "established" ? foundation.data : null;
  const inputs = current?.inputs ?? [];
  const selectedTransition = inputs.find((item) => item.id === transitionInputId) ?? null;
  const selectedEdit = inputs.find((item) => item.id === editInputId) ?? null;

  const load = () => { setFoundation(null); void api.projectFoundation(projectId).then(setFoundation); };
  useEffect(load, [projectId]);
  useEffect(() => {
    if (!current) return;
    setPurpose(current.purpose); setBasis(current.engineering_basis);
    setInScope(current.in_scope.map((item) => item.statement).join("\n"));
    setOutScope(current.out_of_scope.map((item) => item.statement).join("\n"));
    setCriteria(current.completion_criteria.map((item) => item.statement).join("\n"));
    setTargetStage(current.next_stage_readiness.target_stage ?? current.stage);
  }, [current?.version]);
  useEffect(() => {
    if (!selectedEdit) { setInputTitle(""); setInputDescription(""); return; }
    setInputTitle(selectedEdit.title); setInputDescription(selectedEdit.description ?? ""); setRequiredStage(selectedEdit.required_by_stage);
  }, [selectedEdit]);

  async function execute(action: () => Promise<ApiResult<unknown>>) {
    setBusy(true); setMutation(null); const result = await action(); setMutation(result); setBusy(false);
    if (result.state === "success") load();
  }
  function saveFoundation(event: FormEvent) {
    event.preventDefault();
    void execute(() => api.putProjectFoundation(projectId, { expected_version: current?.version ?? 0, purpose, engineering_basis: basis, in_scope: lines(inScope), out_of_scope: lines(outScope), completion_criteria: lines(criteria), rationale: basisRationale }));
  }
  function saveInput(event: FormEvent) {
    event.preventDefault(); if (!current) return;
    const common = { expected_foundation_version: current.version, title: inputTitle, description: inputDescription.trim() || null, ordinal: selectedEdit?.ordinal ?? inputs.length, required_by_stage: requiredStage, rationale: inputRationale };
    void execute(() => selectedEdit ? api.updateProjectInput(projectId, selectedEdit.id, { ...common, expected_input_version: selectedEdit.version }) : api.createProjectInput(projectId, common));
  }
  function moveInput(input: ProjectFoundationInput, offset: number) {
    if (!current) return; const index = inputs.findIndex((item) => item.id === input.id); const target = index + offset; if (target < 0 || target >= inputs.length) return;
    const order = inputs.map((item) => item.id); [order[index], order[target]] = [order[target], order[index]];
    if (!reorderRationale.trim()) return;
    void execute(() => api.reorderProjectInputs(projectId, { expected_foundation_version: current.version, ordered_input_ids: order, rationale: reorderRationale }));
  }
  async function loadSources() {
    const workspaceId = sourceWorkspace ? Number(sourceWorkspace) : null;
    setSources(null); setSourceId(""); setSources(await api.projectInputSources(projectId, sourceKind, workspaceId));
  }
  function transitionInput(event: FormEvent) {
    event.preventDefault(); if (!current || !selectedTransition) return;
    const candidate = sources?.state === "success" ? sources.data.items.find((item) => item.source_id === sourceId) : undefined;
    void execute(() => api.transitionProjectInput(projectId, selectedTransition.id, { expected_foundation_version: current.version, expected_input_version: selectedTransition.version, target_standing: targetStanding, source_kind: targetStanding === "received" ? sourceKind : undefined, source_id: targetStanding === "received" ? candidate?.source_id : undefined, source_workspace_id: targetStanding === "received" ? candidate?.workspace_id : undefined, rationale: transitionRationale }));
  }
  function transitionStage(event: FormEvent) {
    event.preventDefault(); if (!current) return;
    void execute(() => api.transitionProjectStage(projectId, { expected_foundation_version: current.version, target_stage: targetStage, rationale: stageRationale }));
  }

  const sourceItems = sources?.state === "success" ? sources.data.items : [];
  const stageLabel = current?.stage.replaceAll("_", " ") ?? "definition";
  const blockerText = useMemo(() => current?.next_stage_readiness.blockers.map((item) => item.input_title ? `${item.code.replaceAll("_", " ")}: ${item.input_title}` : item.code.replaceAll("_", " ")) ?? [], [current]);

  return <section className="project-foundation" aria-labelledby="project-foundation-title">
    <div className="project-foundation-heading"><div><span className="eyebrow">Governed Project foundation</span><h2 id="project-foundation-title">Definition, scope, inputs and lifecycle</h2><p>Establish the Human-authored engineering basis, govern required inputs, and advance only when current canonical sources support readiness.</p></div><button type="button" className="button secondary compact" onClick={load}><RefreshCw size={15} />Reload</button></div>
    {!foundation ? <LoadingState /> : foundation.state === "protected" || foundation.state === "invalid" ? <ProtectedState /> : foundation.state !== "success" ? <ErrorState unavailable={foundation.state === "unavailable"} /> : <>
      {foundation.data.availability === "basis_not_established" ? <div className="foundation-callout"><ShieldCheck /><div><strong>Engineering basis not established</strong><span>Legacy Project data remains unchanged. Establish the foundation explicitly before lifecycle progression.</span></div></div> : null}
      <div className="foundation-grid">
        <Surface title={current ? "Engineering basis" : "Establish engineering basis"} subtitle="Human-authored canonical Project foundation"><form className="foundation-form" onSubmit={saveFoundation}><label>Project purpose<textarea value={purpose} onChange={(event) => setPurpose(event.target.value)} maxLength={2000} rows={3} required /></label><label>Engineering basis<textarea value={basis} onChange={(event) => setBasis(event.target.value)} maxLength={5000} rows={5} required /></label><div className="foundation-list-grid"><label>In scope <span>one item per line</span><textarea value={inScope} onChange={(event) => setInScope(event.target.value)} rows={5} required /></label><label>Out of scope <span>one item per line</span><textarea value={outScope} onChange={(event) => setOutScope(event.target.value)} rows={5} /></label><label>Completion criteria <span>one item per line</span><textarea value={criteria} onChange={(event) => setCriteria(event.target.value)} rows={5} required /></label></div><label>Human rationale<textarea value={basisRationale} onChange={(event) => setBasisRationale(event.target.value)} maxLength={2000} rows={2} required /></label><button className="button primary" disabled={busy}>{current ? "Save foundation" : "Establish foundation"}</button></form></Surface>
        <Surface title="Lifecycle readiness" subtitle={`Current stage · ${stageLabel}`}><div className="readiness-panel"><StatusBadge value={current?.next_stage_readiness.state ?? "not established"} />{current ? blockerText.length ? <ul>{blockerText.map((item) => <li key={item}>{item}</li>)}</ul> : <p><CheckCircle2 size={16} />The next stage has no current blockers.</p> : <EmptyState title="Basis not established" detail="Lifecycle readiness begins after the Project foundation is established." />}{current ? <form className="foundation-form" onSubmit={transitionStage}><label>Target stage<select aria-label="Target stage" value={targetStage} onChange={(event) => setTargetStage(event.target.value as ProjectStage)}>{stages.map((stage) => <option key={stage} value={stage}>{stage.replaceAll("_", " ")}</option>)}</select></label><label>Human transition rationale<textarea value={stageRationale} onChange={(event) => setStageRationale(event.target.value)} rows={2} required /></label><button className="button secondary" disabled={busy || targetStage === current.stage}><ArrowRight size={15} />Transition stage</button></form> : null}</div></Surface>
      </div>
      {current ? <div className="foundation-grid input-grid">
        <Surface title="Required engineering inputs" subtitle="Ordered, standing-aware and source-authorized"><label className="input-reorder-rationale">Human rationale for input ordering<textarea value={reorderRationale} onChange={(event) => setReorderRationale(event.target.value)} rows={2} maxLength={2000} /></label><div className="foundation-input-list">{inputs.length ? inputs.map((item, index) => <article key={item.id}><span className="input-ordinal">{index + 1}</span><div><strong>{item.title}</strong><span>Required by {item.required_by_stage.replaceAll("_", " ")} · Version {item.version}</span></div><StatusBadge value={item.standing} /><div className="input-order-actions"><button type="button" aria-label={`Move ${item.title} up`} disabled={index === 0 || busy || !reorderRationale.trim()} onClick={() => moveInput(item, -1)}><ArrowUp /></button><button type="button" aria-label={`Move ${item.title} down`} disabled={index === inputs.length - 1 || busy || !reorderRationale.trim()} onClick={() => moveInput(item, 1)}><ArrowDown /></button></div></article>) : <EmptyState title="No required inputs" detail="Add the first engineering input to make stage readiness explicit." />}</div></Surface>
        <Surface title={selectedEdit ? "Edit required input" : "Add required input"} subtitle="Human-defined Project requirement"><form className="foundation-form" onSubmit={saveInput}><label>Edit existing input<select aria-label="Edit existing required input" value={editInputId} onChange={(event) => setEditInputId(event.target.value)}><option value="">Create new input</option>{inputs.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Input title<input value={inputTitle} onChange={(event) => setInputTitle(event.target.value)} maxLength={200} required /></label><label>Description <span>(optional)</span><textarea value={inputDescription} onChange={(event) => setInputDescription(event.target.value)} maxLength={2000} rows={2} /></label><label>Required by stage<select value={requiredStage} onChange={(event) => setRequiredStage(event.target.value as ProjectStage)}>{stages.map((stage) => <option key={stage} value={stage}>{stage.replaceAll("_", " ")}</option>)}</select></label><label>Human rationale<textarea value={inputRationale} onChange={(event) => setInputRationale(event.target.value)} rows={2} required /></label><button className="button secondary" disabled={busy}><Plus size={15} />{selectedEdit ? "Save required input" : "Add required input"}</button></form></Surface>
        <Surface title="Update input standing" subtitle="Attach current authorized sources through selectors only"><form className="foundation-form" onSubmit={transitionInput}><label>Required input<select aria-label="Required input" value={transitionInputId} onChange={(event) => setTransitionInputId(event.target.value)} required><option value="">Select input</option>{inputs.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Target standing<select aria-label="Target standing" value={targetStanding} onChange={(event) => setTargetStanding(event.target.value as ProjectInputStanding)}>{standings.map((standing) => <option key={standing} value={standing}>{standing.replaceAll("_", " ")}</option>)}</select></label>{targetStanding === "received" ? <><label>Canonical source type<select aria-label="Canonical source type" value={sourceKind} onChange={(event) => setSourceKind(event.target.value as "supporting_file" | "evidence")}><option value="supporting_file">Supporting File</option><option value="evidence">Evidence</option></select></label><label>Engineering Workspace<select aria-label="Source Engineering Workspace" value={sourceWorkspace} onChange={(event) => setSourceWorkspace(event.target.value)}><option value="">Project-level / no Workspace</option>{workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.display_name}</option>)}</select></label><button type="button" className="button secondary compact" onClick={() => void loadSources()} disabled={busy}>Load authorized sources</button>{sources?.state === "protected" ? <ProtectedState /> : sources && sources.state !== "success" ? <ErrorState unavailable={sources.state === "unavailable"} /> : <label>Authorized source<select aria-label="Authorized source" value={sourceId} onChange={(event) => setSourceId(event.target.value)} required><option value="">Select current canonical source</option>{sourceItems.map((item) => <option key={`${item.kind}:${item.source_id}`} value={item.source_id}>{item.display_label}</option>)}</select></label>}</> : null}<label>Human rationale<textarea value={transitionRationale} onChange={(event) => setTransitionRationale(event.target.value)} rows={2} required /></label><button className="button primary" disabled={busy || !selectedTransition || (targetStanding === "received" && !sourceId)}><ClipboardList size={15} />Update standing</button></form></Surface>
      </div> : null}
      <MutationMessage result={mutation} />
    </>}
  </section>;
}
