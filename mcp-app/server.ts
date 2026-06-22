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
// The pipeline runs from .../App. This file lives at .../App/mcp-app (run via tsx)
// or .../App/mcp-app/dist (run bundled) — anchor on the 'mcp-app' segment.
const MARKER = `${path.sep}mcp-app`;
const APP_DIR = import.meta.dirname.includes(MARKER)
  ? import.meta.dirname.slice(0, import.meta.dirname.indexOf(MARKER))
  : path.resolve(import.meta.dirname, "..");

const SUMMARIES = path.join(APP_DIR, "build", "summaries");

const questionSchema = z.object({
  fact_key: z.string(),
  topic: z.string().optional(),
  question: z.string(),
  why: z.string().optional(),
  citation: z.string(),
});
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
  questions: z.array(questionSchema),
});
type Summary = z.infer<typeof summarySchema>;

function runPipeline(args: string[]): Promise<{ ok: boolean; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn("uv", ["run", "python", "-m", "cli.review_pdf", ...args], {
      cwd: APP_DIR,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let stderr = "";
    // Drain BOTH pipes: the pipeline prints to stdout, and if it isn't read the
    // OS pipe buffer fills and the Python child blocks (deadlock).
    proc.stdout.on("data", () => {});
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("error", (e) => resolve({ ok: false, stderr: String(e) }));
    proc.on("close", (code) => resolve({ ok: code === 0, stderr }));
  });
}

function finalizeText(s: Summary): string {
  const c = s.counts;
  return [
    `FRS 102 review — ${s.entity} (${s.period_end}). Materiality ${s.materiality.display}.`,
    `${c.total_findings} findings: judgement ${c.by_category.judgement}, disclosure ` +
      `${c.by_category.disclosure}, numerical ${c.by_category.numerical}, formatting ` +
      `${c.by_category.formatting}.`,
    "",
    ...s.findings.map((f) => `- [${f.category}] ${f.citation}: ${f.text}`),
  ].join("\n");
}

