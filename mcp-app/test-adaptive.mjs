import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { readFileSync } from "node:fs";
const PDF = "C:/Users/Philip/Downloads/FRS102Disclosure/App/build/layout/FC.pdf";
const truth = JSON.parse(readFileSync("../build/summaries/FC.answers.json", "utf-8"));
const t = new StdioClientTransport({ command: "node", args: ["dist/server.mjs"] });
const c = new Client({ name: "t", version: "0.0.1" });
await c.connect(t);
let r = await c.callTool({ name: "review_accounts", arguments: { pdf_path: PDF, entity: "Four Communications Limited" } }, undefined, { timeout: 30000 });
const answers = {}; let asked = 0;
while (!r.structuredContent?.done) {
  const q = r.structuredContent.question; asked++;
  console.log(`Q${asked} (remaining ${r.structuredContent.remaining}) [${q.topic||""}] ${q.fact_key}`);
  answers[q.fact_key] = truth[q.fact_key] ?? false;
  r = await c.callTool({ name: "next_question", arguments: { pdf_path: PDF, answers } }, undefined, { timeout: 30000 });
  if (asked > 30) { console.log("guard"); break; }
}
console.log(`interview done after ${asked} questions`);
const f = await c.callTool({ name: "finalize_review", arguments: { pdf_path: PDF, entity: "Four Communications Limited", answers } }, undefined, { timeout: 30000 });
console.log("finalize:", f.structuredContent?.counts?.total_findings, "findings,", f.structuredContent?.materiality?.display);
await c.close(); process.exit(0);
