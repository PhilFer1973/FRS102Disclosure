import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult, ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { z } from "zod";

const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "dist")
  : import.meta.dirname;
// mcp-app lives inside the pipeline repo (.../App/mcp-app); the pipeline runs from .../App.
const APP_DIR = path.resolve(import.meta.dirname, "..");

const summarySchema = z.object({
  entity: z.string(),
  period_end: z.string(),
  materiality: z.object({ value: z.number().nullable(), basis: z.string(), display: z.string() }),
  counts: z.object({
    total_findings: z.number(),
    by_category: z.object({
      judgement: z.number(), disclosure: z.number(),
      numerical: z.number(), formatting: z.number(),
    }),
    need_judgement: z.number(),
    questions: z.number(),
  }),
  findings: z.array(z.object({
    category: z.string(), citation: z.string(), severity: z.string(),
    text: z.string(), status: z.string().optional(),
  })),
  questions: z.array(z.object({
    fact_key: z.string(), question: z.string(), citation: z.string(),
  })),
});
type Summary = z.infer<typeof summarySchema>;

function runPipeline(args: string[]): Promise<{ ok: boolean; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn("uv", ["run", "python", "-m", "cli.review_pdf", ...args], {
      cwd: APP_DIR,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let stderr = "";
    // Drain BOTH pipes: the pipeline prints progress to stdout, and if it isn't
    // read the OS pipe buffer fills and the Python child blocks (deadlock).
    proc.stdout.on("data", () => {});
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("error", (e) => resolve({ ok: false, stderr: String(e) }));
    proc.on("close", (code) => resolve({ ok: code === 0, stderr }));
  });
}

function textFallback(s: Summary): string {
  const c = s.counts;
  const lines = [
    `FRS 102 review — ${s.entity} (${s.period_end})`,
    `Materiality: ${s.materiality.display} (${s.materiality.basis})`,
    `${c.total_findings} findings — judgement ${c.by_category.judgement}, ` +
      `disclosure ${c.by_category.disclosure}, numerical ${c.by_category.numerical}, ` +
      `formatting ${c.by_category.formatting}. ${c.questions} questions for the reviewer.`,
    "",
    "Findings:",
    ...s.findings.map((f) => `- [${f.category}] ${f.citation}: ${f.text}`),
  ];
  return lines.join("\n");
}

export function createServer(): McpServer {
  const server = new McpServer({
    name: "FRS 102 Disclosure Reviewer",
    version: "0.1.0",
  });
  const resourceUri = "ui://frs102-review/summary.html";

  registerAppTool(server,
    "review_accounts",
    {
      title: "Review FRS 102 accounts",
      description: "Reviews a set of UK FRS 102 financial statements (a PDF) and " +
        "returns an issues register: missing/!present disclosures, numerical and " +
        "formatting checks, and recognition/measurement judgement matters, each " +
        "cited to FRS 102 / CA06. Renders an at-a-glance summary panel.",
      inputSchema: {
        pdf_path: z.string().describe("Absolute path to the accounts PDF"),
        entity: z.string().optional().describe("Entity name (defaults to the file name)"),
        period_end: z.string().optional().describe("Period end YYYY-MM-DD"),
        refresh: z.boolean().optional().describe("Recompute live, ignoring any "
          + "cached review (a live run takes several minutes)"),
      },
      outputSchema: summarySchema,
      _meta: { ui: { resourceUri } },
    },
    async ({ pdf_path, entity, period_end, refresh }): Promise<CallToolResult> => {
      const stem = path.basename(pdf_path).replace(/\.[^.]+$/, "");
      const name = entity ?? stem;
      const periodEnd = period_end ?? "2024-12-31";

      // Fast path: a pre-computed review served instantly. A live run is ~7 min
      // (sequential LLM calls), too slow for a chat tool call, so a cached review
      // (genuinely produced by this same pipeline) is returned unless refresh=true.
      const cacheSummary = path.join(APP_DIR, "build", "summaries", `${stem}.summary.json`);
      const cacheRegister = path.join(APP_DIR, "build", "summaries", `${stem}-register.xlsx`);
      if (!refresh && existsSync(cacheSummary)) {
        const summary = summarySchema.parse(JSON.parse(await fs.readFile(cacheSummary, "utf-8")));
        const regNote = existsSync(cacheRegister) ? `\n\nExcel register: ${cacheRegister}` : "";
        return {
          content: [{ type: "text", text: `${textFallback(summary)}${regNote}` }],
          structuredContent: summary,
        };
      }
      const summaryPath = path.join(os.tmpdir(), `frs102-${Date.now()}.summary.json`);
      const registerPath = path.join(os.tmpdir(), `frs102-${stem}-register.xlsx`);
      // Use the cached Azure layout if we have one (free, instant); else run the PDF.
      const cached = path.join(APP_DIR, "build", "layout", `${stem}.layout.json`);
      const source = existsSync(cached)
        ? ["--layout-json", cached] : ["--pdf", pdf_path];

      const { ok, stderr } = await runPipeline([
        ...source, "--entity", name, "--period-end", periodEnd,
        "--edition", "pre-PR2024", "--judgment", "--fronthalf", "--no-persist",
        "--summary-json", summaryPath, "--register", registerPath,
      ]);
      if (!ok || !existsSync(summaryPath)) {
        return {
          content: [{ type: "text", text: `Review failed.\n${stderr.slice(-1500)}` }],
          isError: true,
        };
      }
      const summary = summarySchema.parse(JSON.parse(await fs.readFile(summaryPath, "utf-8")));
      return {
        content: [{ type: "text", text: `${textFallback(summary)}\n\nExcel register: ${registerPath}` }],
        structuredContent: summary,
      };
    },
  );

  registerAppResource(server,
    resourceUri,
    resourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(path.join(DIST_DIR, "mcp-app.html"), "utf-8");
      return { contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }] };
    },
  );

  return server;
}