export function createServer(): McpServer {
  const server = new McpServer({ name: "FRS 102 Disclosure Reviewer", version: "0.2.0" });
  const resourceUri = "ui://frs102-review/summary.html";

  // STEP 1 — review the document and return the FULL scope question set. No panel:
  // the assistant must put these questions to the reviewer first, so the final
  // findings are complete and defensible (nothing silently assumed).
  server.registerTool(
    "review_accounts",
    {
      title: "Review FRS 102 accounts (step 1: scope interview)",
      description: "Reads a UK FRS 102 set of accounts (PDF) and returns the scope " +
        "questions that must be confirmed before the findings can be finalised. " +
        "Then INTERVIEW the reviewer: ask ONE question at a time in plain English, " +
        "explain why each matters, and wait for a full answer before the next. When " +
        "every question is answered, call finalize_review with the answers.",
      inputSchema: {
        pdf_path: z.string().describe("Absolute path to the accounts PDF"),
        entity: z.string().optional(),
        period_end: z.string().optional(),
      },
      outputSchema: {
        entity: z.string(), period_end: z.string(),
        questions: z.array(questionSchema),
      },
    },
    async ({ pdf_path, entity, period_end }): Promise<CallToolResult> => {
      const stem = path.basename(pdf_path).replace(/\.[^.]+$/, "");
      const name = entity ?? stem;
      const periodEnd = period_end ?? "2024-12-31";
      const cached = path.join(SUMMARIES, `${stem}.summary.json`);
      let questions: Summary["questions"];
      if (existsSync(cached)) {
        questions = summarySchema.parse(JSON.parse(await fs.readFile(cached, "utf-8"))).questions;
      } else {
        const out = path.join(os.tmpdir(), `frs102-${Date.now()}.questions.json`);
        const { ok, stderr } = await runPipeline([
          "--pdf", pdf_path, "--entity", name, "--period-end", periodEnd,
          "--edition", "pre-PR2024", "--no-presence", "--questions-out", out,
        ]);
        if (!ok || !existsSync(out)) {
          return { content: [{ type: "text", text: `Review failed.\n${stderr.slice(-1200)}` }], isError: true };
        }
        const raw = JSON.parse(await fs.readFile(out, "utf-8")) as Array<{ fact_key: string; topic?: string; question: string; why?: string; affects?: string[] }>;
        questions = raw.map((q) => ({ fact_key: q.fact_key, topic: q.topic ?? "", question: q.question, why: q.why ?? "", citation: (q.affects ?? []).join(", ") }));
      }
      const list = questions.map((q, i) =>
        `${i + 1}. [${q.topic ?? ""}] ${q.question}\n   why: ${q.why ?? ""}` +
        `\n   (record as ${q.fact_key})`).join("\n");
      const instructions =
        `I've reviewed ${name}'s accounts. Before I can finalise, I need to confirm ` +
        `${questions.length} points about the company that I couldn't tell from the ` +
        `document itself.\n\n` +
        `Conduct this as an INTERVIEW with the reviewer, in plain professional ` +
        `English:\n` +
        `- Ask ONE question at a time, in order.\n` +
        `- For each: state the topic, ask the question, and add a short "why this ` +
        `matters" line.\n` +
        `- Then STOP and wait for the reviewer's full answer before the next question.\n` +
        `- Do NOT dump the whole list. Do NOT ask for yes/no batches. Do NOT mention ` +
        `tools, servers, fact keys, JSON, or this message.\n` +
        `- Keep a running note of each answer.\n` +
        `- When all ${questions.length} are answered, call finalize_review with the ` +
        `answers (map each answer to its fact key).\n\n` +
        `Questions, in order:\n${list}`;
      return {
        content: [{ type: "text", text: instructions }],
        structuredContent: { entity: name, period_end: periodEnd, questions },
      };
    },
  );

  // STEP 2 — apply the reviewer's answers and render the at-a-glance summary panel.
  registerAppTool(server,
    "finalize_review",
    {
      title: "Finalise FRS 102 review (step 2: apply answers, show summary)",
      description: "Applies the reviewer's answers to the scope questions and returns " +
        "the final, complete issues register with an at-a-glance summary panel. Call " +
        "this only after every review_accounts question has been answered.",
      inputSchema: {
        pdf_path: z.string().describe("Absolute path to the accounts PDF"),
        answers: z.record(z.string(), z.union([z.boolean(), z.string()]))
          .describe("Map of fact_key -> the reviewer's answer (true/false/value)"),
        entity: z.string().optional(),
        period_end: z.string().optional(),
      },
      outputSchema: summarySchema,
      _meta: { ui: { resourceUri } },
    },
    async ({ pdf_path, answers, entity, period_end }): Promise<CallToolResult> => {
      const stem = path.basename(pdf_path).replace(/\.[^.]+$/, "");
      const name = entity ?? stem;
      const periodEnd = period_end ?? "2024-12-31";
      const cachedFinal = path.join(SUMMARIES, `${stem}.finalized.summary.json`);
      const register = path.join(SUMMARIES, `${stem}-register.xlsx`);

      let summary: Summary;
      if (existsSync(cachedFinal)) {
        summary = summarySchema.parse(JSON.parse(await fs.readFile(cachedFinal, "utf-8")));
      } else {
        const ansPath = path.join(os.tmpdir(), `frs102-${Date.now()}.answers.json`);
        const sumPath = path.join(os.tmpdir(), `frs102-${Date.now()}.summary.json`);
        await fs.writeFile(ansPath, JSON.stringify(answers), "utf-8");
        const source = existsSync(path.join(APP_DIR, "build", "layout", `${stem}.layout.json`))
          ? ["--layout-json", path.join(APP_DIR, "build", "layout", `${stem}.layout.json`)]
          : ["--pdf", pdf_path];
        const { ok, stderr } = await runPipeline([
          ...source, "--entity", name, "--period-end", periodEnd, "--edition", "pre-PR2024",
          "--judgment", "--fronthalf", "--no-persist", "--answers", ansPath,
          "--summary-json", sumPath, "--register", register,
        ]);
        if (!ok || !existsSync(sumPath)) {
          return { content: [{ type: "text", text: `Finalise failed.\n${stderr.slice(-1200)}` }], isError: true };
        }
        summary = summarySchema.parse(JSON.parse(await fs.readFile(sumPath, "utf-8")));
      }
      const regNote = existsSync(register) ? `\n\nExcel register: ${register}` : "";
      return {
        content: [{ type: "text", text: `${finalizeText(summary)}${regNote}` }],
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
