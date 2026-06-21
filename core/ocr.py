"""
OCR Pipeline — core/ocr.py
============================
What this does:
  - Takes a PDF uploaded by the user
  - Converts each page into an image using PyMuPDF
  - Sends each image to Gemini Vision (gemini-2.5-flash)
  - Gemini reads the image like a human would and returns all the text
  - We stitch all pages together into one clean text block

Why Gemini Vision for OCR?
  Traditional OCR (Tesseract) struggles with tables, rotated text, and
  messy invoice layouts. Gemini Vision understands context — it knows
  "Unit Price" is a column header and reads the table correctly.
"""

import fitz  # PyMuPDF — opens PDFs and converts pages to images
from google import genai
import tempfile
import os


def extract_text_from_pdf(pdf_path: str, api_key: str) -> str:
    """
    Main function — takes a PDF file path, returns extracted text as string.
    
    Args:
        pdf_path: path to the uploaded PDF file
        api_key: your Gemini API key
    
    Returns:
        Full extracted text from all pages combined
    """
    client = genai.Client(api_key=api_key)
    
    # Open the PDF with PyMuPDF
    doc = fitz.open(pdf_path)
    
    all_text = []
    
    print(f"Processing PDF: {len(doc)} pages found")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Convert PDF page → image (300 DPI for good quality)
        # Matrix(3, 3) means 3x zoom = ~216 DPI, good balance of quality vs speed
        mat = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=mat)
        
        # Save the page image to a temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            pix.save(tmp_path)
        
        try:
            uploaded_file = client.files.upload(file=tmp_path, config={"mime_type": "image/png"})
            prompt = """Extract ALL text from this document page exactly as it appears.
            
Rules:
- Preserve table structure using | separators
- Keep all numbers, dates, and codes exactly as shown
- If you see a header, mark it with [HEADER: header text]
- If you see a table, mark it with [TABLE START] and [TABLE END]
- Include everything — don't skip any text
- For each line item in a table, put it on its own line

Output only the extracted text, nothing else."""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[uploaded_file, prompt]
            )
            
            page_text = response.text
            all_text.append(f"\n--- PAGE {page_num + 1} ---\n{page_text}")
            
            print(f"  ✓ Page {page_num + 1} extracted ({len(page_text)} chars)")
            
        finally:
            # Always clean up temp files
            os.unlink(tmp_path)
    
    doc.close()
    
    full_text = "\n".join(all_text)
    print(f"\n✓ OCR complete — {len(full_text)} total characters extracted")
    
    return full_text


def extract_text_from_image(image_path: str, api_key: str) -> str:
    """
    Same as above but for a single image file (JPG, PNG).
    Useful when user uploads a photo of a document.
    """
    client = genai.Client(api_key=api_key)
    uploaded_file = client.files.upload(file=image_path)
    prompt = """Extract ALL text from this document image exactly as it appears.
Preserve tables, headers, and structure. Output only the extracted text."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded_file, prompt]
    )
    return response.text