# connector/src/process_report_response.py
"""
Process Report Response - Markdown to PDF Converter
Converts Markdown text to professionally styled PDF with AFS purple theme
"""

from src.runner_override import RunnerOverride as RO
import base64
import datetime as dt
import os
from typing import Optional
from bs4 import BeautifulSoup
from jinja2 import Template
from markdown import markdown
from weasyprint import HTML
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default footer logo configuration (built into container)
DEFAULT_FOOTER_LOGO = "AFS_wordmark_horizontal_purple.svg"
DEFAULT_FOOTER_LOGO_HEIGHT_MM = 8.0

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


def _data_uri_for_logo(logo_filename: str) -> Optional[str]:
    """
    Convert logo file to data URI for embedding in PDF
    Looks for logo in /app/assets/ directory (inside connector)
    """
    import mimetypes
    
    # Logo should be at /app/assets/ when deployed in container
    logo_path = f"/app/assets/{logo_filename}"
    
    if os.path.isfile(logo_path):
        mime, _ = mimetypes.guess_type(logo_path)
        if not mime:
            mime = "application/octet-stream"
        try:
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            logger.info(f"Successfully loaded logo from: {logo_path}")
            return f"data:{mime};base64,{b64}"
        except Exception as e:
            logger.error(f"Failed to read logo from {logo_path}: {e}")
            return None
    
    logger.error(f"Logo file not found: {logo_path}")
    return None


def md_to_html(md_text: str) -> str:
    """Convert Markdown to clean HTML"""
    html = markdown(md_text, extensions=["extra", "sane_lists", "smarty", "nl2br"], output_format="html5")
    return str(BeautifulSoup(html, "html.parser"))


def build_document_html(markdown_text: str, document_title: str, include_timestamp: bool,
                        footer_logo_data: Optional[str], footer_logo_height_mm: float) -> str:
    """Build complete HTML document with styling"""
    css = Template(THEME_CSS).render(
        doc_title_css=(document_title or "Report").replace('"', '\\"'),
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


class RunnerOverride(RO):
    """
    Process Report Response Action
    Converts Markdown to PDF with AFS purple theme
    """

    def __init__(self, asset, asset_schema, http_proxy):
        super().__init__(asset, asset_schema, http_proxy)
        self.logger = logger
        self.logger.info("Process Report Response action initialized")

    def run(self, inputs, action_schema):
        """
        Main execution method called by Turbine
        
        Args:
            inputs: Dictionary containing action inputs
            action_schema: Action schema definition
            
        Returns:
            Dictionary containing action outputs
        """
        try:
            # Extract inputs
            markdown_text = inputs.get('markdown_text', '')
            document_title = inputs.get('document_title', 'Security Report')
            include_timestamp = inputs.get('include_timestamp', True)
            
            # Validate input
            if not markdown_text or not markdown_text.strip():
                self.logger.warning("Empty markdown text provided")
                return {
                    'success': False,
                    'message': 'Markdown text is required and cannot be empty',
                    'pdf_content': None
                }
            
            if len(markdown_text) > 1_000_000:  # 1MB limit
                self.logger.warning(f"Markdown text too large: {len(markdown_text)} characters")
                return {
                    'success': False,
                    'message': 'Markdown text exceeds maximum size of 1MB',
                    'pdf_content': None
                }
            
            self.logger.info(f"Converting Markdown to PDF: '{document_title}' ({len(markdown_text)} characters)")
            
            # Load default footer logo (built into container)
            footer_logo_data = _data_uri_for_logo(DEFAULT_FOOTER_LOGO)
            
            # Build HTML document
            self.logger.debug("Building HTML document with AFS purple theme")
            html_str = build_document_html(
                markdown_text,
                document_title,
                include_timestamp,
                footer_logo_data,
                DEFAULT_FOOTER_LOGO_HEIGHT_MM
            )
            
            # Generate PDF
            self.logger.debug("Generating PDF document")
            pdf_buffer = HTML(string=html_str, base_url="/app").write_pdf()
            
            # Encode as base64
            pdf_base64 = base64.b64encode(pdf_buffer).decode('utf-8')
            
            self.logger.info(f"Successfully generated PDF: {len(pdf_buffer)} bytes")
            
            return {
                'success': True,
                'message': f'Successfully converted {len(markdown_text)} characters to PDF ({len(pdf_buffer)} bytes)',
                'pdf_content': pdf_base64
            }
            
        except Exception as e:
            self.logger.error(f"Error converting Markdown to PDF: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Conversion failed: {str(e)}',
                'pdf_content': None
            }