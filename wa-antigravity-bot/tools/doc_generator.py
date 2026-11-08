"""Document Generator Tool for WhatsApp Antigravity Bot.

Provides capabilities to generate formatted Word (.docx), PDF (.pdf), and Plain Text (.txt)
documents stored in the storage directory.
"""

import os
import re
from datetime import datetime
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# Base storage directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize filename to avoid invalid characters."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    return clean.replace(" ", "_") if clean else "dokumen"


def create_word_document(title: str, content: str, filename: Optional[str] = None) -> str:
    """
    Creates a professional Word document (.docx) using python-docx.
    Formats title, headings, bullet points, and paragraphs cleanly.
    
    Args:
        title: Title of the document
        content: Main text content (supports Markdown-like syntax: ## headings, - bullets, * bullets)
        filename: Optional custom filename (e.g., 'ringkasan_apbn.docx')
        
    Returns:
        Relative or clean path to the generated file in storage/
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(title)[:30]
        filename = f"{safe_title}_{timestamp}.docx"
    elif not filename.endswith(".docx"):
        filename = f"{filename}.docx"

    file_path = os.path.join(STORAGE_DIR, filename)

    doc = Document()

    # Configure Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Add Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.text = f"Dokumen Resmi • Dibuat oleh Antigravity Bot"
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.style.font.size = Pt(8.5)
        hp.style.font.italic = True
        hp.style.font.color.rgb = RGBColor(128, 128, 128)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.text = f"Tanggal Pembuatan: {datetime.now().strftime('%d %B %Y %H:%M WIB')} | WhatsApp Integration"
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.style.font.size = Pt(8.5)
        fp.style.font.color.rgb = RGBColor(128, 128, 128)

    # Document Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(12)
    title_p.paragraph_format.space_after = Pt(18)
    run_title = title_p.add_run(title)
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(26, 54, 93)  # Deep Navy Blue

    # Parse and structure content lines
    lines = content.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # Empty line adds subtle spacing
            p_spacer = doc.add_paragraph()
            p_spacer.paragraph_format.space_after = Pt(4)
            continue

        # Level 1 Heading (# ...)
        if line.startswith("# "):
            h_text = line[2:].strip()
            hp = doc.add_paragraph()
            hp.paragraph_format.space_before = Pt(14)
            hp.paragraph_format.space_after = Pt(6)
            run = hp.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 58, 138)

        # Level 2 Heading (## ...)
        elif line.startswith("## "):
            h_text = line[3:].strip()
            hp = doc.add_paragraph()
            hp.paragraph_format.space_before = Pt(12)
            hp.paragraph_format.space_after = Pt(4)
            run = hp.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(49, 46, 129)

        # Level 3 Heading (### ...)
        elif line.startswith("### "):
            h_text = line[4:].strip()
            hp = doc.add_paragraph()
            hp.paragraph_format.space_before = Pt(10)
            hp.paragraph_format.space_after = Pt(2)
            run = hp.add_run(h_text)
            run.font.name = "Calibri"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(55, 65, 81)

        # Bullet List (- or * or •)
        elif line.startswith(("- ", "* ", "• ")):
            bullet_text = line[2:].strip()
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.space_after = Pt(3)
            bp.paragraph_format.line_spacing = 1.15
            _format_rich_text(bp, bullet_text)

        # Numbered List (1. or 2. etc.)
        elif re.match(r"^\d+\.\s+", line):
            num_text = re.sub(r"^\d+\.\s+", "", line)
            np = doc.add_paragraph(style="List Number")
            np.paragraph_format.space_after = Pt(3)
            np.paragraph_format.line_spacing = 1.15
            _format_rich_text(np, num_text)

        # Standard Paragraph
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            _format_rich_text(p, line)

    doc.save(file_path)
    return file_path


def _format_rich_text(paragraph, text: str):
    """Parses basic Markdown **bold** and *italic* formatting inside a paragraph."""
    # Split by bold markers
    tokens = re.split(r"(\*\*.*?\*\*)", text)
    for token in tokens:
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            run.font.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(31, 41, 55)
        else:
            # Check for italics inside
            sub_tokens = re.split(r"(\*.*?\*)", token)
            for sub in sub_tokens:
                if sub.startswith("*") and sub.endswith("*") and len(sub) > 2:
                    run = paragraph.add_run(sub[1:-1])
                    run.font.italic = True
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
                    run.font.color.rgb = RGBColor(55, 65, 81)
                else:
                    run = paragraph.add_run(sub)
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
                    run.font.color.rgb = RGBColor(31, 41, 55)


def create_txt_document(title: str, content: str, filename: Optional[str] = None) -> str:
    """Creates a clean formatted .txt document in storage/."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(title)[:30]
        filename = f"{safe_title}_{timestamp}.txt"
    elif not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    file_path = os.path.join(STORAGE_DIR, filename)

    divider = "=" * 60
    header = f"{divider}\n{title.upper().center(60)}\n{divider}\n"
    footer = f"\n{divider}\nDibuat pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Antigravity Bot\n{divider}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + "\n" + content + "\n" + footer)

    return file_path


def create_pdf_document(title: str, content: str, filename: Optional[str] = None) -> str:
    """
    Creates a clean PDF document using fpdf2.
    Fallback to .txt if fpdf2 is unavailable or encounters encoding issues.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(title)[:30]
        filename = f"{safe_title}_{timestamp}.pdf"
    elif not filename.endswith(".pdf"):
        filename = f"{filename}.pdf"

    file_path = os.path.join(STORAGE_DIR, filename)

    try:
        from fpdf import FPDF

        class PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, "Dokumen Resmi - Dibuat oleh WhatsApp Antigravity Bot", 0, 1, "R")
                self.ln(2)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f"Halaman {self.page_no()}", 0, 0, "C")

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        epw = pdf.epw

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(26, 54, 93)
        pdf.multi_cell(epw, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Body
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)

        for line in content.splitlines():
            line_str = line.strip()
            if not line_str:
                pdf.ln(4)
                continue

            # Heading 1
            if line_str.startswith("# "):
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(30, 58, 138)
                pdf.multi_cell(epw, 8, line_str[2:].strip(), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
            # Heading 2
            elif line_str.startswith("## "):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(49, 46, 129)
                pdf.multi_cell(epw, 7, line_str[3:].strip(), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
            # Bullets
            elif line_str.startswith(("- ", "* ", "• ")):
                bullet_text = line_str[2:].replace("**", "").replace("*", "")
                pdf.multi_cell(epw, 6, f"  -  {bullet_text}", new_x="LMARGIN", new_y="NEXT")
            else:
                clean_text = line_str.replace("**", "").replace("*", "")
                pdf.multi_cell(epw, 6, clean_text, new_x="LMARGIN", new_y="NEXT")

        pdf.output(file_path)
        return file_path
    except Exception as e:
        print(f"[PDF Generation Error] {e}")
        # Fallback to TXT if PDF generation encounters issues
        txt_path = create_txt_document(title, content, filename.replace(".pdf", ".txt"))
        return txt_path
