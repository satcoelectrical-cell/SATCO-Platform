import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectFoundationPanel } from "../components/ProjectFoundationPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  projectFoundation: vi.fn(), putProjectFoundation: vi.fn(), createProjectInput: vi.fn(),
  updateProjectInput: vi.fn(), reorderProjectInputs: vi.fn(), transitionProjectInput: vi.fn(),
  transitionProjectStage: vi.fn(), projectInputSources: vi.fn(),
} }));
vi.mock("../api/client", () => ({ api: apiMock }));

const workspace = { id:9, project_id:7, project_code:"SAT-007", project_name:"Protection renewal", discipline:"electrical", display_name:"Electrical Engineering", description:null, status:"active", version:1, updated_at:"2026-08-24T00:00:00Z", allowed_actions:[] };
const established = {
  outcome:"success", availability:"established", project_id:7, version:4,
  purpose:"Renew protection systems", engineering_basis:"Approved single-line and site survey",
  stage:"definition", in_scope:[{id:"10000000-0000-0000-0000-000000000001",ordinal:0,statement:"Relay replacement"}],
  out_of_scope:[{id:"10000000-0000-0000-0000-000000000002",ordinal:0,statement:"Transformer replacement"}],
  completion_criteria:[{id:"10000000-0000-0000-0000-000000000003",ordinal:0,statement:"Approved protection study"}],
  inputs:[{id:"20000000-0000-0000-0000-000000000001",title:"Existing relay settings",description:null,ordinal:0,required_by_stage:"preparation",standing:"missing",source_condition:"not_required",source:null,version:1,standing_changed_at:"2026-08-24T00:00:00Z",updated_at:"2026-08-24T00:00:00Z"}],
  next_stage_readiness:{state:"blocked",target_stage:"preparation",blockers:[{code:"required_input_not_ready",input_id:"20000000-0000-0000-0000-000000000001",input_title:"Existing relay settings"}]},
  allowed_actions:["edit_basis","manage_inputs","transition_stage"], established_at:"2026-08-24T00:00:00Z",updated_at:"2026-08-24T00:00:00Z",
} as const;

beforeEach(() => {
  for (const fn of Object.values(apiMock)) fn.mockReset();
  apiMock.projectFoundation.mockResolvedValue({state:"success",data:established});
  apiMock.putProjectFoundation.mockResolvedValue({state:"success",data:established});
  apiMock.createProjectInput.mockResolvedValue({state:"success",data:{outcome:"success",project_id:7,foundation_version:5,item:established.inputs[0]}});
  apiMock.transitionProjectInput.mockResolvedValue({state:"success",data:{outcome:"success",project_id:7,foundation_version:5,item:established.inputs[0]}});
  apiMock.transitionProjectStage.mockResolvedValue({state:"success",data:{outcome:"success",project_id:7,foundation_version:5,stage:"preparation"}});
  apiMock.projectInputSources.mockResolvedValue({state:"success",data:{outcome:"success",visible_count:1,items:[{kind:"supporting_file",source_id:"30000000-0000-0000-0000-000000000001",version:2,workspace_id:9,display_label:"Protection settings.pdf · Version 2"}]}});
});

it("renders the established real-data foundation, readiness and no raw identity fields", async () => {
  render(<ProjectFoundationPanel projectId={7} workspaces={[workspace]} />);
  expect(await screen.findByDisplayValue("Renew protection systems")).toBeVisible();
  expect(screen.getByText(/required input not ready: Existing relay settings/i)).toBeVisible();
  expect(screen.queryByLabelText(/organization id|project id|source id/i)).not.toBeInTheDocument();
  expect(apiMock.projectFoundation).toHaveBeenCalledWith(7);
});

