"""Run Azure Layout over a PDF and save the result for inspection.

  uv run python -m cli.dump_layout "C:/path/to/accounts.pdf"

Writes build/layout/<name>.summary.json (counts + sample) and, with --full, the
raw AnalyzeResult as JSON. Use this to inspect real Layout output before
building the model->FS mapping.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.extract.pdf_layout import analyze_pdf, layout_summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf")
    ap.add_argument("--full", action="store_true", help="also dump raw result JSON")
    args = ap.parse_args()

    result = analyze_pdf(args.pdf)
    out_dir = Path("build/layout")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.pdf).stem
    summary = layout_summary(result)
    (out_dir / f"{stem}.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.full:
        raw = result.as_dict() if hasattr(result, "as_dict") else result
        (out_dir / f"{stem}.layout.json").write_text(
            json.dumps(raw, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8")
        print(f"raw layout written to {out_dir / f'{stem}.layout.json'}")


if __name__ == "__main__":
    main()
