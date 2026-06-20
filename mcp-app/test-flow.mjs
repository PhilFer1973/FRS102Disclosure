import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
const PDF = "C:/Users/Philip/Downloads/FRS102Disclosure/App/build/layout/FC.pdf";
const transport = new StdioClientTransport({ command: "node", args: ["dist/server.mjs"] });
const client = new Client({ name: "t", version: "0.0.1" });
await client.connect(transport);
const r1 = await client.callTool({ name: "review_accounts",
  arguments: { pdf_path: PDF, entity: "Four Communications Limited" } }, undefined, { timeout: 30000 });
const qs = r1.structuredContent?.questions ?? [];
console.log("STEP1 review: isError", r1.isError ?? false, "| questions", qs.length);
const r2 = await client.callTool({ name: "finalize_review",
  arguments: { pdf_path: PDF, entity: "Four Communications Limited",
    answers: { is_qualifying_entity: true, is_small_entity: false } } }, undefined, { timeout: 30000 });
const s = r2.structuredContent;
console.log("STEP2 finalize: isError", r2.isError ?? false,
  "| total", s?.counts?.total_findings, "| materiality", s?.materiality?.display,
  "| by_cat", JSON.stringify(s?.counts?.by_category));
await client.close(); console.log("OK"); process.exit(0);
