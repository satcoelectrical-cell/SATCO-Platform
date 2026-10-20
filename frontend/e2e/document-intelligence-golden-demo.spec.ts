import { expect, test } from "@playwright/test";
import { Buffer } from "node:buffer";

test("complete customer-only document intelligence workflow",async({page})=>{
  await page.goto("/projects/7?workspace=9&section=documents");
  await expect(page.getByRole("heading",{name:"Document Intelligence"})).toBeVisible();

  const fileInput=page.getByLabel("Supporting file");
  const rationale=page.getByLabel("Upload rationale");
  await fileInput.setInputFiles({name:"narrative-design-basis.pdf",mimeType:"application/pdf",buffer:Buffer.from("%PDF-1.4 narrative engineering fixture")});
  await rationale.fill("Upload the bounded narrative engineering source");
  await page.getByRole("button",{name:/Upload to quarantine/i}).click();
  await expect(page.getByText("narrative-design-basis.pdf").first()).toBeVisible();

  await fileInput.setInputFiles({name:"tabular-line-sizing.pdf",mimeType:"application/pdf",buffer:Buffer.from("%PDF-1.4 tabular engineering fixture")});
  await rationale.fill("Upload the bounded tabular engineering source");
  await page.getByRole("button",{name:/Upload to quarantine/i}).click();
  await expect(page.getByText("tabular-line-sizing.pdf").first()).toBeVisible();

  await page.getByRole("button",{name:"Refresh"}).first().click();
  const analysisForm=page.locator("form.document-analysis-form");
  await analysisForm.locator("select").nth(0).selectOption("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1");
  await analysisForm.locator("select").nth(1).selectOption("narrative_engineering");
  await analysisForm.getByLabel("Human rationale").fill("Extract reviewable candidates from this exact narrative source");
  await analysisForm.getByRole("button",{name:/Start analysis/i}).click();
  await expect(page.getByText(/narrative engineering · source version 2/i)).toBeVisible();

  await analysisForm.locator("select").nth(0).selectOption("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2");
  await analysisForm.locator("select").nth(1).selectOption("tabular_engineering");
  await analysisForm.getByLabel("Human rationale").fill("Extract reviewable candidates from this exact tabular source");
  await analysisForm.getByRole("button",{name:/Start analysis/i}).click();
  await expect(page.getByText(/tabular engineering · source version 2/i)).toBeVisible();

  await page.getByRole("button",{name:/Inspect evidence/i}).first().click();
  await expect(page.getByTitle("Source page 1")).toBeVisible();
  await page.getByRole("button",{name:"Accept",exact:true}).click();
  await page.getByLabel("Decision rationale").fill("Confirmed against the exact bound source");
  await page.getByRole("button",{name:/Confirm Human decision/i}).click();
  await expect(page.getByText(/Human decision recorded: accepted/i)).toBeVisible();
  await page.getByLabel("Promotion destination").selectOption("evidence_and_context");
  await page.getByLabel("Promotion rationale").fill("Create governed source-linked records");
  await page.getByRole("button",{name:/Promote reviewed candidate/i}).click();
  await expect(page.getByText(/Promotion complete: proposed Evidence and Engineering Context/i)).toBeVisible();
  await page.getByRole("button",{name:"Close"}).click();

  await page.getByRole("button",{name:/Inspect evidence/i}).nth(1).click();
  await expect(page.getByTitle("Source page 2")).toBeVisible();
  await page.getByRole("button",{name:"Accept",exact:true}).click();
  await page.getByLabel("Decision rationale").fill("Confirmed the tabular value against its exact cell source");
  await page.getByRole("button",{name:/Confirm Human decision/i}).click();
  await expect(page.getByText(/Human decision recorded: accepted/i)).toBeVisible();
  await page.getByRole("button",{name:"Close"}).click();

  const scope=page.getByRole("group",{name:"Analysis scope"});
  await scope.getByRole("checkbox").nth(0).check();
  await scope.getByRole("checkbox").nth(1).check();
  await page.getByLabel("Evaluation rationale").fill("Compare reviewed sources under the approved rule pack");
  await page.getByRole("button",{name:/Run approved correlation rules/i}).click();
  await expect(page.getByText(/Evaluation complete: 1 correlations and 1 advisory findings/i)).toBeVisible();
  await expect(page.getByRole("heading",{name:"Cross-document discrepancy: Line A"})).toBeVisible();
  await page.getByText("Why SATCO raised this").click();
  await expect(page.locator("details[open] dd").filter({hasText:/same exact normalized subject/i})).toBeVisible();

  await page.getByLabel("Include Cross-document discrepancy: Line A in report").check();
  await page.getByLabel("Draft generation rationale").fill("Prepare a preliminary draft for Human review");
  await page.getByRole("button",{name:/Generate Technical Report draft/i}).click();
  await expect(page.getByRole("link",{name:/Review generated draft/i})).toHaveAttribute("href",/\/reports\/99999999/);
  await expect(page.getByText(/A Human must review the exact draft before acceptance/i)).toBeVisible();
  await page.getByRole("link",{name:/Review generated draft/i}).click();
  await expect(page.getByRole("heading",{name:"Human acceptance of this exact revision"})).toBeVisible();
  await page.getByLabel("Human acceptance rationale").fill("Reviewed the preliminary scope, uncertainty, rule basis, and exact source provenance");
  await page.getByLabel(/explicitly accept this exact revision/i).check();
  await page.getByRole("button",{name:"Accept exact revision"}).click();
  await expect(page.getByText("Accepted and immutable")).toBeVisible();
  await expect(page.getByText(/terminal|database console|raw json|api key/i)).toHaveCount(0);
});

test("shows safe loading, protected, and unavailable customer states",async({page})=>{
  let releaseAnalyses:()=>void=()=>{};
  const analysesReleased=new Promise<void>(resolve=>{releaseAnalyses=resolve;});
  await page.route("**/projects/7/document-analyses?workspace_id=9",async route=>{
    await analysesReleased;
    await route.fulfill({status:403,contentType:"application/json",body:JSON.stringify({detail:"internal tenant policy and database row identifier"})});
  });
  await page.goto("/projects/7?workspace=9&section=documents");
  await expect(page.getByText("Loading document analyses…")).toBeVisible();
  releaseAnalyses();
  await expect(page.getByText("Not available")).toBeVisible();
  await expect(page.getByText(/internal tenant policy|database row identifier/i)).toHaveCount(0);

  await page.unroute("**/projects/7/document-analyses?workspace_id=9");
  await page.route("**/projects/7/document-findings?workspace_id=9",route=>route.fulfill({status:503,contentType:"application/json",body:JSON.stringify({detail:"provider credential secret and stack trace"})}));
  await page.reload();
  await expect(page.getByText("Service temporarily unavailable")).toBeVisible();
  await expect(page.getByText(/provider credential secret|stack trace/i)).toHaveCount(0);
});
