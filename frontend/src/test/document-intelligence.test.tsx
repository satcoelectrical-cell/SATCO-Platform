import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DocumentIntelligencePanel } from "../components/DocumentIntelligencePanel";
import { DocumentFindingsPanel } from "../components/DocumentFindingsPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  supportingFiles: vi.fn(), documentAnalyses: vi.fn(), createDocumentAnalysis: vi.fn(),
  retryDocumentAnalysis: vi.fn(), documentCandidates: vi.fn(), documentAnalysisSource: vi.fn(),
  reviewDocumentCandidate: vi.fn(), promoteDocumentCandidate: vi.fn(),
  documentCorrelations: vi.fn(), documentFindings: vi.fn(), correlateDocuments: vi.fn(),
  createDocumentReportDraft: vi.fn(),
} }));

vi.mock("../api/client", () => ({ api: apiMock }));

const asset = {
  id:"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",organization_id:"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  project_id:7,workspace_id:9,safe_filename:"design-basis.pdf",media_type:"application/pdf",byte_size:1024,
  digest_algorithm:"sha256",content_digest:"c".repeat(64),lifecycle:"available",version:2,uploader_id:11,
  uploaded_at:"2026-10-07T10:00:00Z",scanned_at:"2026-10-07T10:01:00Z",predecessor_asset_id:null,allowed_actions:["download"],
};

function installSourceRelayMock(urls:string[]=[]){
  const instances:{port1:{postMessage:ReturnType<typeof vi.fn>;close:ReturnType<typeof vi.fn>;addEventListener:ReturnType<typeof vi.fn>;start:ReturnType<typeof vi.fn>};port2:{postMessage:ReturnType<typeof vi.fn>;close:ReturnType<typeof vi.fn>;addEventListener:ReturnType<typeof vi.fn>;start:ReturnType<typeof vi.fn>}}[]=[];
  const emptyPort=()=>({postMessage:vi.fn(),close:vi.fn(),addEventListener:vi.fn(),start:vi.fn()});
  class SourceRelay {
    port1;port2;
    constructor(){
      let listener:((event:MessageEvent)=>void)|null=null;
      const readyUrl=urls[instances.length]??"blob:source";
      this.port1={postMessage:vi.fn(()=>listener?.({data:{type:"ready",url:readyUrl}} as MessageEvent)),close:vi.fn(),addEventListener:vi.fn((_type:string,next:(event:MessageEvent)=>void)=>{listener=next;}),start:vi.fn()};
      this.port2=emptyPort();instances.push(this);
    }
  }
  vi.stubGlobal("MessageChannel",SourceRelay);
  return instances;
}

function sourceTarget(){
  return {opener:window,closed:false,close:vi.fn(),location:{replace:vi.fn()},document:{title:"",body:{textContent:""},createElement:vi.fn(()=>({textContent:""})),head:{append:vi.fn()}}} as unknown as Window;
}

beforeEach(()=>{
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  for(const fn of Object.values(apiMock))fn.mockReset();
  apiMock.supportingFiles.mockResolvedValue({state:"success",data:{items:[asset],visible_count:1,continuation:null}});
  apiMock.documentAnalyses.mockResolvedValue({state:"success",data:{items:[],total:0}});
  apiMock.documentCorrelations.mockResolvedValue({state:"success",data:{items:[],total:0}});
  apiMock.documentFindings.mockResolvedValue({state:"success",data:{items:[],total:0}});
});

it("requests analysis from an exact scanner-cleared PDF through the customer UI",async()=>{
  apiMock.createDocumentAnalysis.mockResolvedValue({state:"success",data:{analysis_run_id:"run"}});
  const user=userEvent.setup();render(<DocumentIntelligencePanel projectId={7} workspaceId={9}/>);
  await user.selectOptions(await screen.findByLabelText("Engineering document"),asset.id);
  await user.selectOptions(screen.getByLabelText("Document family hint"),"narrative_engineering");
  await user.type(screen.getByLabelText("Human rationale"),"Analyze the customer engineering source");
  await user.click(screen.getByRole("button",{name:/start analysis/i}));
  await waitFor(()=>expect(apiMock.createDocumentAnalysis).toHaveBeenCalledWith(7,{
    workspace_id:9,supporting_file_asset_id:asset.id,expected_asset_version:2,
    expected_content_digest:asset.content_digest,family_hint:"narrative_engineering",
    rationale:"Analyze the customer engineering source",
  }));
  expect(screen.getByText(/preserve Human review/i)).toBeVisible();
});

