#!/usr/bin/env python3
# Markdown → PDF (Letter) with footer logo LEFT (margin box) and page X/Y RIGHT
from __future__ import annotations

import argparse, base64, datetime as dt, json, mimetypes, os
from typing import Dict, Optional
from bs4 import BeautifulSoup
from jinja2 import Template
from markdown import markdown
from weasyprint import HTML

THEME_CSS = r"""
@page {
  size: Letter;
  margin: 30mm 20mm 22mm;

  /* top rule + top-right title */
  @top-center { content: ""; display:block; height:1px; background:#5B2A86; opacity:.45; }
  @top-right  { content: "{{ doc_title_css }}"; font-size:9pt; color:#555; vertical-align:middle; }

  /* Footer: logo LEFT (data-URI), page counter RIGHT */
  @bottom-left  {
    content: url("{{ footer_logo_data }}");
    /* Height of the footer box; this also caps the rendered logo height */
    line-height: {{ footer_logo_height_mm }}mm;
  }
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 9pt; color:#444;
  }
}

/* Body typography */
html { font:300 11pt "Inter",system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; color:#0f172a; line-height:1.55; }
body { margin:0; }

h1 { font-size:22pt; color:#5B2A86; margin:0 0 .5em; }
h2 { string-set: section content(); font-size:15pt; border-bottom:2px solid #5B2A86; padding-bottom:3pt; margin-top:1.5em; color:#2d2a2e; }
h3 { font-size:13pt; color:#4a3a6b; margin-top:1em; }

p, li { color:#111; }
a { color:#5B2A86; text-decoration:none; }
ul, ol { margin:.5em 0 .5em 1.2em; }
li { margin:.15em 0; }

blockquote { border-left:3px solid #5B2A86; margin:.8em 0; padding:.5em 1em; color:#444; background:#f9f7fc; }

table { width:100%; border-collapse:collapse; margin:1em 0; font-size:10.25pt; }
th, td { border:1px solid #e2e2e7; padding:6pt 8pt; vertical-align:top; }
th { background:#f2f0f8; color:#333; text-align:left; }

pre, code { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace; }
pre { background:#0f172a; color:#e5e7eb; padding:8pt 10pt; border-radius:8px; overflow:hidden; }
code { background:#f1f5f9; padding:1pt 3pt; border-radius:5px; }

h2, h3, blockquote, table, pre { page-break-inside:avoid; }
hr { border:none; border-top:1px solid #e2e8f0; margin:12pt 0; }
"""

HTML_TEMPLATE = r"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{ doc_title }}</title>
    <style>{{ css }}</style>
  </head>
  <body>
    <h1>{{ doc_title }}</h1>
    {% if show_timestamp %}
      <p style="color:#555; font-size:10pt; margin-top:-6pt;">Generated {{ timestamp }}</p>
    {% endif %}
    <hr />
    {{ content|safe }}
  </body>
</html>
"""

def _data_uri_for(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime: mime = "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def md_to_html(md_text: str) -> str:
    html = markdown(md_text, extensions=["extra","sane_lists","smarty","nl2br"], output_format="html5")
    return str(BeautifulSoup(html, "html.parser"))

def build_document_html(markdown_text: str, document_title: str, include_timestamp: bool,
                        footer_logo_data: Optional[str], footer_logo_height_mm: float) -> str:
    css = Template(THEME_CSS).render(
        doc_title_css=(document_title or "Report").replace('"','\\"'),
        footer_logo_data=footer_logo_data or "",
        footer_logo_height_mm=footer_logo_height_mm,
    )
    return Template(HTML_TEMPLATE).render(
        css=css,
        content=md_to_html(markdown_text),
        doc_title=document_title or "Report",
        show_timestamp=bool(include_timestamp),
        timestamp=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )

def render_pdf(payload: Dict, output_path: str, base_url: Optional[str] = None) -> None:
    markdown_text   = payload.get("markdown_text", "")
    document_title  = payload.get("document_title", "Report")
    include_ts      = bool(payload.get("include_timestamp", True))
    footer_logo     = payload.get("footer_logo", "AFS_Wordmark_purple_horizontal.png")
    footer_logo_height_mm = float(payload.get("footer_logo_height_mm", 8.0))

    footer_logo_data = None
    if footer_logo:
        logo_path = os.path.join(base_url or os.getcwd(), footer_logo)
        if os.path.isfile(logo_path):
            footer_logo_data = _data_uri_for(logo_path)

    html_str = build_document_html(markdown_text, document_title, include_ts, footer_logo_data, footer_logo_height_mm)
    HTML(string=html_str, base_url=base_url or os.getcwd()).write_pdf(output_path)

def parse_args():
    ap = argparse.ArgumentParser(description="Render Markdown to a Letter-size PDF via WeasyPrint.")
    ap.add_argument("-i","--input", required=True, help="Path to JSON payload.")
    ap.add_argument("-o","--output", default="output.pdf", help="Output PDF path.")
    return ap.parse_args()

def main():
    args = parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)
    payload_dir = os.path.dirname(os.path.abspath(args.input)) or os.getcwd()
    render_pdf(payload, args.output, base_url=payload_dir)
    print(f"✓ PDF written to {args.output}")

if __name__ == "__main__":
    main()