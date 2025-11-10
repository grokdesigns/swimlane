#!/usr/bin/env python3
"""
Extract PDF and HTML from process_report_response output
Usage: python extract_pdf.py [input_json] [output_pdf] [output_html]
"""

import json
import base64
import sys
from pathlib import Path


def extract_pdf(input_json_path: str, output_pdf_path: str, output_html_path: str = None) -> None:
    """
    Extract base64-encoded PDF and HTML from JSON output and save to files
    
    Args:
        input_json_path: Path to the JSON output file
        output_pdf_path: Path where PDF should be saved
        output_html_path: Path where HTML should be saved (optional, derived from PDF path if not provided)
    """
    # Derive HTML path from PDF path if not provided
    if output_html_path is None:
        output_html_path = Path(output_pdf_path).with_suffix('.html')
    
    # Read the JSON output
    print(f"📖 Reading JSON from: {input_json_path}")
    try:
        with open(input_json_path, 'r') as f:
            content = f.read()
            if not content.strip():
                print(f"❌ JSON file is empty: {input_json_path}")
                sys.exit(1)
            output = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in file: {e}")
        print(f"   File: {input_json_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        sys.exit(1)
    
    # Check if conversion was successful
    if not output.get('success'):
        print(f"❌ Conversion failed: {output.get('message')}")
        sys.exit(1)
    
    # Extract PDF content
    pdf_content = output.get('pdf_content')
    if not pdf_content:
        print("❌ No PDF content found in output")
        sys.exit(1)
    
    # Extract HTML content
    html_content = output.get('html_content')
    if not html_content:
        print("❌ No HTML content found in output")
        sys.exit(1)
    
    # Decode base64 and write both files
    try:
        # Save PDF
        pdf_data = base64.b64decode(pdf_content)
        with open(output_pdf_path, 'wb') as pdf_file:
            pdf_file.write(pdf_data)
        
        # Save HTML
        html_data = base64.b64decode(html_content)
        with open(output_html_path, 'wb') as html_file:
            html_file.write(html_data)
        
        print(f"✅ Success: {output.get('message')}")
        print(f"📄 PDF saved to: {output_pdf_path}")
        print(f"📊 PDF size: {len(pdf_data):,} bytes")
        print(f"🌐 HTML saved to: {output_html_path}")
        print(f"📊 HTML size: {len(html_data):,} bytes")
        
    except Exception as e:
        print(f"❌ Error decoding/writing files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Default paths
    default_input = "data/process_report_response_output.json"
    default_output_pdf = "output.pdf"
    default_output_html = "output.html"
    
    # Parse command line arguments
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_pdf_path = sys.argv[2] if len(sys.argv) > 2 else default_output_pdf
    output_html_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Check if input file exists
    if not Path(input_path).exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Extract and save PDF and HTML
    extract_pdf(input_path, output_pdf_path, output_html_path)