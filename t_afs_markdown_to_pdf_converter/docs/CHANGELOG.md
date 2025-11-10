# Change Log

## 1.0.1 - 2025-01-16

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

## 1.0.0 - 2025-01-15

* Initial Release
  * Process Report Response action: Convert Markdown to styled PDF
  * Built-in AFS purple theme with branded footer logo
  * Support for custom document titles and timestamps
  * Base64-encoded PDF output for workflow integration
