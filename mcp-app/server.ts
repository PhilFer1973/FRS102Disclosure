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
  citation: z.string().optional(),
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

function finalizePresentation(s: Summary, registerPath: string): string {
  const c = s.counts;
  const order = { judgement: 0, disclosure: 1, numerical: 2, formatting: 3 } as Record<string, number>;
  const findings = [...s.findings].sort((a, b) => (order[a.category] ?? 9) - (order[b.category] ?? 9));
  const list = findings.map((f) => `- [${f.category}] ${f.citation}${f.status ? ` (${f.status})` : ""}: ${f.text}`).join("\n");
  return [
    `The review of ${s.entity} (year ended ${s.period_end}) is complete and the summary panel is shown above. ` +
      `Materiality is ${s.materiality.display}. There are ${c.total_findings} findings.`,
    "",
    "Now present these findings to the reviewer, in plain professional English:",
    "- Go through them grouped by type, most important first: matters of JUDGEMENT " +
      "(recognition/measurement) first, then DISCLOSURE points, then NUMERICAL items.",
    "- For EACH finding say three things plainly: (1) what the issue is, (2) where in " +
      "the accounts it relates to (which note or statement), and (3) what the reviewer " +
      "should do about it — add the disclosure, verify the figure, or consider the point.",
    "- Give the FRS 102 / Companies Act reference for each so they can look it up.",
    `- Mention the full issues register is saved as an Excel file (${registerPath}).`,
    "- Speak ONLY about the accounts and what to do. Do NOT mention this tool, the " +
      "pipeline, OCR, embedded paragraphs, deduplication, or anything technical.",
    "",
    "Findings:",
    list,
  ].join("\n");
}

function runCapture(args: string[]): Promise<{ ok: boolean; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn("uv", ["run", "python", ...args], {
      cwd: APP_DIR, env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("error", (e) => resolve({ ok: false, stdout, stderr: String(e) }));
    proc.on("close", (code) => resolve({ ok: code === 0, stdout, stderr }));
  });
}

// next_question prints one JSON line to stdout; take the last JSON-looking line.
function lastJsonLine(s: string): any {
  const lines = s.trim().split(/\r?\n/).filter((l) => l.trim().startsWith("{"));
  return lines.length ? JSON.parse(lines[lines.length - 1]) : null;
}

function interviewOne(name: string, q: any, first: boolean): string {
  return [
    first ? `I've reviewed ${name}'s accounts. I need to confirm a few points I `
      + `couldn't determine from the document before I can finalise.` : "",
    "Put THIS one question to the reviewer, in plain professional English, then wait "
      + "for their answer:",
    `  Topic: ${q.topic || "—"}`,
    `  Question: ${q.question}`,
    q.why ? `  Why it matters: ${q.why}` : "",
    "",
    "After they answer, call next_question again with ALL answers gathered so far "
      + `(each as ${q.fact_key}-style key -> true/false/value, including this one). `
      + "Ask only this one question now — never list others, never ask for yes/no "
      + "batches, never mention tools or fact keys. When next_question reports it is "
      + "done, call finalize_review with the collected answers.",
  ].filter(Boolean).join("\n");
}

