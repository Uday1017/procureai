"""
OCR Pipeline — core/ocr.py
"""

import fitz
from google import genai
from google.genai import types
import os


def extract_text_from_pdf(pdf_path: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    doc = fitz.open(pdf_path)
    all_text = []

    print(f"Processing PDF: {len(doc)} pages found")

    for page_num in range(len(doc)):
        page = doc[page_num]

        # 1.5x zoom instead of 3x — cuts image size by 75%, enough for OCR
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)

        # Send raw bytes directly — no temp file, no disk I/O, less RAM
        img_bytes = pix.tobytes("png")
        del pix  # Free memory immediately after getting bytes

        prompt = """Extract ALL text from this document page exactly as it appears.
Rules:
- Preserve table structure using | separators
- Keep all numbers, dates, and codes exactly as shown
- Mark headers with [HEADER: text]
- Mark tables with [TABLE START] and [TABLE END]
- Output only the extracted text, nothing else."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Lighter than 2.5-flash
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt
            ]
        )

        del img_bytes  # Free memory after sending
        page_text = response.text
        all_text.append(f"\n--- PAGE {page_num + 1} ---\n{page_text}")
        print(f"  ✓ Page {page_num + 1} extracted ({len(page_text)} chars)")

    doc.close()
    full_text = "\n".join(all_text)
    print(f"\n✓ OCR complete — {len(full_text)} total characters extracted")
    return full_text


def extract_text_from_image(image_path: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            "Extract ALL text from this document image exactly as it appears."
        ]
    )
    return response.text