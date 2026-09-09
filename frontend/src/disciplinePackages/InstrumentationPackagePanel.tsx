import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, PackageObjectCreateResult, PackageRuleResult } from "../api/types";
import { PackageWorkspaceShell, type PackagePanelProps } from "./PackageWorkspaceShell";

const OBJECTS = ["instrument","transmitter","analyzer","flowmeter","control_valve","instrument_loop","junction_box","instrument_panel"] as const;
const RELATIONSHIPS = ["transmits_to","connected_to_loop","connected_to_io_channel","provides_feedback_to","calibrated_against"] as const;
const INPUTS = ["measurement_service","operating_range","design_conditions","signal_basis","loop_basis"] as const;
const DELIVERABLES = ["instrument_index","instrument_datasheet","instrument_loop_diagram","instrument_io_list"] as const;
const EVIDENCE = ["measurement_process_basis_evidence","range_condition_basis_evidence","loop_calibration_basis_evidence","deliverable_review_evidence"] as const;
const RULES = ["object_relationship_integrity","required_input_completeness","loop_signal_connectivity","evidence_sufficiency","deliverable_readiness"] as const;

export function InstrumentationPackagePanel({ state = "UNAVAILABLE", projectId, workspaceId }: Readonly<PackagePanelProps>) {
  const [objectType,setObjectType]=useState<(typeof OBJECTS)[number]>("instrument");
  const [displayValue,setDisplayValue]=useState("");
  const [rationale,setRationale]=useState("");
  const [creation,setCreation]=useState<ApiResult<PackageObjectCreateResult>|null>(null);
  const [assessment,setAssessment]=useState<ApiResult<PackageRuleResult>|null>(null);
  async function createObject(event:FormEvent){event.preventDefault();if(!projectId||!workspaceId)return;setCreation(await api.createInstrumentationObject(projectId,workspaceId,{declaration_id:`instrumentation.object.${objectType}`,primary_identifier_display_value:displayValue,primary_identifier_evidence_references:[],steward_id:null,rationale}));}
  async function evaluate(){if(!projectId||!workspaceId)return;setAssessment(await api.evaluateInstrumentationRule(projectId,workspaceId,{hook_id:"instrumentation.required_input_completeness",hook_version:"1.0.0",envelope:{objects:[],relationships:[],deliverables:[],contexts:[],evidence:[],missing_required_ids:[],partial:true,protected:false,stale:false}}));}
  return <PackageWorkspaceShell title="Instrumentation V1" state={state}>
    <p>Server-authorized Instrumentation engineering package. Deterministic checks are bounded and do not replace Human engineering review.</p>
    <div className="package-catalog-grid">
      <section><h3>Objects · 8</h3><ul>{OBJECTS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Relationships · 5</h3><ul>{RELATIONSHIPS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Inputs / Context · 5</h3><ul>{INPUTS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Evidence & Deliverables</h3><p>{EVIDENCE.length} evidence requirements · {DELIVERABLES.length} deliverables</p><ul>{DELIVERABLES.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Deterministic Guidance · 5</h3><ul>{RULES.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul><button type="button" className="button secondary" onClick={evaluate}>Evaluate bounded readiness</button>{assessment?.state==="success"?<p role="status">{assessment.data.status}</p>:null}</section>
    </div>
    <form className="bootstrap-form" onSubmit={createObject}><h3>Create Object with required primary Identifier</h3><label>Object declaration<select value={objectType} onChange={e=>setObjectType(e.target.value as typeof objectType)}>{OBJECTS.map(x=><option key={x} value={x}>{x.replaceAll("_"," ")}</option>)}</select></label><label>Primary identifier<input required minLength={1} maxLength={128} value={displayValue} onChange={e=>setDisplayValue(e.target.value)}/></label><label>Rationale<textarea required minLength={1} maxLength={2000} value={rationale} onChange={e=>setRationale(e.target.value)}/></label><button className="button primary">Create atomic Object + Identifier</button>{creation?.state==="success"?<p role="status">Created {creation.data.primary_identifier.display_value}</p>:creation?<p role="alert">Operation {creation.state}</p>:null}</form>
  </PackageWorkspaceShell>;
}
