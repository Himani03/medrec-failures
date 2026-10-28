"""Render WRITEUP.md to WRITEUP.pdf (Markdown -> HTML -> headless Chrome).

Usage:
    python src/build_pdf.py
"""
import subprocess
from pathlib import Path

import markdown

from config import ROOT

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: Letter; margin: 0.55in 0.6in; }
body { font: 9.4pt/1.3 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1a1a1a; }
h1 { font-size: 16pt; margin: 0 0 4px; }
h1 + p { color: #555; margin-top: 0; }
h2 { font-size: 12.5pt; margin: 16px 0 6px; border-bottom: 1px solid #ddd; padding-bottom: 2px; }
h3 { font-size: 11pt; margin: 12px 0 4px; }
blockquote { margin: 8px 0; padding: 6px 12px; background: #f4f6f8; border-left: 4px solid #c0392b; font-weight: 600; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 6px 0 10px; }
th, td { border: 1px solid #d8d8d8; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #f2f2f2; }
img { max-width: 64%; display: block; margin: 6px auto; }
img[alt=Workflow] { max-width: 50%; }
code { font-size: 8.8pt; background: #f3f3f3; padding: 0 2px; }
hr { page-break-after: always; border: 0; }
"""


APPENDIX_FILES = [  # (title, summary file); missing files are skipped. Full tables for other runs live in results/.
    ("A2. Failure 1, qwen2.5:3b: all arms", "results/summary_stop_instruction_qwen2.5-3b.md"),
    ("A3. Failure 2, qwen2.5:3b: top vs bottom, with the format example", "results/summary_list_position_qwen2.5-3b.md"),
    ("A4. Failure 2, qwen2.5:3b: top vs bottom, example removed", "results/summary_list_position_noex_qwen2.5-3b.md"),
]

REPRO = """## A5. Reproduce, and where the rest is

`pip install -r requirements.txt`, then `bash run_all.sh`. It runs the 48 unit tests and rebuilds every table, figure, this PDF and the slides from the cached model outputs in about 30 seconds. With Ollama running, deleting `results/cache/` reruns qwen2.5:3b from scratch. `WITH_GPT=1` also reruns gpt-5.4-mini (needs `OPENAI_API_KEY` in `.env`).

Not printed here, but in the repo: gpt-5.4-mini tables for both failures and the allergy test (`results/summary_*_gpt-5.4-mini.md`), the example-leak table (`results/summary_example_leak_qwen2.5-3b.md`), the broad probe on 148 real notes (`results/probe_qwen2.5-3b.md`), every raw model answer (`results/*/*.jsonl`), the hand-review log (`review/`), and the reworded and two-step prompts (`src/prompts.py`)."""


def appendix():
    from prompts import EXTRACT, PROBE_STOPPED
    parts = ["## A1. Prompts (exactly as sent; {note} is the note text)"]
    for name, text in (("Default extraction", EXTRACT), ("Direct question (mechanism test for Failure 1)", PROBE_STOPPED)):
        parts.append(f"**{name}**\n\n```\n{text.replace('{{', '{').replace('}}', '}')}\n```")
    for title, rel in APPENDIX_FILES:
        path = ROOT / rel
        if path.exists():
            body = path.read_text().split("\n", 1)[1]  # drop the file's own '# title' line
            for cut in ("\n## Main-case errors", "\n## Same drug kept", "\n## [real]" if "noex" in rel else "\n## @@"):
                body = body.split(cut)[0]  # case lists and repeated tables stay in the repo
            body = body.replace("\n## ", "\n#### ")
            parts.append(f"## {title}\n{body}")
    parts.append(REPRO)
    return "\n\n".join(parts)


def main():
    md = (ROOT / "WRITEUP.md").read_text().replace("[[APPENDIX]]", appendix())
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    html = ROOT / "WRITEUP.html"
    html.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{body}")
    pdf = ROOT / "WRITEUP.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True)
    html.unlink()
    print(f"-> {pdf}")


if __name__ == "__main__":
    main()
