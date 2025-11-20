# connector/src/process_report_response.py
"""
Process Report Response - Markdown to PDF Converter
Converts Markdown text to professionally styled PDF with AFS purple theme

FONT INSTALLATION INSTRUCTIONS:
To enable the enhanced typography, download and install these fonts:

1. Inter font family:
   - Download from: https://fonts.google.com/specimen/Inter
   - Files needed: Inter-Light.ttf, Inter-Regular.ttf, Inter-SemiBold.ttf, Inter-Bold.ttf

2. Montserrat font family (for headings):
   - Download from: https://fonts.google.com/specimen/Montserrat
   - Files needed: Montserrat-SemiBold.ttf, Montserrat-Bold.ttf

3. JetBrains Mono (for code):
   - Download from: https://fonts.google.com/specimen/JetBrains+Mono
   - File needed: JetBrainsMono-Regular.ttf

Place all font files in: /app/assets/fonts/
(Create the fonts subdirectory if it doesn't exist)

The Dockerfile should copy these fonts during build:
COPY connector/assets/fonts /app/assets/fonts

If fonts are not available, the system will fall back to system fonts.
"""

from src.runner_override import RunnerOverride as RO
import base64
import datetime as dt
import json
import os
import re
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
/* Local Font Faces - Place font files in /app/assets/fonts/ directory */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 300;
  src: url('/app/assets/fonts/Inter_18pt-Light.ttf') format('truetype');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  src: url('/app/assets/fonts/Inter_18pt-Regular.ttf') format('truetype');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  src: url('/app/assets/fonts/Inter_18pt-SemiBold.ttf') format('truetype');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  src: url('/app/assets/fonts/Inter_18pt-Bold.ttf') format('truetype');
}

@font-face {
  font-family: 'Montserrat';
  font-style: normal;
  font-weight: 600;
  src: url('/app/assets/fonts/Montserrat-SemiBold.ttf') format('truetype');
}

@font-face {
  font-family: 'Montserrat';
  font-style: normal;
  font-weight: 700;
  src: url('/app/assets/fonts/Montserrat-Bold.ttf') format('truetype');
}

@font-face {
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 400;
  src: url('/app/assets/fonts/JetBrainsMono-Regular.ttf') format('truetype');
}

