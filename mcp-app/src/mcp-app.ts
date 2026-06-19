import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import "./global.css";

interface Summary {
  entity: string;
  period_end: string;
  materiality: { display: string; basis: string };
  counts: {
    total_findings: number;
    by_category: { judgement: number; disclosure: number; numerical: number; formatting: number };
    need_judgement: number;
    questions: number;
  };
}

const root = document.getElementById("root") as HTMLElement;

const CATS: { key: keyof Summary["counts"]["by_category"]; label: string; color: string }[] = [
  { key: "judgement", label: "Judgement", color: "#BA7517" },
  { key: "disclosure", label: "Disclosure", color: "#378ADD" },
  { key: "numerical", label: "Numerical", color: "#1D9E75" },
  { key: "formatting", label: "Formatting", color: "#888780" },
];

function card(label: string, value: string): string {
  return `<div style="background:var(--color-background-secondary);border-radius:var(--border-radius-md);padding:12px 14px;">
    <div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:4px;">${label}</div>
    <div style="font-size:22px;font-weight:500;">${value}</div></div>`;
}

function bar(label: string, count: number, max: number, color: string): string {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <div style="width:74px;font-size:13px;color:var(--color-text-secondary);">${label}</div>
    <div style="flex:1;height:14px;background:var(--color-background-secondary);border-radius:7px;overflow:hidden;">
      <div style="width:${pct}%;height:100%;background:${color};border-radius:7px;"></div></div>
    <div style="width:18px;text-align:right;font-size:13px;font-weight:500;">${count}</div></div>`;
}

function render(s: Summary): void {
  const c = s.counts;
  const max = Math.max(1, ...CATS.map((x) => c.by_category[x.key]));
  root.innerHTML =
    `<div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:14px;">
      <span style="font-size:17px;font-weight:500;">${s.entity}</span>
      <span style="font-size:12px;color:var(--color-text-secondary);">FRS 102 review · ${s.period_end}</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:18px;">
      ${card("Findings raised", String(c.total_findings))}
      ${card("Materiality", s.materiality.display)}
      ${card("Need judgement", String(c.need_judgement))}
      ${card("Questions", String(c.questions))}
    </div>
    <div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:10px;">Findings by category</div>
    ${CATS.map((x) => bar(x.label, c.by_category[x.key], max, x.color)).join("")}`;
}

function handleHostContextChanged(ctx: McpUiHostContext) {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
}

const app = new App({ name: "FRS 102 Review Summary", version: "0.1.0" });

app.onteardown = async () => ({});
app.onerror = console.error;
app.onhostcontextchanged = handleHostContextChanged;
app.ontoolresult = (result: CallToolResult) => {
  const s = result.structuredContent as Summary | undefined;
  if (s?.counts) render(s);
};

app.connect().then(() => {
  const ctx = app.getHostContext();
  if (ctx) handleHostContextChanged(ctx);
});