it("shows a truthful empty state and no developer controls",async()=>{
  render(<DocumentIntelligencePanel projectId={7} workspaceId={9}/>);
  expect(await screen.findByText("No analyses yet")).toBeVisible();
  expect(screen.queryByText(/json|sql|terminal|provider endpoint|api key/i)).not.toBeInTheDocument();
});

it("presents provider unavailability as a safe customer retry",async()=>{
  const run={analysis_run_id:"12121212-1212-4121-8121-121212121212",project_id:7,workspace_id:9,supporting_file_asset_id:asset.id,source_asset_version:2,source_content_digest:asset.content_digest,safe_filename:asset.safe_filename,state:"provider_unavailable",document_family:"narrative_engineering",progress:{completed_units:1,total_units:1,customer_message:"Semantic interpretation is temporarily unavailable; retry is available"},page_count:1,candidate_count:0,unreviewed_count:0,limitations:["Deterministic extraction remains unchanged"],allowed_actions:["open","retry"],version:3,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"};
  apiMock.documentAnalyses.mockResolvedValue({state:"success",data:{items:[run],total:1}});
  apiMock.retryDocumentAnalysis.mockResolvedValue({state:"success",data:{...run,state:"queued",allowed_actions:["open"],version:1}});
  const user=userEvent.setup();render(<DocumentIntelligencePanel projectId={7} workspaceId={9}/>);
  expect(await screen.findByText(/Semantic interpretation is temporarily unavailable/i)).toBeVisible();
  expect(screen.queryByText(/api key|endpoint|stack trace|localhost/i)).not.toBeInTheDocument();
  await user.click(screen.getByRole("button",{name:"Retry"}));
  await waitFor(()=>expect(apiMock.retryDocumentAnalysis).toHaveBeenCalledWith(7,run.analysis_run_id,3));
});

it("opens the authenticated exact source at the candidate page",async()=>{
  const run={analysis_run_id:"11111111-1111-4111-8111-111111111111",project_id:7,workspace_id:9,supporting_file_asset_id:asset.id,source_asset_version:2,source_content_digest:asset.content_digest,safe_filename:asset.safe_filename,state:"requires_review",document_family:"tabular_engineering",progress:{completed_units:1,total_units:1,customer_message:"1 candidate requires review"},page_count:1,candidate_count:1,unreviewed_count:1,limitations:[],allowed_actions:["open","review_candidates"],version:3,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"};
  const locator={locator_id:"22222222-2222-4222-8222-222222222222",schema_version:1,locator_kind:"table_cell",supporting_file_asset_id:asset.id,asset_version_at_analysis:2,storage_object_version:"object-v2",digest_algorithm:"sha256",content_digest:asset.content_digest,media_type:"application/pdf",page_index:2,page_label:"3",section_path:[],section_title:null,table_key:"page-3-table-1",table_title:null,row_index:1,row_label:"Item A",column_index:2,column_label:"Pressure",text_start:null,text_end:null,text_excerpt:"12 bar",text_excerpt_digest:null,bounding_box:null,source_revision_label:null,extraction_method:"deterministic",created_at:"2026-10-07T10:01:00Z"};
  const candidate={candidate_id:"33333333-3333-4333-8333-333333333333",analysis_run_id:run.analysis_run_id,version:1,ordinal:0,kind:"engineering_value",assertion_mode:"direct",review_state:"unreviewed",subject_key:"item_a",subject_label:"Item A",value:{raw_value:"12 bar",normalized_value:"12",numeric_value:"12",unit:"bar",quantity_type:"pressure",condition:null},confidence:"0.9",confidence_rationale:"Direct table cell",uncertainty:null,assumptions:[],proposed_canonical_target:"engineering_context_value",locators:[locator],allowed_actions:["accept","correct","reject","defer"],reviewed_by_id:null,reviewed_at:null,promotion_receipt_id:null,promoted_evidence_id:null,promoted_engineering_context_id:null,allowed_promotions:[]};
  apiMock.documentAnalyses.mockResolvedValue({state:"success",data:{items:[run],total:1}});
  apiMock.documentCandidates.mockResolvedValue({state:"success",data:{items:[candidate],total:1,reviewed_count:0,unreviewed_count:1}});
  apiMock.documentAnalysisSource.mockResolvedValue({state:"success",data:new Blob(["%PDF-1.4"],{type:"application/pdf"})});
  apiMock.reviewDocumentCandidate.mockResolvedValue({state:"success",data:{...candidate,version:2,review_state:"accepted",allowed_actions:[],reviewed_by_id:17,reviewed_at:"2026-10-07T10:02:00Z",allowed_promotions:["evidence","evidence_and_context"]}});
  apiMock.promoteDocumentCandidate.mockResolvedValue({state:"success",data:{promotion_receipt_id:"44444444-4444-4444-8444-444444444444",candidate_id:candidate.candidate_id,candidate_version:2,evidence_id:"55555555-5555-4555-8555-555555555555",evidence_version:2,evidence_lifecycle:"proposed",engineering_context_id:81,source_locator_ids:[locator.locator_id],promoted_at:"2026-10-07T10:03:00Z",promoted_by_id:17}});
  const createObjectURL=vi.spyOn(URL,"createObjectURL").mockReturnValue("blob:exact-source");
  const revokeObjectURL=vi.spyOn(URL,"revokeObjectURL").mockImplementation(()=>undefined);
  const user=userEvent.setup();render(<DocumentIntelligencePanel projectId={7} workspaceId={9}/>);
  await user.click(await screen.findByRole("button",{name:/inspect evidence/i}));
  expect(await screen.findByText("Item A")).toBeVisible();
  expect(screen.getByText(/asset v2.*SHA-256/i)).toBeVisible();
  expect(screen.getByTitle("Source page 3")).toHaveAttribute("src","blob:exact-source#page=3&zoom=page-width");
  expect(screen.getByText(/row 2.*Pressure/i)).toBeVisible();
  await user.click(screen.getByRole("button",{name:"Accept"}));
  await user.type(screen.getByLabelText("Decision rationale"),"Confirmed against exact source page three");
  await user.click(screen.getByRole("button",{name:/confirm human decision/i}));
  await waitFor(()=>expect(apiMock.reviewDocumentCandidate).toHaveBeenCalledWith(7,run.analysis_run_id,candidate.candidate_id,{expected_version:1,action:"accept",rationale:"Confirmed against exact source page three",correction:null}));
  expect(await screen.findByText(/Human decision recorded: accepted/i)).toBeVisible();
  await user.selectOptions(screen.getByLabelText("Promotion destination"),"evidence_and_context");
  await user.type(screen.getByLabelText("Promotion rationale"),"Create canonical traceability for approved pressure");
  await user.click(screen.getByRole("button",{name:/promote reviewed candidate/i}));
  await waitFor(()=>expect(apiMock.promoteDocumentCandidate).toHaveBeenCalledWith(7,run.analysis_run_id,candidate.candidate_id,{expected_candidate_version:2,include_engineering_context:true,rationale:"Create canonical traceability for approved pressure"}));
  expect(await screen.findByText(/Promotion complete: proposed Evidence and Engineering Context/i)).toBeVisible();
  expect(screen.getByText(/Evidence starts as proposed/i)).toBeVisible();
  createObjectURL.mockRestore();revokeObjectURL.mockRestore();
});

it("lets the Human reviewer normalize comparison keys without changing source provenance",async()=>{
  const run={analysis_run_id:"11111111-1111-4111-8111-111111111111",project_id:7,workspace_id:9,supporting_file_asset_id:asset.id,source_asset_version:2,source_content_digest:asset.content_digest,safe_filename:asset.safe_filename,state:"requires_review",document_family:"tabular_engineering",progress:{completed_units:1,total_units:1,customer_message:"1 candidate requires review"},page_count:1,candidate_count:1,unreviewed_count:1,limitations:[],allowed_actions:["open","review_candidates"],version:3,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"};
  const locator={locator_id:"22222222-2222-4222-8222-222222222222",schema_version:1,locator_kind:"table_cell",supporting_file_asset_id:asset.id,asset_version_at_analysis:2,storage_object_version:"object-v2",digest_algorithm:"sha256",content_digest:asset.content_digest,media_type:"application/pdf",page_index:0,page_label:"1",section_path:[],section_title:null,table_key:"page-1-table-1",table_title:null,row_index:36,row_label:"Feed Collector to RO Vessels",column_index:9,column_label:"Volumetric Flow",text_start:null,text_end:null,text_excerpt:"30.0",text_excerpt_digest:null,bounding_box:null,source_revision_label:null,extraction_method:"deterministic",created_at:"2026-10-07T10:01:00Z"};
  const candidate={candidate_id:"33333333-3333-4333-8333-333333333333",analysis_run_id:run.analysis_run_id,version:1,ordinal:0,kind:"engineering_value",assertion_mode:"direct",review_state:"unreviewed",subject_key:"feed_collector_to_ro_vessels",subject_label:"Feed Collector to RO Vessels",value:{raw_value:"30.0",normalized_value:"30.0",numeric_value:"30.0",unit:null,quantity_type:"volumetric_flow_column",condition:null},confidence:"0.9",confidence_rationale:"Direct table cell",uncertainty:null,assumptions:[],proposed_canonical_target:"engineering_context_value",locators:[locator],allowed_actions:["accept","correct","reject","defer"],reviewed_by_id:null,reviewed_at:null,promotion_receipt_id:null,promoted_evidence_id:null,promoted_engineering_context_id:null,allowed_promotions:[]};
  apiMock.documentAnalyses.mockResolvedValue({state:"success",data:{items:[run],total:1}});
  apiMock.documentCandidates.mockResolvedValue({state:"success",data:{items:[candidate],total:1,reviewed_count:0,unreviewed_count:1}});
  apiMock.documentAnalysisSource.mockResolvedValue({state:"success",data:new Blob(["%PDF-1.4"],{type:"application/pdf"})});
  apiMock.reviewDocumentCandidate.mockResolvedValue({state:"success",data:{...candidate,version:2,review_state:"corrected",subject_key:"ro_feed_flow",subject_label:"RO Feed Flow",value:{...candidate.value,unit:"m3/h",quantity_type:"volumetric_flow"},allowed_actions:[],reviewed_by_id:17,reviewed_at:"2026-10-07T10:02:00Z",allowed_promotions:["evidence","evidence_and_context"]}});
  vi.spyOn(URL,"createObjectURL").mockReturnValue("blob:exact-source");
  vi.spyOn(URL,"revokeObjectURL").mockImplementation(()=>undefined);
  const user=userEvent.setup();render(<DocumentIntelligencePanel projectId={7} workspaceId={9}/>);
  await user.click(await screen.findByRole("button",{name:/inspect evidence/i}));
  await user.click(await screen.findByRole("button",{name:"Correct"}));
  await user.clear(screen.getByLabelText("Normalized subject key"));await user.type(screen.getByLabelText("Normalized subject key"),"ro_feed_flow");
  await user.clear(screen.getByLabelText("Subject label"));await user.type(screen.getByLabelText("Subject label"),"RO Feed Flow");
  await user.clear(screen.getByLabelText("Engineering quantity type"));await user.type(screen.getByLabelText("Engineering quantity type"),"volumetric_flow");
  await user.type(screen.getByLabelText("Unit"),"m3/h");
  await user.type(screen.getByLabelText("Decision rationale"),"Human-confirmed semantic equivalence after exact-source review");
  await user.click(screen.getByRole("button",{name:/confirm human decision/i}));
  await waitFor(()=>expect(apiMock.reviewDocumentCandidate).toHaveBeenCalledWith(7,run.analysis_run_id,candidate.candidate_id,{expected_version:1,action:"correct",rationale:"Human-confirmed semantic equivalence after exact-source review",correction:{subject_key:"ro_feed_flow",subject_label:"RO Feed Flow",uncertainty:null,value:{raw_value:"30.0",normalized_value:"30.0",numeric_value:"30.0",unit:"m3/h",quantity_type:"volumetric_flow",condition:null}}}));
});

it("binds filenames, excerpts, and source actions explicitly despite reversed UUID order",async()=>{
  const pidRun={analysis_run_id:"ffffffff-ffff-4fff-8fff-ffffffffffff",project_id:7,workspace_id:9,supporting_file_asset_id:"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",source_asset_version:2,source_content_digest:"a".repeat(64),safe_filename:"golden-pid.pdf",state:"completed" as const,document_family:"narrative_engineering" as const,progress:{completed_units:1,total_units:1,customer_message:"Reviewed"},page_count:1,candidate_count:2,unreviewed_count:0,limitations:[],allowed_actions:["open","review_candidates"],version:4,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"};
  const controlRun={...pidRun,analysis_run_id:"00000000-0000-4000-8000-000000000001",supporting_file_asset_id:"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2",source_content_digest:"b".repeat(64),safe_filename:"golden-control-narrative.pdf"};
  const locator=(id:string,assetId:string,digest:string,excerpt:string,pageIndex=0)=>({locator_id:id,schema_version:1 as const,locator_kind:"text_span" as const,supporting_file_asset_id:assetId,asset_version_at_analysis:2,storage_object_version:`object-${id}`,digest_algorithm:"sha256" as const,content_digest:digest,media_type:"application/pdf",page_index:pageIndex,page_label:String(pageIndex+1),section_path:[],section_title:null,table_key:null,table_title:null,row_index:null,row_label:null,column_index:null,column_label:null,text_start:0,text_end:excerpt.length,text_excerpt:excerpt,text_excerpt_digest:"d".repeat(64),bounding_box:null,source_revision_label:null,extraction_method:"deterministic" as const,created_at:"2026-10-07T10:01:00Z"});
  const pidFirst=locator("11111111-1111-4111-8111-111111111111",pidRun.supporting_file_asset_id,pidRun.source_content_digest,"P&ID: XV-101 is Fail Closed (FC).",0);
  const pidSecond=locator("22222222-2222-4222-8222-222222222222",pidRun.supporting_file_asset_id,pidRun.source_content_digest,"P&ID: design pressure is 12 bar.",0);
  const control=locator("33333333-3333-4333-8333-333333333333",controlRun.supporting_file_asset_id,controlRun.source_content_digest,"Control Narrative: XV-101 is Fail Open (FO).",0);
  const finding={finding_id:"88888888-8888-4888-8888-888888888888",analysis_run_ids:[pidRun.analysis_run_id,controlRun.analysis_run_id],kind:"discrepancy" as const,state:"open" as const,title:"Cross-document discrepancy: XV-101 — fail position",explanation:"Reviewed values differ.",rule_id:"document.reviewed-assertion-consistency",rule_version:2,applicability:"Same explicit subject, parameter, and condition.",uncertainty:"Human disposition required.",evidence_sources:[
    {analysis_run_id:controlRun.analysis_run_id,candidate_id:"00000000-0000-4000-8000-000000000010",locator:control},
    {analysis_run_id:pidRun.analysis_run_id,candidate_id:"ffffffff-ffff-4fff-8fff-fffffffffff0",locator:pidFirst},
    {analysis_run_id:pidRun.analysis_run_id,candidate_id:"ffffffff-ffff-4fff-8fff-fffffffffff0",locator:pidSecond},
  ],evidence:[control,pidFirst,pidSecond],advisory:true as const};
  apiMock.documentFindings.mockResolvedValue({state:"success",data:{items:[finding],total:1}});
  const relays=installSourceRelayMock(["blob:control-pdf","blob:pid-pdf"]);
  const events:string[]=[];
  apiMock.documentAnalysisSource.mockImplementation(async(_projectId:number,runId:string)=>{events.push(`api:${runId}`);return {state:"success",data:new Blob([runId===pidRun.analysis_run_id?"PID PDF":"CONTROL PDF"],{type:"application/pdf"})};});
  const controlTarget=sourceTarget();
  const pidTarget=sourceTarget();
  const targets=[controlTarget,pidTarget];
  const open=vi.spyOn(window,"open").mockImplementation(()=>{events.push("open");return targets.shift()??null;});
  const revokeObjectURL=vi.spyOn(URL,"revokeObjectURL").mockImplementation(()=>undefined);
  const user=userEvent.setup();render(<DocumentFindingsPanel projectId={7} workspaceId={9} runs={[pidRun,controlRun]}/>);

  const controlRow=(await screen.findByText("Control Narrative: XV-101 is Fail Open (FO).")).parentElement!;
  const pidRow=screen.getByText("P&ID: XV-101 is Fail Closed (FC).").parentElement!;
  expect(within(controlRow).getByText(/golden-control-narrative\.pdf/)).toBeVisible();
  expect(within(pidRow).getByText(/golden-pid\.pdf/)).toBeVisible();
  expect(screen.getByText("P&ID: design pressure is 12 bar.")).toBeVisible();
  expect(screen.getAllByRole("button",{name:"Open exact source"})).toHaveLength(3);

  await user.click(within(controlRow).getByRole("button",{name:"Open exact source"}));
  await waitFor(()=>expect(apiMock.documentAnalysisSource).toHaveBeenCalledWith(7,controlRun.analysis_run_id));
  expect(events.slice(0,2)).toEqual(["open",`api:${controlRun.analysis_run_id}`]);
  expect(relays[0].port1.postMessage).toHaveBeenCalledWith({type:"open",blob:expect.any(Blob),page:1});
  await user.click(within(pidRow).getByRole("button",{name:"Open exact source"}));
  await waitFor(()=>expect(apiMock.documentAnalysisSource).toHaveBeenCalledWith(7,pidRun.analysis_run_id));
  expect(relays[1].port1.postMessage).toHaveBeenCalledWith({type:"open",blob:expect.any(Blob),page:1});
  expect(open).toHaveBeenCalledTimes(2);
  Object.defineProperty(controlTarget,"closed",{value:true});
  Object.defineProperty(pidTarget,"closed",{value:true});
  await new Promise(resolve=>window.setTimeout(resolve,1100));
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:control-pdf");
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:pid-pdf");
});

it("handles popup blocking and authorized-source API failure safely",async()=>{
  const run={analysis_run_id:"11111111-1111-4111-8111-111111111111",project_id:7,workspace_id:9,supporting_file_asset_id:asset.id,source_asset_version:2,source_content_digest:asset.content_digest,safe_filename:"golden-pid.pdf",state:"completed" as const,document_family:"narrative_engineering" as const,progress:{completed_units:1,total_units:1,customer_message:"Reviewed"},page_count:1,candidate_count:1,unreviewed_count:0,limitations:[],allowed_actions:["open"],version:4,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"};
  const locator={locator_id:"77777777-7777-4777-8777-777777777777",schema_version:1 as const,locator_kind:"text_span" as const,supporting_file_asset_id:asset.id,asset_version_at_analysis:2,storage_object_version:"object-v2",digest_algorithm:"sha256" as const,content_digest:asset.content_digest,media_type:"application/pdf",page_index:0,page_label:"1",section_path:[],section_title:null,table_key:null,table_title:null,row_index:null,row_label:null,column_index:null,column_label:null,text_start:0,text_end:6,text_excerpt:"source",text_excerpt_digest:"d".repeat(64),bounding_box:null,source_revision_label:null,extraction_method:"deterministic" as const,created_at:"2026-10-07T10:01:00Z"};
  const finding={finding_id:"88888888-8888-4888-8888-888888888888",analysis_run_ids:[run.analysis_run_id],kind:"discrepancy" as const,state:"open" as const,title:"Traceable finding",explanation:"Reviewed values differ.",rule_id:"rule",rule_version:2,applicability:"Exact binding.",uncertainty:null,evidence_sources:[{analysis_run_id:run.analysis_run_id,candidate_id:"99999999-9999-4999-8999-999999999999",locator}],evidence:[locator],advisory:true as const};
  apiMock.documentFindings.mockResolvedValue({state:"success",data:{items:[finding],total:1}});
  installSourceRelayMock();
  const open=vi.spyOn(window,"open").mockReturnValue(null);
  const user=userEvent.setup();render(<DocumentFindingsPanel projectId={7} workspaceId={9} runs={[run]}/>);
  await user.click(await screen.findByRole("button",{name:"Open exact source"}));
  expect(await screen.findByText(/source tab was blocked/i)).toBeVisible();
  expect(apiMock.documentAnalysisSource).not.toHaveBeenCalled();

  const target=sourceTarget();
  open.mockReturnValue(target);
  apiMock.documentAnalysisSource.mockResolvedValue({state:"protected"});
  await user.click(screen.getByRole("button",{name:"Open exact source"}));
  await waitFor(()=>expect(apiMock.documentAnalysisSource).toHaveBeenCalledWith(7,run.analysis_run_id));
  expect(target.close).toHaveBeenCalled();
  expect(await screen.findByText(/not available in your current authorized context/i)).toBeVisible();
});

it("runs approved correlation rules and explains evidence-backed findings",async()=>{
  const runs=["narrative.pdf","table.pdf"].map((safe_filename,index)=>({analysis_run_id:`00000000-0000-4000-8000-00000000000${index+1}`,project_id:7,workspace_id:9,supporting_file_asset_id:asset.id,source_asset_version:2,source_content_digest:asset.content_digest,safe_filename,state:"completed" as const,document_family:index?"tabular_engineering" as const:"narrative_engineering" as const,progress:{completed_units:1,total_units:1,customer_message:"Reviewed"},page_count:1,candidate_count:1,unreviewed_count:0,limitations:[],allowed_actions:["open","review_candidates"],version:4,created_at:"2026-10-07T10:00:00Z",updated_at:"2026-10-07T10:01:00Z"}));
  const locator={locator_id:"77777777-7777-4777-8777-777777777777",schema_version:1 as const,locator_kind:"table_cell" as const,supporting_file_asset_id:asset.id,asset_version_at_analysis:2,storage_object_version:"object-v2",digest_algorithm:"sha256" as const,content_digest:asset.content_digest,media_type:"application/pdf",page_index:1,page_label:"2",section_path:[],section_title:null,table_key:"page-2-table-1",table_title:null,row_index:2,row_label:"Item A",column_index:1,column_label:"Pressure",text_start:null,text_end:null,text_excerpt:"15 bar",text_excerpt_digest:null,bounding_box:null,source_revision_label:null,extraction_method:"deterministic" as const,created_at:"2026-10-07T10:01:00Z"};
  const finding={finding_id:"88888888-8888-4888-8888-888888888888",analysis_run_ids:runs.map(run=>run.analysis_run_id),kind:"discrepancy" as const,state:"open" as const,title:"Cross-document discrepancy: Item A",explanation:"Two reviewed values differ; SATCO has not selected which is correct.",rule_id:"document.exact-key-numeric-consistency",rule_version:1,applicability:"Same exact normalized subject, quantity type, and unit.",uncertainty:"Confirm operating condition.",evidence_sources:[{analysis_run_id:runs[1].analysis_run_id,candidate_id:"99999999-9999-4999-8999-999999999999",locator}],evidence:[locator],advisory:true as const};
  apiMock.documentCorrelations.mockResolvedValue({state:"success",data:{items:[],total:0}});
  apiMock.documentFindings.mockResolvedValue({state:"success",data:{items:[finding],total:1}});
  apiMock.correlateDocuments.mockResolvedValue({state:"success",data:{rule_pack_id:"satco.document-correlation.v2",rule_pack_version:2,evaluated_run_ids:runs.map(run=>run.analysis_run_id),correlations:[],findings:[finding]}});
  apiMock.createDocumentReportDraft.mockResolvedValue({state:"success",data:{report_id:"99999999-9999-4999-8999-999999999999",version:1,draft_revision_id:"aaaaaaaa-9999-4999-8999-999999999999",lifecycle:"draft",preliminary:true,finding_ids:[finding.finding_id]}});
  const user=userEvent.setup();render(<DocumentFindingsPanel projectId={7} workspaceId={9} runs={runs}/>);
  expect(await screen.findByText("Cross-document discrepancy: Item A")).toBeVisible();
  await user.click(screen.getByText("Why SATCO raised this"));
  expect(screen.getByText(/Same exact normalized subject/i)).toBeVisible();
  expect(screen.getByRole("button",{name:/open exact source/i})).toBeVisible();
  const boxes=screen.getAllByRole("checkbox");await user.click(boxes[0]);await user.click(boxes[1]);
  await user.type(screen.getByLabelText("Evaluation rationale"),"Compare Human-reviewed project documents");
  await user.click(screen.getByRole("button",{name:/run approved correlation rules/i}));
  await waitFor(()=>expect(apiMock.correlateDocuments).toHaveBeenCalledWith(7,{analysis_run_ids:runs.map(run=>run.analysis_run_id),rule_pack_id:"satco.document-correlation.v2",rationale:"Compare Human-reviewed project documents"}));
  await user.click(screen.getByLabelText(`Include ${finding.title} in report`));
  await user.type(screen.getByLabelText("Draft generation rationale"),"Prepare preliminary report for Human engineering review");
  await user.click(screen.getByRole("button",{name:/generate technical report draft/i}));
  await waitFor(()=>expect(apiMock.createDocumentReportDraft).toHaveBeenCalledWith(7,{workspace_id:9,finding_ids:[finding.finding_id],purpose:"engineering_analysis",rationale:"Prepare preliminary report for Human engineering review"}));
  expect(await screen.findByRole("link",{name:/review generated draft/i})).toHaveAttribute("href",expect.stringContaining("/reports/99999999"));
});
