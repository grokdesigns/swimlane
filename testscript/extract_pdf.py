#!/usr/bin/env python3
"""
Extract PDF from process_report_response output
Usage: python extract_pdf.py [input_json] [output_pdf]
"""

import json
import base64
import sys
from pathlib import Path


def extract_pdf(input_json_path: str, output_pdf_path: str) -> None:
    """
    Extract base64-encoded PDF from JSON output and save to file
    
    Args:
        input_json_path: Path to the JSON output file
        output_pdf_path: Path where PDF should be saved
    """
    # Read the JSON output
    with open(input_json_path, 'r') as f:
        output = json.load(f)
    
    # Check if conversion was successful
    if not output.get('success'):
        print(f"❌ Conversion failed: {output.get('message')}")
        sys.exit(1)
    
    # Extract PDF content
    pdf_content = output.get('pdf_content')
    if not pdf_content:
        print("❌ No PDF content found in output")
        sys.exit(1)
    
    # Decode base64 and write to file
    try:
        pdf_data = base64.b64decode(pdf_content)
        with open(output_pdf_path, 'wb') as pdf_file:
            pdf_file.write(pdf_data)
        
        print(f"✅ Success: {output.get('message')}")
        print(f"📄 PDF saved to: {output_pdf_path}")
        print(f"📊 File size: {len(pdf_data):,} bytes")
        
    except Exception as e:
        print(f"❌ Error decoding/writing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Default paths
    default_input = "data/process_report_response_output.json"
    default_output = "output.pdf"
    
    # Parse command line arguments
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output
    
    # Check if input file exists
    if not Path(input_path).exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Extract and save PDF
    extract_pdf(input_path, output_path)