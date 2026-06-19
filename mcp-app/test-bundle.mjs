import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({ command: "node", args: ["dist/server.mjs"] });
const client = new Client({ name: "test-bundle", version: "0.0.1" });
await client.connect(transport);

const tools = await client.listTools();
console.log("tools:", tools.tools.map((t) => t.name));

const res = await client.callTool(
  { name: "review_accounts", arguments: {
      pdf_path: "C:\\Users\\Philip\\Downloads\\FRS102Disclosure\\App\\build\\layout\\FC.pdf",
      entity: "Four Communications Limited", period_end: "2024-12-31" } },
  undefined, { timeout: 30000 });
const s = res.structuredContent;
console.log("cached call isError:", res.isError ?? false);
if (s?.counts) console.log("entity:", s.entity, "| materiality:", s.materiality.display,
  "| counts:", JSON.stringify(s.counts.by_category), "| total:", s.counts.total_findings);
else console.log("NO structuredContent; text:", (res.content?.[0]?.text ?? "").slice(0, 300));

await client.close();
console.log("OK");
process.exit(0);
