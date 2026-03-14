#!/usr/bin/env python3
"""
Export docs/TECHNICAL_REPORT.md to docs/Technical_Report.pdf.
Requires: pip install markdown playwright && playwright install chromium
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_FILE = ROOT / "docs" / "TECHNICAL_REPORT.md"
PDF_FILE = ROOT / "docs" / "Technical_Report.pdf"
HTML_FILE = ROOT / "docs" / "_report_export.html"


def md_to_html() -> str:
    import markdown
    text = MD_FILE.read_text(encoding="utf-8")
    return markdown.markdown(text, extensions=["tables", "fenced_code"])


def build_document(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Football Analytics API – Technical Report</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; max-width: 800px; margin: 2em auto; padding: 0 1em; color: #222; }}
h1 {{ font-size: 1.5em; border-bottom: 1px solid #ccc; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.2em; margin-top: 1.2em; }}
h3 {{ font-size: 1.05em; margin-top: 1em; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
th {{ background: #f5f5f5; }}
pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 0.9em; }}
code {{ background: #f5f5f5; padding: 2px 5px; font-size: 0.9em; }}
a {{ color: #06c; }}
ul {{ padding-left: 1.5em; }}
p {{ margin: 0.6em 0; }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="load")
        page.pdf(path=str(pdf_path), margin={"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"})
        browser.close()


def main() -> int:
    if not MD_FILE.is_file():
        print(f"Error: {MD_FILE} not found", file=sys.stderr)
        return 1
    try:
        body = md_to_html()
    except Exception as e:
        print(f"Error converting Markdown: {e}", file=sys.stderr)
        return 1
    doc = build_document(body)
    HTML_FILE.parent.mkdir(parents=True, exist_ok=True)
    HTML_FILE.write_text(doc, encoding="utf-8")
    try:
        html_to_pdf(HTML_FILE, PDF_FILE)
    except Exception as e:
        print(f"Error generating PDF (is Playwright installed? run: playwright install chromium): {e}", file=sys.stderr)
        return 1
    HTML_FILE.unlink(missing_ok=True)
    print(f"Saved: {PDF_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
