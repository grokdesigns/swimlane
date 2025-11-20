# Change Log

## 1.1.0 - 2025-11-20

### Added
* Support for JSON-based timeline and MITRE technique enhancement
  - New optional `timelineEvents` JSON input for matching timeline timestamps to phases
  - New optional `mitreTechniques` JSON input for adding comments to MITRE ATT&CK technique references
  - Timeline phases are now sourced exclusively from JSON data for reliability
  - MITRE technique comments are automatically appended to technique descriptions in italics

### Changed
* **Architecture improvement**: Both timeline and MITRE enhancements now work on HTML DOM using BeautifulSoup
  - Previously attempted to manipulate markdown text with regex, which was fragile
  - Now converts markdown to HTML first, then enhances the DOM structure
  - Provides reliable, consistent processing without markdown syntax conflicts
* Timeline timestamp display now omits seconds for cleaner presentation
  - Example: `2025-11-09 11:12 UTC` instead of `2025-11-09 11:12:00 UTC`
* Phase indicators in markdown (e.g., " (Phase: xxx)") are now stripped from event descriptions
  - Phases are added to the visual timeline based solely on JSON lookup data

### Fixed
* Timeline phase detection now works reliably with JSON data instead of parsing markdown text
* MITRE technique comments are correctly positioned at the end of technique descriptions
* Eliminated issues with markdown syntax interference (asterisks, brackets) during enhancement

## 1.0.4 - 2025-11-17

### Added
* Support for timeline phases.

### Fixed
* Updated pip and OS packages to resolve vulnerabilities detected by Trivy.
  - 10 Python vulnerabilities resolved.
  - 39 Debian vulnerabilities resolved.
* Resolved issue with blank page under timeline.

## 1.0.3 - 2025-11-17

### Added
* Support for timeline visualizations.

## 1.0.2 - 2025-11-11

### Fixed
* Unordered lists in markdown now properly convert to `<ul>` and `<li>` HTML tags
  - Fixed issue where lists immediately following text without blank lines were rendered as inline text with `<br/>` tags
  - Enhanced `clean_markdown()` function to automatically insert blank lines before list items when needed
  - Ensures proper list rendering in both HTML and PDF output

### Changed
* Improved code documentation and comments throughout `process_report_response.py`
  - Removed debugging narratives and bug fix information from inline comments
  - Simplified function docstrings to be more concise and maintainable
  - Focused comments on describing what functions do rather than implementation history

## 1.0.1 - 2025-11-10

### Added
* HTML content output: Now returns both `pdf_content` and `html_content` (base64-encoded) for greater flexibility
* Markdown preprocessing engine to fix common formatting issues:
  - Normalizes excessive asterisks (e.g., `****text****` → `**text**`)
  - Automatically closes unclosed bold markers in list items
  - Fixes mixed bold/italic patterns
* URL auto-linking: Bare URLs are now automatically converted to clickable links in both HTML and PDF output
* Enhanced CSS for code blocks:
  - Horizontal scrolling support with `overflow-x: auto`
  - Word wrapping for long content that would overflow page boundaries
  - Improved styling for inline code and pre-formatted blocks
* Explicit CSS rules for `<strong>` and `<em>` elements to ensure proper bold and italic rendering

### Changed
* Updated output schema to include `html_content` field
* Improved code block readability with better contrast and wrapping behavior
* Enhanced extract_pdf.py script to extract both PDF and HTML files

### Fixed
* Bold text now properly renders in PDF output
* Code blocks no longer run off the right edge of the page
* List items with labels now correctly apply bold formatting
* URLs in reports are now properly clickable

## 1.0.0 - 2025-11-06

* Initial Release
  * Process Report Response action: Convert Markdown to styled PDF
  * Built-in AFS purple theme with branded footer logo
  * Support for custom document titles and timestamps
  * Base64-encoded PDF output for workflow integration
