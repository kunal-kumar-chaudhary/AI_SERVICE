import fitz  # PyMuPDF
from docx import Document
from pathlib import Path

def parse_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_docx(file_path: str) -> str:
    """Extract text from Word document"""
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def parse_file(file_path: str) -> str:
    """Parse PDF or Word file"""
    ext = Path(file_path).suffix.lower()
    
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")