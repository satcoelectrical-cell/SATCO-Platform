import { useEffect, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowUpRight, Bot, BriefcaseBusiness, CalendarClock, FileText, FolderKanban, Gauge, Layers3, Plus } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ApiResult, Capture, Customer, Paginated, Project, Workspace } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "../components/States";
import { PageHeader, Surface } from "../components/Page";

function ResultBoundary<T>({ result, children, empty }: { result: ApiResult<T> | null; children: (data: T) => React.ReactNode; empty?: (data: T) => boolean }) {
  if (!result) return <LoadingState />;
  if (result.state === "protected" || result.state === "invalid") return <ProtectedState />;
  if (result.state !== "success") return <ErrorState unavailable={result.state === "unavailable"} />;
  if (empty?.(result.data)) return <EmptyState title="Nothing visible here yet" detail="Use the available action to begin authorized engineering work." />;
  return children(result.data);
}

function MutationState({ result }: { result: ApiResult<unknown> | null }) {
  if (!result || result.state === "success") return null;
  return <p className="form-message" role="alert">{result.state === "invalid" ? "Check the supplied engineering details." : result.state === "protected" ? "This operation is not available." : "The operation could not be completed."}</p>;
}

export function ProjectsPage() {
  const [projects, setProjects] = useState<ApiResult<Paginated<Project>> | null>(null);
  const [customers, setCustomers] = useState<ApiResult<Paginated<Customer>> | null>(null);
  const [customerResult, setCustomerResult] = useState<ApiResult<Customer> | null>(null);
  const [projectResult, setProjectResult] = useState<ApiResult<Project> | null>(null);
  const [customerName, setCustomerName] = useState("");
  const [customerCompany, setCustomerCompany] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [editCustomerId, setEditCustomerId] = useState("");
  const [projectName, setProjectName] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = () => { void api.projects().then(setProjects); void api.customers().then(setCustomers); };
  useEffect(refresh, []);

  async function createCustomer(event: FormEvent) {
    event.preventDefault(); setBusy(true);
    const result = await api.createCustomer({ name: customerName, company: customerCompany || null, phone: customerPhone || null, email: customerEmail || null }); setCustomerResult(result);
    if (result.state === "success") { setCustomerName(""); setCustomerCompany(""); setCustomerPhone(""); setCustomerEmail(""); setCustomerId(String(result.data.id)); refresh(); }
    setBusy(false);
  }
  async function updateCustomer(event: FormEvent) {
    event.preventDefault(); if (!editCustomerId) return; setBusy(true);
    const result = await api.updateCustomer(Number(editCustomerId), { name: customerName, company: customerCompany || null, phone: customerPhone || null, email: customerEmail || null }); setCustomerResult(result);
    if (result.state === "success") refresh(); setBusy(false);
  }
  function selectCustomerForEdit(value: string) {
    setEditCustomerId(value); const selected = customerItems.find((item) => item.id === Number(value));
    setCustomerName(selected?.name ?? ""); setCustomerCompany(selected?.company ?? ""); setCustomerPhone(selected?.phone ?? ""); setCustomerEmail(selected?.email ?? "");
  }
  async function createProject(event: FormEvent) {
    event.preventDefault(); setBusy(true);
    const result = await api.createProject({ name: projectName, customer_id: Number(customerId) }); setProjectResult(result);
    if (result.state === "success") { setProjectName(""); refresh(); }
    setBusy(false);
  }

  const customerItems = customers?.state === "success" ? customers.data.items : [];
  return <div className="page"><PageHeader eyebrow="Authorized portfolio" title="Projects" description="Start with a Customer, create the Project, then enter its trusted engineering context." />
    <div className="bootstrap-grid"><Surface title="1 · Customer" subtitle="Organization-scoped canonical Customer"><form className="bootstrap-form" onSubmit={editCustomerId ? updateCustomer : createCustomer}><label>Edit existing Customer<select aria-label="Edit existing Customer" value={editCustomerId} onChange={(event) => selectCustomerForEdit(event.target.value)}><option value="">Create new Customer</option>{customerItems.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}</select></label><label>Customer name<input value={customerName} onChange={(event) => setCustomerName(event.target.value)} minLength={1} maxLength={200} required /></label><label>Company <span>(optional)</span><input value={customerCompany} onChange={(event) => setCustomerCompany(event.target.value)} maxLength={200} /></label><div className="form-row"><label>Phone <span>(optional)</span><input value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} maxLength={64} /></label><label>Email <span>(optional)</span><input type="email" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} maxLength={320} /></label></div><button className="button secondary" disabled={busy}><Plus size={16} />{editCustomerId ? "Save Customer" : "Create Customer"}</button><MutationState result={customerResult} /></form></Surface>
      <Surface title="2 · Project" subtitle="Select an authorized Customer"><form className="bootstrap-form" onSubmit={createProject}><label>Customer<select value={customerId} onChange={(event) => setCustomerId(event.target.value)} required><option value="">Select Customer</option>{customerItems.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}</select></label><label>Project name<input value={projectName} onChange={(event) => setProjectName(event.target.value)} minLength={1} maxLength={200} required /></label><button className="button primary" disabled={busy || !customerItems.length}><Plus size={16} />Create Project</button>{!customerItems.length && customers?.state === "success" ? <p className="form-hint">Create the first Customer to enable Project creation.</p> : null}<MutationState result={projectResult} /></form></Surface></div>
    <ResultBoundary result={projects} empty={(data) => !data.items.length}>{(data) => <div className="project-cards">{data.items.map((project) => <Link className="project-card surface" to={`/projects/${project.id}`} key={project.id}><div className="project-card-top"><span className="widget-icon"><FolderKanban /></span><StatusBadge value={project.status} /></div><span className="eyebrow">{project.project_code}</span><h2>{project.name}</h2><p>{project.description || project.customer.name}</p><div className="project-metrics"><span><Gauge />{project.progress}% complete</span><span><CalendarClock />{project.target_completion_date || "No target date"}</span></div><div className="progress-track"><i style={{ width: `${project.progress}%` }} /></div><span className="text-link">Open engineering workspace<ArrowUpRight size={16} /></span></Link>)}</div>}</ResultBoundary></div>;
}