@page {
  size: Letter;
  margin: 30mm 20mm 22mm;

  /* top rule + top-right title */
  @top-center { content: ""; display:block; height:1px; background:#5B2A86; opacity:.45; }
  @top-right  { content: "{{ doc_title_css }}"; font-size:9pt; color:#555; vertical-align:middle; font-weight:600; }

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
html {
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-weight: 400;
  font-size: 11pt;
  color: #0f172a;
  line-height: 1.6;
}
body { margin: 0; }

/* Headings with enhanced typography */
h1 {
  font-family: 'Montserrat', 'Inter', sans-serif;
  font-size: 24pt;
  font-weight: 700;
  color: #5B2A86;
  margin: 0 0 .5em;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 2px rgba(91, 42, 134, 0.1);
}

h2 {
  string-set: section content();
  font-family: 'Montserrat', 'Inter', sans-serif;
  font-size: 16pt;
  font-weight: 700;
  border-bottom: 2px solid #5B2A86;
  padding-bottom: 4pt;
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  color: #2d2a2e;
  page-break-after: avoid;
  letter-spacing: -0.01em;
}

h3 {
  font-family: 'Montserrat', 'Inter', sans-serif;
  font-size: 13pt;
  font-weight: 600;
  color: #4a3a6b;
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  page-break-after: avoid;
}

/* Enhanced paragraph and list styling */
p, li { color: #1e293b; orphans: 3; widows: 3; }
p { margin: 0.6em 0; }

a { color: #5B2A86; text-decoration: none; font-weight: 500; }
a:hover { text-decoration: underline; }

ul, ol {
  margin: .8em 0 .8em 1.2em;
  page-break-inside: avoid;
  page-break-before: avoid;
}

li {
  margin: .25em 0;
  line-height: 1.5;
}

/* Enhanced blockquotes */
blockquote {
  border-left: 4px solid #5B2A86;
  margin: 1em 0;
  padding: .6em 1.2em;
  color: #475569;
  background: linear-gradient(to right, #f9f7fc, #ffffff);
  border-radius: 0 4px 4px 0;
  font-style: italic;
}

/* Enhanced table styling with zebra striping */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.2em 0;
  font-size: 10pt;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

th, td {
  border: 1px solid #e2e8f0;
  padding: 8pt 10pt;
  vertical-align: top;
  text-align: left;
}

th {
  background: linear-gradient(to bottom, #5B2A86, #4a2270);
  color: #ffffff;
  font-weight: 600;
  text-align: left;
  font-size: 10pt;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-size: 9pt;
}

/* Zebra striping for table rows */
tbody tr:nth-child(odd) {
  background: #ffffff;
}

tbody tr:nth-child(even) {
  background: #f8fafc;
}

tbody tr:hover {
  background: #f1f5f9;
}

/* Enhanced code blocks with better styling */
pre, code {
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

pre {
  background: linear-gradient(to bottom, #1e293b, #0f172a);
  color: #e2e8f0;
  padding: 12pt 14pt;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  border-left: 4px solid #5B2A86;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  line-height: 1.5;
  font-size: 9.5pt;
}

code {
  background: #f1f5f9;
  color: #5B2A86;
  padding: 2pt 5pt;
  border-radius: 4px;
  word-wrap: break-word;
  font-size: 9.5pt;
  font-weight: 500;
  border: 1px solid #e2e8f0;
}

pre code {
  background: transparent;
  padding: 0;
  color: inherit;
  border: none;
  font-weight: 400;
}

/* Enhanced emphasis */
strong, b { font-weight: 700; color: #0f172a; }
em, i { font-style: italic; color: #475569; }

/* Page break controls */
h2, h3, blockquote, table, pre { page-break-inside: avoid; }

/* Enhanced horizontal rule */
hr {
  border: none;
  border-top: 2px solid #e2e8f0;
  margin: 16pt 0;
  background: linear-gradient(to right, transparent, #e2e8f0, transparent);
}

/* Visual Timeline Styles */
.timeline-heading {
  font-size: 11pt;
  font-weight: 700;
  color: #2d2a2e;
  margin-top: 1em;
  margin-bottom: 0.8em;
  page-break-after: avoid;
}

.timeline-container {
  margin: 0 0 1.5em 0;
  padding: 0;
}

.timeline-entry {
  display: flex;
  padding-bottom: 1.5em;
  page-break-inside: avoid;
}

.timeline-entry:last-child {
  padding-bottom: 0;
}

.timeline-marker-wrapper {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 1.5em;
}

.timeline-marker {
  width: 12px;
  height: 12px;
  background: #5B2A86;
  border: 3px solid #f9f7fc;
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: #5B2A86;
  opacity: 0.4;
  margin-top: 0.3em;
  min-height: 2em;
}

.timeline-content {
  flex: 1;
  padding-top: 0;
}

.timeline-time-row {
  margin-bottom: 0.2em;
  line-height: 1.4;
}

.timeline-time {
  display: inline-block;
  font-size: 9.5pt;
  font-weight: 600;
  color: #5B2A86;
  letter-spacing: 0.3px;
  vertical-align: middle;
}

.timeline-event {
  font-size: 10.5pt;
  color: #2d2a2e;
  line-height: 1.5;
}

.event-phase {
  display: inline-block;
  padding: 1.6pt 6.4pt;
  border-radius: 9.6px;
  font-size: 6.4pt;
  font-weight: 600;
  color: #1e293b;
  text-transform: capitalize;
  letter-spacing: 0.3px;
  margin-left: 0.8em;
  vertical-align: middle;
}

.event-phase.preparation {
  background: #99cfff;
}

.event-phase.detection {
  background: #ffe082;
}

.event-phase.containment {
  background: #f5a3a3;
}

.event-phase.eradication {
  background: #a0d8e4;
}

.event-phase.recovery {
  background: #a4d4ae;
}

.event-phase.post-incident {
  background: #33cbb7;
}
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
    Convert logo file to data URI for embedding in PDF.
    Searches for logo in /app/assets/ directory.
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


def parse_mitre_techniques_json(mitre_json_str: str) -> dict:
    """
    Parse MITRE techniques JSON and create a lookup dictionary.
    
    Args:
        mitre_json_str: JSON string containing MITRE techniques organized by tactic
    
    Returns:
        Dictionary mapping technique IDs to their comments
        Example: {"T1190": "Test", "T1078.004": None}
    """
    if not mitre_json_str or not mitre_json_str.strip():
        return {}
    
    try:
        mitre_data = json.loads(mitre_json_str)
        technique_lookup = {}
        
        for tactic, techniques in mitre_data.items():
            if not isinstance(techniques, list):
                continue
            
            for tech in techniques:
                if not isinstance(tech, dict):
                    continue
                
                technique_str = tech.get('technique', '')
                # Extract technique ID (e.g., "T1190" from "T1190 - Exploit Public-Facing Application")
                technique_match = re.match(r'^(T\d+(?:\.\d+)?)', technique_str)
                if technique_match:
                    tech_id = technique_match.group(1)
                    comment = tech.get('comment')
                    technique_lookup[tech_id] = comment
                    logger.debug(f"Loaded MITRE technique: {tech_id} with comment: {comment}")
        
        logger.info(f"Loaded {len(technique_lookup)} MITRE techniques from JSON")
        return technique_lookup
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse MITRE techniques JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error processing MITRE techniques: {e}")
        return {}


def parse_timeline_events_json(timeline_json_str: str) -> dict:
    """
    Parse timeline events JSON and create a lookup dictionary.
    
    Args:
        timeline_json_str: JSON string containing timeline events
    
    Returns:
        Dictionary mapping timestamps to phase information
        Example: {"2025-11-15T23:48": "detection"}
    """
    if not timeline_json_str or not timeline_json_str.strip():
        return {}
    
    try:
        timeline_data = json.loads(timeline_json_str)
        timeline_lookup = {}
        
        if not isinstance(timeline_data, list):
            logger.warning("Timeline JSON is not an array")
            return {}
        
        for event in timeline_data:
            if not isinstance(event, dict):
                continue
            
            date = event.get('date', '')
            phase = event.get('phase')
            
            if date:
                # Normalize timestamp for matching (remove timezone info for comparison)
                normalized_date = date.replace('Z', '').strip()
                timeline_lookup[normalized_date] = phase
                logger.debug(f"Loaded timeline event: {normalized_date} -> {phase}")
        
        logger.info(f"Loaded {len(timeline_lookup)} timeline events from JSON")
        return timeline_lookup
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse timeline events JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error processing timeline events: {e}")
        return {}


def enhance_mitre_techniques_html(html_str: str, mitre_lookup: dict) -> str:
    """
    Enhance MITRE technique references in HTML with comments from JSON.
    This operates on the HTML after markdown conversion, which is more reliable
    than trying to manipulate markdown syntax.
    
    Args:
        html_str: HTML string containing MITRE techniques as links
        mitre_lookup: Dictionary mapping technique IDs to comments
    
    Returns:
        Enhanced HTML with comments added to MITRE techniques
    """
    if not mitre_lookup:
        logger.info("No MITRE technique enhancements to apply")
        return html_str
    
    logger.info("Enhancing MITRE technique references in HTML with comments")
    
    soup = BeautifulSoup(html_str, 'html.parser')
    
    # Find all links that contain MITRE technique patterns
    for link in soup.find_all('a', href=True):
        # Check if this is a MITRE ATT&CK link
        if 'attack.mitre.org/techniques/' in link.get('href', ''):
            # Extract technique ID from link text
            link_text = link.get_text()
            tech_match = re.match(r'^(T\d+(?:\.\d+)?)', link_text)
            
            if tech_match:
                tech_id = tech_match.group(1)
                comment = mitre_lookup.get(tech_id)
                
                if comment:
                    logger.debug(f"Adding comment to {tech_id}: {comment}")
                    
                    # Find the parent list item
                    parent_li = link.find_parent('li')
                    if parent_li:
                        # Add comment at the end of the list item as emphasized text
                        comment_tag = soup.new_tag('em')
                        comment_tag.string = f" (Comment: {comment})"
                        
                        # Append to the end of the list item
                        parent_li.append(comment_tag)
                        logger.debug(f"Added comment to {tech_id} in list item")
                    else:
                        # If not in a list, add after the link's parent paragraph
                        parent_p = link.find_parent('p')
                        if parent_p:
                            comment_tag = soup.new_tag('em')
                            comment_tag.string = f" (Comment: {comment})"
                            parent_p.append(comment_tag)
                            logger.debug(f"Added comment to {tech_id} in paragraph")
    
    logger.info("MITRE technique enhancement complete")
    return str(soup)


def enhance_timeline_html(html_str: str, timeline_lookup: dict = None) -> str:
    """
    Find timeline sections in HTML and replace them with visual timeline HTML.
    Works on the HTML DOM using BeautifulSoup for reliable parsing.
    
    Args:
        html_str: HTML string that may contain timeline sections
        timeline_lookup: Optional dictionary mapping timestamps to phases from JSON
    
    Returns:
        Enhanced HTML with visual timelines replacing plain lists
    """
    if timeline_lookup is None:
        timeline_lookup = {}
    
    soup = BeautifulSoup(html_str, 'html.parser')
    
    # Find all headings/paragraphs that contain "Timeline"
    timeline_headers = []
    for tag in soup.find_all(['p', 'h2', 'h3', 'h4']):
        text = tag.get_text()
        if re.search(r'(Incident\s+)?Timeline:?', text, re.IGNORECASE):
            timeline_headers.append(tag)
    
    if not timeline_headers:
        logger.info("No timeline sections found in HTML")
        return html_str
    
    logger.info(f"Found {len(timeline_headers)} timeline section(s) in HTML")
    
    # Process each timeline section
    for header in timeline_headers:
        # Extract heading text
        heading_match = re.search(r'((?:Incident\s+)?Timeline)', header.get_text(), re.IGNORECASE)
        heading = heading_match.group(1) if heading_match else "Timeline"
        
        # Find the next sibling list (ul or ol)
        next_sibling = header.find_next_sibling()
        timeline_list = None
        while next_sibling and next_sibling.name not in ['ul', 'ol']:
            next_sibling = next_sibling.find_next_sibling()
        
        if next_sibling and next_sibling.name in ['ul', 'ol']:
            timeline_list = next_sibling
        
        if not timeline_list:
            logger.debug(f"No list found after timeline header: {heading}")
            continue
        
        # Parse timeline entries from this list
        timeline_entries = []
        for li in timeline_list.find_all('li', recursive=False):
            text = li.get_text()
            # Pattern: (YYYY-MM-DD HH:MM:SS UTC) — Event description
            match = re.match(r'^\(([^)]+)\)\s*[—\-–]+\s*(.+)$', text.strip())
            if match:
                datetime_str = match.group(1).strip()
                event_desc = match.group(2).strip()
                
                # Strip out any " (Phase: xxx)" text from event description
                event_desc = re.sub(r'\s*\(Phase:\s*[^)]+\)\s*$', '', event_desc, flags=re.IGNORECASE).strip()
                
                # Look up phase in JSON by matching timestamp
                phase = None
                if timeline_lookup:
                    normalized_time = datetime_str.replace(' UTC', '').replace(' ', 'T').strip()
                    for key in timeline_lookup:
                        if normalized_time in key or key in normalized_time:
                            phase = timeline_lookup[key]
                            logger.debug(f"Matched timeline phase: {datetime_str} -> {phase}")
                            break
                
                timeline_entries.append((datetime_str, phase, event_desc))
        
        if timeline_entries:
            # Generate the visual timeline HTML
            timeline_html = generate_timeline_html(timeline_entries, heading)
            
            # Parse the timeline HTML and insert it
            timeline_soup = BeautifulSoup(timeline_html, 'html.parser')
            
            # Replace the header with our timeline
            header.replace_with(timeline_soup)
            
            # Remove the original list
            timeline_list.decompose()
            
            logger.info(f"Replaced timeline section '{heading}' with visual timeline ({len(timeline_entries)} events)")
        else:
            logger.warning(f"No valid timeline entries found in list for header: {heading}")
    
    return str(soup)


def strip_seconds_from_timestamp(timestamp: str) -> str:
    """
    Remove seconds from a timestamp string while preserving the format.
    
    Args:
        timestamp: Timestamp string (e.g., "2025-11-09 11:12:00 UTC" or "2025-11-09T11:12:00")
    
    Returns:
        Timestamp without seconds (e.g., "2025-11-09 11:12 UTC" or "2025-11-09T11:12")
    """
    # Pattern to match and remove :SS from timestamps
    # Handles both space-separated (2025-11-09 11:12:00 UTC) and T-separated (2025-11-09T11:12:00) formats
    timestamp = re.sub(r'(:\d{2})(:\d{2})', r'\1', timestamp)
    return timestamp


def generate_timeline_html(entries: list, heading: str = "Timeline") -> str:
    """
    Generate HTML for a visual timeline from parsed entries.
    
    Args:
        entries: List of tuples [(datetime_str, phase, event_description), ...]
                 Phase can be None if not provided.
        heading: The heading text to display above the timeline
    
    Returns:
        HTML string with styled timeline including heading
    """
    if not entries:
        return ""
    
    html_parts = [f'<h3 class="timeline-heading">{heading}</h3>']
    html_parts.append('<div class="timeline-container">')
    
    for i, (datetime_str, phase, event) in enumerate(entries):
        # Strip seconds from timestamp for display
        display_time = strip_seconds_from_timestamp(datetime_str)
        is_last = (i == len(entries) - 1)
        line_class = '' if is_last else ' timeline-has-line'
        
        # Build phase pill HTML if phase is provided
        phase_html = ''
        if phase:
            # Ensure phase is lowercase and matches CSS class names
            phase_class = phase.lower().replace(' ', '-')
            phase_display = phase.replace('-', ' ').title()
            phase_html = f'<span class="event-phase {phase_class}">{phase_display}</span>'
        
        html_parts.append(f'''
    <div class="timeline-entry{line_class}">
        <div class="timeline-marker-wrapper">
            <div class="timeline-marker"></div>
            {'' if is_last else '<div class="timeline-line"></div>'}
        </div>
        <div class="timeline-content">
            <div class="timeline-time-row">
                <div class="timeline-time">{display_time}</div>
                {phase_html}
            </div>
            <div class="timeline-event">{event}</div>
        </div>
    </div>''')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)




def process_urls(md_text: str) -> str:
    """
    Convert bare URLs into clickable markdown links by wrapping them in angle brackets.
    Avoids processing URLs already in markdown link syntax.
    """
    logger.info("Processing URLs for auto-linking")
    
    # Match URLs not already wrapped in markdown syntax
    url_pattern = r'(?<!\()(https?://[^\s<>\)]+)(?!\))'
    
    def replace_url(match):
        url = match.group(1)
        # Don't wrap if it's already in angle brackets
        if url.startswith('<') or url.endswith('>'):
            return url
        logger.debug(f"Converting bare URL to auto-link: {url[:60]}...")
        return f'<{url}>'
    
    md_text = re.sub(url_pattern, replace_url, md_text)
    logger.info("URL processing complete")
    
    return md_text


def clean_markdown(md_text: str, mitre_lookup: dict = None, timeline_lookup: dict = None) -> str:
    """
    Pre-process markdown text to fix common formatting issues:
    - Normalizes excessive asterisks (****text**** → **text**)
    - Closes unclosed bold markers in list items
    - Adds blank lines before lists for proper parsing
    - Converts bare URLs to markdown auto-links
    - Enriches timeline with phase information from JSON
    
    Note: MITRE technique enhancement happens after HTML conversion for better reliability
    """
    if timeline_lookup is None:
        timeline_lookup = {}
    original_length = len(md_text)
    logger.info(f"Starting markdown cleaning: {original_length} characters")
    logger.debug(f"First 500 chars:\n{md_text[:500]}")
    
    # Normalize sequences of 3+ asterisks to exactly 2
    md_text = re.sub(r'\*{3,}', '**', md_text)
    logger.info("Normalized excessive asterisks")
    logger.debug(f"After normalization (first 500):\n{md_text[:500]}")
    
    # Fix unclosed bold markers in list items and headers
    lines = []
    for i, line in enumerate(md_text.split('\n'), 1):
        original_line = line
        
        if not line.strip():
            lines.append(line)
            continue
        
        list_match = re.match(r'^(\s*)([-*•])\s+(.+)$', line)
        
        if list_match:
            indent, marker, content = list_match.groups()
            double_ast_count = content.count('**')
            
            # Fix unclosed bold markers (odd count of **)
            if double_ast_count % 2 != 0:
                label_match = re.match(r'^\*\*([^*]+?):\s*(.*)$', content)
                
                if label_match:
                    label, rest = label_match.groups()
                    content = f'**{label}:** {rest}'.strip()
                    logger.info(f"Line {i}: Fixed list item label bold")
                else:
                    content = content.rstrip() + '**'
                    logger.info(f"Line {i}: Closed bold at end of list item")
                
                line = f"{indent}{marker} {content}"
        else:
            double_ast_count = line.count('**')
            
            if double_ast_count % 2 != 0:
                if line.strip().startswith('**') and ':' in line:
                    line = re.sub(r'^\*\*([^*]+?):\s*$', r'**\1:**', line)
                    logger.info(f"Line {i}: Fixed header bold")
                else:
                    line = line.rstrip() + '**'
                    logger.info(f"Line {i}: Closed bold at end")
        
        lines.append(line)
    
    md_text = '\n'.join(lines)
    
    logger.info("Fixed unclosed bold markers")
    logger.debug(f"After bold fixes (first 500):\n{md_text[:500]}")
    
    # Add blank lines before lists for proper markdown parsing
    lines = md_text.split('\n')
    result_lines = []
    prev_line_was_blank = True
    prev_line_was_list = False
    
    for line in lines:
        stripped = line.lstrip()
        is_list_item = stripped.startswith(('- ', '* ', '+ ', '• '))
        is_blank = not line.strip()
        
        # Insert blank line before list if needed for proper parsing
        if is_list_item and not prev_line_was_blank and not prev_line_was_list:
            result_lines.append('')
            logger.debug(f"Added blank line before list item: {line[:50]}")
        
        result_lines.append(line)
        
        prev_line_was_blank = is_blank
        prev_line_was_list = is_list_item
    
    md_text = '\n'.join(result_lines)
    
    logger.info("Added blank lines before list items")
    logger.debug(f"After list formatting (first 500):\n{md_text[:500]}")
    
    # Process URLs for auto-linking
    md_text = process_urls(md_text)
    logger.debug(f"After URL processing (first 500):\n{md_text[:500]}")
    
    # Convert paragraph-based timeline entries to list format
    # Find lines that look like timeline entries: (YYYY-MM-DD HH:MM:SS UTC) — ...
    # that don't already start with a list marker
    lines = md_text.split('\n')
    result_lines = []
    prev_line = ''
    first_timeline_entry = True
    
    for line in lines:
        stripped = line.strip()
        # Check if this is a timeline entry without a list marker
        if re.match(r'^\(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+UTC\)', stripped):
            # This is a timeline entry - ensure it has a list marker
            if not re.match(r'^\s*[-*+•]\s+', line):
                # If this is the first timeline entry and the previous line is a heading,
                # insert a blank line first to ensure proper markdown list parsing
                if first_timeline_entry and prev_line.strip() and not prev_line.strip() == '':
                    # Check if previous line looks like a heading (contains "Timeline" or ends with ":")
                    if 'timeline' in prev_line.lower() or prev_line.strip().endswith(':'):
                        result_lines.append('')  # Add blank line
                        logger.debug("Inserted blank line before timeline list")
                
                first_timeline_entry = False
                
                # Add list marker
                indent = len(line) - len(stripped)
                line = ' ' * indent + '- ' + stripped
                logger.debug(f"Added list marker to timeline entry: {stripped[:60]}...")
        else:
            # Reset first_timeline_entry flag if we encounter a non-timeline line
            first_timeline_entry = True
        
        result_lines.append(line)
        prev_line = line
    
    md_text = '\n'.join(result_lines)
    logger.info("Converted paragraph-based timeline entries to list format")
    
    logger.info(f"Markdown cleaning complete: {len(md_text)} characters")
    
    return md_text


def md_to_html(md_text: str, mitre_lookup: dict = None, timeline_lookup: dict = None) -> str:
    """
    Convert markdown to HTML with cleaning and formatting.
    Enhancements (timeline and MITRE) are done on the HTML DOM for reliability.
    """
    if mitre_lookup is None:
        mitre_lookup = {}
    if timeline_lookup is None:
        timeline_lookup = {}
    
    # Clean markdown (timeline and MITRE enhancements happen after HTML conversion)
    cleaned_md = clean_markdown(md_text, mitre_lookup, timeline_lookup)
    
    # Convert markdown to HTML
    html = markdown(cleaned_md, extensions=["extra", "sane_lists", "smarty", "nl2br"], output_format="html5")
    html_str = str(BeautifulSoup(html, "html.parser"))
    
    # Enhance timelines in HTML (find and replace with visual timelines)
    html_str = enhance_timeline_html(html_str, timeline_lookup)
    
    # Enhance MITRE techniques in HTML (add comments from JSON)
    html_str = enhance_mitre_techniques_html(html_str, mitre_lookup)
    
    return html_str


def build_document_html(markdown_text: str, document_title: str, include_timestamp: bool,
                        footer_logo_data: Optional[str], footer_logo_height_mm: float,
                        mitre_lookup: dict = None, timeline_lookup: dict = None) -> str:
    """Build complete HTML document with AFS purple theme styling"""
    css = Template(THEME_CSS).render(
        doc_title_css=(document_title or "Report").replace('"', '\\"'),
        footer_logo_data=footer_logo_data or "",
        footer_logo_height_mm=footer_logo_height_mm,
    )
    return Template(HTML_TEMPLATE).render(
        css=css,
        content=md_to_html(markdown_text, mitre_lookup, timeline_lookup),
        doc_title=document_title or "Report",
        show_timestamp=bool(include_timestamp),
        timestamp=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )


class RunnerOverride(RO):
    """Converts Markdown text to professionally styled PDF documents"""

    def __init__(self, asset, asset_schema, http_proxy):
        super().__init__(asset, asset_schema, http_proxy)
        self.logger = logger
        self.logger.info("Process Report Response action initialized")

    def run(self, inputs, action_schema):
        """
        Convert markdown text to PDF with professional styling.
        
        Args:
            inputs: Dictionary containing markdown_text, document_title, include_timestamp,
                    mitreTechniques (JSON), timelineEvents (JSON)
            action_schema: Action schema definition
            
        Returns:
            Dictionary with success status, message, pdf_content (base64), html_content (base64)
        """
        try:
            markdown_text = inputs.get('markdown_text', '')
            document_title = inputs.get('document_title', 'Security Report')
            include_timestamp = inputs.get('include_timestamp', True)
            mitre_techniques_json = inputs.get('mitreTechniques', '')
            timeline_events_json = inputs.get('timelineEvents', '')
            
            # Validate inputs
            if not markdown_text or not markdown_text.strip():
                self.logger.warning("Empty markdown text provided")
                return {
                    'success': False,
                    'message': 'Markdown text is required and cannot be empty',
                    'pdf_content': None,
                    'html_content': None
                }
            
            if len(markdown_text) > 1_000_000:  # 1MB limit
                self.logger.warning(f"Markdown text too large: {len(markdown_text)} characters")
                return {
                    'success': False,
                    'message': 'Markdown text exceeds maximum size of 1MB',
                    'pdf_content': None,
                    'html_content': None
                }
            
            self.logger.info(f"Converting Markdown to PDF: '{document_title}' ({len(markdown_text)} characters)")
            
            # Parse optional JSON inputs
            mitre_lookup = parse_mitre_techniques_json(mitre_techniques_json)
            timeline_lookup = parse_timeline_events_json(timeline_events_json)
            
            self.logger.debug("Pre-processing markdown to clean formatting issues")
            
            footer_logo_data = _data_uri_for_logo(DEFAULT_FOOTER_LOGO)
            
            self.logger.debug("Building HTML document with AFS purple theme")
            html_str = build_document_html(
                markdown_text,
                document_title,
                include_timestamp,
                footer_logo_data,
                DEFAULT_FOOTER_LOGO_HEIGHT_MM,
                mitre_lookup,
                timeline_lookup
            )
            
            self.logger.debug("Generating PDF document")
            pdf_buffer = HTML(string=html_str, base_url="/app").write_pdf()
            pdf_base64 = base64.b64encode(pdf_buffer).decode('utf-8')
            html_base64 = base64.b64encode(html_str.encode('utf-8')).decode('utf-8')
            
            self.logger.info(f"Successfully generated PDF: {len(pdf_buffer)} bytes")
            
            return {
                'success': True,
                'message': f'Successfully converted {len(markdown_text)} characters to PDF ({len(pdf_buffer)} bytes)',
                'pdf_content': pdf_base64,
                'html_content': html_base64
            }
            
        except Exception as e:
            self.logger.error(f"Error converting Markdown to PDF: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Conversion failed: {str(e)}',
                'pdf_content': None,
                'html_content': None
            }