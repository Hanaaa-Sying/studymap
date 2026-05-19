import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_text_from_outline(outline_path: str) -> str:
    with open(outline_path, "r", encoding="utf-8") as f:
        return f.read()