export function ProjectWorkspacePage() {
  const id = Number(useParams().projectId);
  const [project, setProject] = useState<ApiResult<Project> | null>(null);
  const [workspaces, setWorkspaces] = useState<ApiResult<{ items: Workspace[]; total: number }> | null>(null);
  const [captures, setCaptures] = useState<ApiResult<{ items: Capture[]; total: number }> | null>(null);
  const [workspaceId, setWorkspaceId] = useState(""); const [discipline, setDiscipline] = useState("electrical");
  const [content, setContent] = useState(""); const [sourceKind, setSourceKind] = useState("observation");
  const [workspaceResult, setWorkspaceResult] = useState<ApiResult<Workspace> | null>(null); const [captureResult, setCaptureResult] = useState<ApiResult<Capture> | null>(null); const [busy, setBusy] = useState(false);
  const [projectName, setProjectName] = useState(""); const [projectDescription, setProjectDescription] = useState(""); const [projectPriority, setProjectPriority] = useState("medium"); const [projectUpdateResult, setProjectUpdateResult] = useState<ApiResult<Project> | null>(null);
  const refresh = () => { if (Number.isInteger(id) && id > 0) { void api.project(id).then(setProject); void api.workspaces(id).then(setWorkspaces); void api.captures(id).then(setCaptures); } };
  useEffect(refresh, [id]);
  useEffect(() => { if (project?.state === "success") { setProjectName(project.data.name); setProjectDescription(project.data.description ?? ""); setProjectPriority(project.data.priority); } }, [project]);

  async function createWorkspace(event: FormEvent) { event.preventDefault(); setBusy(true); const result = await api.createWorkspace(id, { discipline }); setWorkspaceResult(result); if (result.state === "success") { setWorkspaceId(String(result.data.id)); refresh(); } setBusy(false); }
  async function createCapture(event: FormEvent) { event.preventDefault(); setBusy(true); const result = await api.createCapture({ project_id: id, workspace_id: Number(workspaceId), source_kind: sourceKind, original_content: content }); setCaptureResult(result); if (result.state === "success") { setContent(""); refresh(); } setBusy(false); }
  async function updateProject(event: FormEvent) { event.preventDefault(); setBusy(true); const result = await api.updateProject(id, { name: projectName, description: projectDescription || null, priority: projectPriority }); setProjectUpdateResult(result); if (result.state === "success") refresh(); setBusy(false); }

  const workspaceItems = workspaces?.state === "success" ? workspaces.data.items : [];
  return <div className="page"><ResultBoundary result={project}>{(currentProject) => <><Link className="text-link back-link" to="/projects"><ArrowLeft size={16} />All Projects</Link><PageHeader eyebrow={`${currentProject.project_code} · ${currentProject.customer.name}`} title={currentProject.name} description={currentProject.description || "Authorized Project engineering workspace."} action={<StatusBadge value={currentProject.status} />} /><div className="workspace-summary"><Surface><span className="eyebrow">Progress</span><strong className="hero-metric">{currentProject.progress}%</strong><div className="progress-track"><i style={{ width: `${currentProject.progress}%` }} /></div></Surface><Surface><span className="eyebrow">Priority</span><strong className="hero-metric small">{currentProject.priority}</strong><span>{currentProject.primary_assignee?.full_name || currentProject.primary_assignee?.username || "Unassigned"}</span></Surface></div>
    <div className="bootstrap-grid"><Surface title="Project basics" subtitle="Edit existing canonical Project fields"><form className="bootstrap-form" onSubmit={updateProject}><label>Project name<input value={projectName} onChange={(event) => setProjectName(event.target.value)} minLength={1} maxLength={200} required /></label><label>Description <span>(optional)</span><textarea value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} maxLength={5000} rows={3} /></label><label>Priority<select value={projectPriority} onChange={(event) => setProjectPriority(event.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></label><button className="button secondary" disabled={busy}>Save Project</button><MutationState result={projectUpdateResult} /></form></Surface><Surface title="3 · Engineering Workspace" subtitle="Create or select a discipline context"><form className="bootstrap-form" onSubmit={createWorkspace}><label>Discipline<select value={discipline} onChange={(event) => setDiscipline(event.target.value)}><option value="electrical">Electrical</option><option value="mechanical">Mechanical</option><option value="instrumentation">Instrumentation</option><option value="civil">Civil</option><option value="process">Process</option></select></label><button className="button secondary" disabled={busy}><Plus size={16} />Create Workspace</button><MutationState result={workspaceResult} /></form></Surface>
      <Surface title="4 · Engineering Capture" subtitle="Record real engineering experience"><form className="bootstrap-form" onSubmit={createCapture}><label>Workspace<select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)} required><option value="">Select Workspace</option>{workspaceItems.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.display_name}</option>)}</select></label><label>Source kind<select value={sourceKind} onChange={(event) => setSourceKind(event.target.value)}><option value="observation">Observation</option><option value="discussion_note">Discussion note</option><option value="field_note">Field note</option><option value="review_note">Review note</option></select></label><label>Capture content<textarea value={content} onChange={(event) => setContent(event.target.value)} minLength={1} maxLength={10000} rows={5} required /></label><button className="button primary" disabled={busy || !workspaceItems.length}><Plus size={16} />Create Capture</button>{!workspaceItems.length && workspaces?.state === "success" ? <p className="form-hint">Create a Workspace before recording a Capture.</p> : null}<MutationState result={captureResult} /></form></Surface></div>
    <div className="split-grid"><Surface title="Discipline Workspaces" subtitle="Canonical Project context"><ResultBoundary result={workspaces} empty={(data) => !data.items.length}>{(data) => <div className="record-list">{data.items.map((workspace) => <button type="button" className="record-button" key={workspace.id} onClick={() => setWorkspaceId(String(workspace.id))}><span className="widget-icon"><Layers3 /></span><div><strong>{workspace.display_name}</strong><span>{workspace.discipline} · Version {workspace.version}</span></div><StatusBadge value={workspace.status} /></button>)}</div>}</ResultBoundary></Surface><Surface title="Recent Captures" subtitle="Authorized engineering experience"><ResultBoundary result={captures} empty={(data) => !data.items.length}>{(data) => <div className="record-list">{data.items.slice(0, 8).map((capture) => <article key={capture.id}><span className="widget-icon"><BriefcaseBusiness /></span><div><strong>{capture.source_kind.replaceAll("_", " ")}</strong><span>{capture.discipline || "General"} · Version {capture.version}</span></div><div className="record-actions"><Link className="button secondary compact" aria-label={`Create Technical Report from ${capture.source_kind.replaceAll("_", " ")}`} to={`/reports?project_id=${id}&workspace_id=${capture.workspace_id}&capture_id=${encodeURIComponent(capture.id)}`}><FileText size={15} />Create report</Link><Link className="button secondary compact" aria-label={`Open AI advice for ${capture.source_kind.replaceAll("_", " ")}`} to={`/assistant?capture_id=${encodeURIComponent(capture.id)}&project_id=${id}&workspace_id=${capture.workspace_id}`}><Bot size={15} />AI advice</Link></div></article>)}</div>}</ResultBoundary></Surface></div></>}</ResultBoundary></div>;
}