it("establishes a legacy foundation only from explicit Human-authored values", async () => {
  apiMock.projectFoundation.mockResolvedValueOnce({state:"success",data:{outcome:"success",availability:"basis_not_established",project_id:7,allowed_actions:["establish"]}});
  const user = userEvent.setup(); render(<ProjectFoundationPanel projectId={7} workspaces={[workspace]} />);
  await user.type(await screen.findByLabelText("Project purpose"), "Renew protection systems");
  await user.type(screen.getByLabelText("Engineering basis"), "Approved survey");
  await user.type(screen.getByLabelText(/In scope/), "Relay replacement");
  await user.type(screen.getByLabelText(/Completion criteria/), "Approved study");
  await user.type(screen.getByLabelText("Human rationale"), "Establish reviewed Project basis");
  await user.click(screen.getByRole("button", {name:"Establish foundation"}));
  expect(apiMock.putProjectFoundation).toHaveBeenCalledWith(7, expect.objectContaining({expected_version:0,in_scope:["Relay replacement"],completion_criteria:["Approved study"],rationale:"Establish reviewed Project basis"}));
});

it("selects an authorized current source and never asks the Human for a raw UUID", async () => {
  const user = userEvent.setup(); render(<ProjectFoundationPanel projectId={7} workspaces={[workspace]} />);
  await user.selectOptions(await screen.findByLabelText("Required input"), established.inputs[0].id);
  await user.selectOptions(screen.getByLabelText("Source Engineering Workspace"), "9");
  await user.click(screen.getByRole("button", {name:"Load authorized sources"}));
  await user.selectOptions(await screen.findByLabelText("Authorized source"), "30000000-0000-0000-0000-000000000001");
  const standingForm = screen.getByRole("button", {name:"Update standing"}).closest("form")!;
  await user.type(within(standingForm).getByLabelText("Human rationale"), "Settings verified for preparation");
  await user.click(within(standingForm).getByRole("button", {name:"Update standing"}));
  expect(apiMock.transitionProjectInput).toHaveBeenCalledWith(7, established.inputs[0].id, expect.objectContaining({source_id:"30000000-0000-0000-0000-000000000001",source_workspace_id:9}));
  expect(screen.queryByLabelText(/source id/i)).not.toBeInTheDocument();
});

it("requires explicit Human rationale for deterministic input ordering", async () => {
  apiMock.projectFoundation.mockResolvedValue({state:"success",data:{...established,inputs:[...established.inputs,{...established.inputs[0],id:"20000000-0000-0000-0000-000000000002",title:"Protection study",ordinal:1}]}});
  apiMock.reorderProjectInputs.mockResolvedValue({state:"success",data:{outcome:"success",project_id:7,foundation_version:5,ordered_input_ids:["20000000-0000-0000-0000-000000000002",established.inputs[0].id]}});
  const user = userEvent.setup(); render(<ProjectFoundationPanel projectId={7} workspaces={[workspace]} />);
  const moveUp = await screen.findByRole("button", {name:"Move Protection study up"});
  expect(moveUp).toBeDisabled();
  await user.type(screen.getByLabelText("Human rationale for input ordering"), "Prioritize current protection study");
  await user.click(moveUp);
  expect(apiMock.reorderProjectInputs).toHaveBeenCalledWith(7,{expected_foundation_version:4,ordered_input_ids:["20000000-0000-0000-0000-000000000002",established.inputs[0].id],rationale:"Prioritize current protection study"});
});

it("collapses protected reads to one neutral state without Project details", async () => {
  apiMock.projectFoundation.mockResolvedValue({state:"protected"});
  render(<ProjectFoundationPanel projectId={7} workspaces={[]} />);
  expect(await screen.findByText("Not available")).toBeVisible();
  expect(screen.queryByText(/Renew protection|Existing relay|denied|forbidden/i)).not.toBeInTheDocument();
});

it("preserves payload-free conflict and unavailable UI handling", async () => {
  apiMock.putProjectFoundation.mockResolvedValue({state:"conflict"});
  const user = userEvent.setup(); render(<ProjectFoundationPanel projectId={7} workspaces={[workspace]} />);
  const basisForm = (await screen.findByRole("button", {name:"Save foundation"})).closest("form")!;
  await user.type(within(basisForm).getByLabelText("Human rationale"), "Reviewed basis update");
  await user.click(within(basisForm).getByRole("button", {name:"Save foundation"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("changed");
  expect(screen.queryByText(/version 4 expected|traceback|exception/i)).not.toBeInTheDocument();
});
