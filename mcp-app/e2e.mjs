import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: process.platform === "win32" ? "npx.cmd" : "npx",
  args: ["tsx", "main.ts"],
});
const client = new Client({ name: "e2e", version: "0.0.1" });
await client.connect(transport);

const t0 = Date.now();
const result = await client.callTool(
  {
    name: "review_accounts",
    arguments: {
      pdf_path: "C:\\Users\\Philip\\Downloads\\FRS102Disclosure\\App\\build\\layout\\FC.pdf",
      entity: "Four Communications Limited",
      period_end: "2024-12-31",
    },
  },
  undefined,
  { timeout: 300000 },
);
const secs = Math.round((Date.now() - t0) / 1000);
const s = result.structuredContent;
console.log(`tool ran in ${secs}s; isError=${result.isError ?? false}`);
if (s?.counts) {
  console.log("entity:", s.entity, "| materiality:", s.materiality.display);
  console.log("counts:", JSON.stringify(s.counts.by_category), "| total:", s.counts.total_findings,
    "| questions:", s.counts.questions);
} else {
  console.log("text:", (result.content?.[0]?.text ?? "").slice(0, 400));
}
await client.close();
process.exit(0);
