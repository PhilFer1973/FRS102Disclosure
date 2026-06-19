import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: process.platform === "win32" ? "npx.cmd" : "npx",
  args: ["tsx", "main.ts"],
});
const client = new Client({ name: "smoke", version: "0.0.1" });
await client.connect(transport);

const tools = await client.listTools();
console.log("tools:", tools.tools.map((t) => `${t.name} (ui=${t._meta?.ui?.resourceUri ?? "none"})`));

const res = await client.readResource({ uri: "ui://frs102-review/summary.html" });
const c = res.contents[0];
console.log("resource mime:", c.mimeType, "bytes:", (c.text ?? "").length);

await client.close();
console.log("OK");
process.exit(0);