export function createServer(): McpServer {
  const server = new McpServer({ name: "FRS 102 Disclosure Reviewer", version: "0.2.0" });
  const resourceUri = "ui://frs102-review/summary.html";

  const profileFor = (stem: string) => path.join(SUMMARIES, `${stem}.profile.json`);
  const poolFor = (stem: string) => path.join(SUMMARIES, `${stem}.qpool.json`);
  const rulesFile = path.join(SUMMARIES, "rules.pre-PR2024.json");

  async function askNext(stem: string, answers: Record<string, unknown> | undefined) {
    const args = ["-m", "cli.next_question", "--base", profileFor(stem),
      "--questions", poolFor(stem)];
    if (existsSync(rulesFile)) args.push("--rules", rulesFile);
    if (answers && Object.keys(answers).length) {
      const ansPath = path.join(os.tmpdir(), `frs102-${Date.now()}.ans.json`);
      await fs.writeFile(ansPath, JSON.stringify(answers), "utf-8");
      args.push("--answers", ansPath);
    }
    const res = await runCapture(args);
    return { data: lastJsonLine(res.stdout), stderr: res.stderr };
  }

  // STEP 1 — start the ADAPTIVE scope interview. Returns the FIRST question only;
  // the assistant asks it, then loops next_question with the answers so far. Each
  // answer prunes dependent questions, so only the gating facts that matter are
  // ever put to the reviewer. No panel here (the panel is the finalise step).
  server.registerTool(
    "review_accounts",
    {
      title: "Review FRS 102 accounts (step 1: start scope interview)",
      description: "Reads a UK FRS 102 set of accounts (PDF) and starts an adaptive " +
        "scope interview, returning the FIRST question to put to the reviewer. After " +
        "each answer, call next_question with ALL answers gathered so far to get the " +
        "next question; when it reports done, call finalize_review. Ask one question " +
        "at a time, in plain English, and explain why it matters.",
      inputSchema: {
        pdf_path: z.string().describe("Absolute path to the accounts PDF"),
        entity: z.string().optional(),
        period_end: z.string().optional(),
      },
      outputSchema: {
        entity: z.string(), period_end: z.string(),
        done: z.boolean(), remaining: z.number(), question: questionSchema.optional(),
      },
    },
    async ({ pdf_path, entity, period_end }): Promise<CallToolResult> => {
      const stem = path.basename(pdf_path).replace(/\.[^.]+$/, "");
      const name = entity ?? stem;
      const periodEnd = period_end ?? "2024-12-31";
      if (!existsSync(profileFor(stem)) || !existsSync(poolFor(stem))) {
        const layout = path.join(APP_DIR, "build", "layout", `${stem}.layout.json`);
        const source = existsSync(layout) ? ["--layout-json", layout] : ["--pdf", pdf_path];
        const gen = await runPipeline([...source, "--entity", name, "--period-end",
          periodEnd, "--edition", "pre-PR2024", "--no-presence", "--no-persist",
          "--profile-out", profileFor(stem), "--questions-out", poolFor(stem)]);
        if (!gen.ok) return { content: [{ type: "text", text: `Review failed.\n${gen.stderr.slice(-1200)}` }], isError: true };
      }
      const { data, stderr } = await askNext(stem, undefined);
      if (!data) return { content: [{ type: "text", text: `Review failed.\n${stderr.slice(-1200)}` }], isError: true };
      const text = data.done
        ? `I've reviewed ${name}'s accounts and could resolve everything from the `
          + `document — no scope questions needed. Call finalize_review now.`
        : interviewOne(name, data.question, true);
      return {
        content: [{ type: "text", text }],
        structuredContent: { entity: name, period_end: periodEnd, done: data.done,
          remaining: data.remaining, question: data.question ?? undefined },
      };
    },
  );

  // STEP 1b — the adaptive loop: given answers so far, return the next question or
  // signal the interview is complete.
  server.registerTool(
    "next_question",
    {
      title: "Next scope question (or finish the interview)",
      description: "Given the answers gathered so far, returns the next scope " +
        "question or signals the interview is complete. Call after each answer. Ask " +
        "one question at a time; when done is true, call finalize_review.",
      inputSchema: {
        pdf_path: z.string(),
        answers: z.record(z.string(), z.union([z.boolean(), z.string()]))
          .describe("All answers gathered so far, fact_key -> true/false/value"),
        entity: z.string().optional(),
      },
      outputSchema: { done: z.boolean(), remaining: z.number(),
        question: questionSchema.optional() },
    },
    async ({ pdf_path, answers, entity }): Promise<CallToolResult> => {
      const stem = path.basename(pdf_path).replace(/\.[^.]+$/, "");
      const name = entity ?? stem;
      if (!existsSync(profileFor(stem))) {
        return { content: [{ type: "text", text: "Call review_accounts first." }], isError: true };
      }
      const { data, stderr } = await askNext(stem, answers);
      if (!data) return { content: [{ type: "text", text: `Failed.\n${stderr.slice(-1000)}` }], isError: true };
      const text = data.done
        ? "All scope questions answered — call finalize_review now with the answers gathered."
        : interviewOne(name, data.question, false);
      return {
        content: [{ type: "text", text }],
        structuredContent: { done: data.done, remaining: data.remaining,
          question: data.question ?? undefined },
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
      return {
        content: [{ type: "text", text: finalizePresentation(summary, register) }],
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
