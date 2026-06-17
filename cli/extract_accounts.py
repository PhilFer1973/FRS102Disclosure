"""Full extraction pipeline: PDF (or cached Layout) -> structured FS model ->
numerical gate.

  uv run python -m cli.extract_accounts --layout-json build/layout/FC.layout.json
  uv run python -m cli.extract_accounts --pdf path/to/accounts.pdf   # calls Azure

Reads a cached Layout result to avoid re-paying Azure during development.
Prints the structured statements and any numerical findings. On clean audited
accounts a correct pipeline yields zero findings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.extract.structure import assemble
from pipeline.llm_client import LLMClient
from pipeline.validate.checks import validate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--layout-json", help="cached Azure Layout result JSON")
    src.add_argument("--pdf", help="PDF to analyze via Azure (incurs cost)")
    ap.add_argument("--entity", default="")
    ap.add_argument("--period-end", default="")
    args = ap.parse_args()

    if args.layout_json:
        layout = json.loads(Path(args.layout_json).read_text(encoding="utf-8"))
        tables = layout["tables"]
    else:
        from pipeline.extract.pdf_layout import analyze_pdf
        result = analyze_pdf(args.pdf)
        tables = (result.as_dict() if hasattr(result, "as_dict") else result)["tables"]

    client = LLMClient()
    fs = assemble(tables, client, args.entity, args.period_end)

    for name, stmt in fs.statements.items():
        print(f"\n=== {name} ({len(stmt.items)} lines) ===")
        for it in stmt.items:
            d = "" if not it.derivation else \
                " = " + " ".join(f"{'+' if s > 0 else '-'}{cid}" for cid, s in it.derivation)
            cur = "" if it.current is None else f"{it.current:,}"
            print(f"  {it.id:42} {cur:>16}{d}")

    findings = validate(fs)
    print(f"\nnumerical gate: {len(findings)} findings")
    for f in findings:
        tag = "ERROR" if f.is_error else f.check_type
        print(f"  [{tag}] {f.location}: {f.description}")
    print("\n" + client.usage_summary())


if __name__ == "__main__":
    main()
