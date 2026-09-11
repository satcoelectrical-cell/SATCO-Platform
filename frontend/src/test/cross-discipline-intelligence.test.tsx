import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CrossDisciplineIntelligencePanel } from "../components/CrossDisciplineIntelligencePanel";

const { apiMock } = vi.hoisted(() => ({
  apiMock: {
    crossDisciplineReadiness: vi.fn(),
    crossDisciplineAssessments: vi.fn(),
    crossDisciplineFindings: vi.fn(),
  },
}));
vi.mock("../api/client", () => ({ api: apiMock }));

const ready = { state:"success",data:{state:"ready",reason_codes:[],definition_digest:"a".repeat(64)} };
const empty = { state:"success",data:{items:[],next_cursor:null} };

beforeEach(()=>{
  apiMock.crossDisciplineReadiness.mockReset().mockResolvedValue(ready);
  apiMock.crossDisciplineAssessments.mockReset().mockResolvedValue(empty);
  apiMock.crossDisciplineFindings.mockReset().mockResolvedValue({state:"success",data:{items:[],next_cursor:null}});
});

describe("PATCH-053 Batch-1 frontend foundation",()=>{
  it("renders an authorized empty state as advisory and never as an inferred PASS",async()=>{
    render(<CrossDisciplineIntelligencePanel projectId={7} workspaceIds={[2,3]}/>);
    expect(screen.getByLabelText("Cross-discipline intelligence")).toHaveAttribute("aria-busy","true");
    expect(await screen.findByRole("status")).toHaveTextContent("empty");
    expect(screen.getByText(/Human disposition remains authoritative/i)).toBeVisible();
    expect(screen.queryByText(/PASS/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/No authorized/i).length).toBeGreaterThan(0);
  });

  it("labels indeterminate without green or empty semantics",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"00000000-0000-4000-8000-000000000001",aggregate_version:1,status:"indeterminate",reason_code:"source_incomplete",result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByText(/not a PASS or an empty result/i)).toBeVisible();
    expect(screen.getAllByRole("status").some((item)=>item.textContent==="indeterminate")).toBe(true);
  });

  it("renders ready history through all six advisory foundation surfaces",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"ready-assessment",aggregate_version:1,status:"completed_no_findings",reason_code:null,result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    render(<CrossDisciplineIntelligencePanel projectId={7} workspaceIds={[2,3]}/>);
    expect(await screen.findByText("ready-assessment")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("ready");
    for(const label of ["Cross-discipline overview","Cross-discipline finding queue","Cross-discipline finding detail","Cross-discipline provenance","Cross-discipline dispositions","Cross-discipline assessment history"]){
      expect(screen.getByLabelText(label)).toBeVisible();
    }
  });

  it("renders only persisted E↔I finding summaries and never infers a pass or a path",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"ei-assessment",aggregate_version:1,status:"completed_with_findings",reason_code:null,result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    apiMock.crossDisciplineFindings.mockResolvedValue({state:"success",data:{items:[{finding_id:"ei-finding",assessment_id:"ei-assessment",ordinal:1,category:"dependency",subcode:"ei.cable_jb_path",severity:"warning",fingerprint:"f".repeat(64),recurrence_key:"r".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true}],next_cursor:null}});
    render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByLabelText("Cross-discipline dependency")).toBeVisible();
    expect(await screen.findByText("ei.cable_jb_path")).toBeVisible();
    expect(screen.getByLabelText("Cross-discipline source comparison")).toHaveTextContent(/does not imply a PASS/i);
    expect(screen.getByLabelText("Cross-discipline commitment context")).toHaveTextContent(/does not establish fulfilment/i);
    expect(screen.queryByText(/inferred path/i)).not.toBeInTheDocument();
  });

  it("renders persisted I↔C findings without exposing operands, topology, or fulfilment inference",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"ic-assessment",aggregate_version:1,status:"completed_with_findings",reason_code:null,result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    apiMock.crossDisciplineFindings.mockResolvedValue({state:"success",data:{items:[
      {finding_id:"ic-type",assessment_id:"ic-assessment",ordinal:1,category:"inconsistent",subcode:"ic.signal_type",severity:"major",fingerprint:"f".repeat(64),recurrence_key:"r".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ic-range",assessment_id:"ic-assessment",ordinal:2,category:"inconsistent",subcode:"ic.signal_range",severity:"major",fingerprint:"g".repeat(64),recurrence_key:"s".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ic-path",assessment_id:"ic-assessment",ordinal:3,category:"dependency",subcode:"ic.valve_command_feedback",severity:"major",fingerprint:"h".repeat(64),recurrence_key:"t".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ic-commitment",assessment_id:"ic-assessment",ordinal:4,category:"unfulfilled_commitment",subcode:"ic.commitment_fulfilment",severity:"major",fingerprint:"i".repeat(64),recurrence_key:"u".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
    ],next_cursor:null}});
    render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByText("ic.signal_type")).toBeVisible();
    expect(screen.getByText("ic.signal_range")).toBeVisible();
    expect(screen.getByText("ic.valve_command_feedback")).toBeVisible();
    expect(screen.getByText("ic.commitment_fulfilment")).toBeVisible();
    expect(screen.queryByText(/4..20|controller/i)).not.toBeInTheDocument();
  });

  it("renders persisted Electrical↔C&A findings as advisory without inferring operands or topology",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"ec-assessment",aggregate_version:1,status:"completed_with_findings",reason_code:null,result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    apiMock.crossDisciplineFindings.mockResolvedValue({state:"success",data:{items:[
      {finding_id:"ec-mcc",assessment_id:"ec-assessment",ordinal:1,category:"incomplete_handoff",subcode:"ec.mcc_command_status",severity:"major",fingerprint:"f".repeat(64),recurrence_key:"r".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ec-path",assessment_id:"ec-assessment",ordinal:2,category:"dependency",subcode:"ec.cabinet_power_path",severity:"major",fingerprint:"g".repeat(64),recurrence_key:"s".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ec-fresh",assessment_id:"ec-assessment",ordinal:3,category:"stale",subcode:"ec.source_freshness",severity:"warning",fingerprint:"h".repeat(64),recurrence_key:"t".repeat(64),current_state:"open",allowed_actions:[],provenance:{},advisory:true},
      {finding_id:"ec-dispute",assessment_id:"ec-assessment",ordinal:4,category:"disputed",subcode:"ec.commitment_dispute",severity:"major",fingerprint:"i".repeat(64),recurrence_key:"u".repeat(64),current_state:"disputed",allowed_actions:[],provenance:{},advisory:true},
    ],next_cursor:null}});
    render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByText("ec.mcc_command_status")).toBeVisible();
    expect(screen.getByText("ec.cabinet_power_path")).toBeVisible();
    expect(screen.getByText("ec.source_freshness")).toBeVisible();
    expect(screen.getByText("ec.commitment_dispute")).toBeVisible();
    expect(screen.queryByText(/alternate supply|controller|observed at/i)).not.toBeInTheDocument();
  });

  it.each([
    ["unavailable",{state:"unavailable"}],
    ["conflict",{state:"conflict"}],
  ] as const)("renders the %s transport state without implying a result",async(state,result)=>{
    apiMock.crossDisciplineReadiness.mockResolvedValue(result);
    render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByRole("alert")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(state);
    expect(screen.queryByText(/PASS/i)).not.toBeInTheDocument();
  });

  it("clears prior project identifiers when a switched project is protected",async()=>{
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"success",data:{items:[{assessment_id:"visible-assessment",aggregate_version:1,status:"completed_no_findings",reason_code:null,result_digest:"b".repeat(64),completed_at:"2026-09-10T00:00:00Z"}],next_cursor:null}});
    const view=render(<CrossDisciplineIntelligencePanel projectId={7}/>);
    expect(await screen.findByText("visible-assessment")).toBeVisible();
    apiMock.crossDisciplineReadiness.mockResolvedValue({state:"protected"});
    apiMock.crossDisciplineAssessments.mockResolvedValue({state:"protected"});
    view.rerender(<CrossDisciplineIntelligencePanel projectId={8}/>);
    await waitFor(()=>expect(screen.queryByLabelText("Cross-discipline intelligence")).not.toBeInTheDocument());
    expect(screen.queryByText("visible-assessment")).not.toBeInTheDocument();
  });

  it("preserves machine identity direction under RTL",async()=>{
    const view=render(<div dir="rtl"><CrossDisciplineIntelligencePanel projectId={7}/></div>);
    const digest=await screen.findByText("a".repeat(64));
    expect(digest).toHaveClass("cross-discipline-machine-id");
    expect(view.container.querySelector("[dir='rtl']")).toBeTruthy();
  });
});
