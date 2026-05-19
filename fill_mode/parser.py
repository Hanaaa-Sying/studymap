import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_first_pages(pdf_path: str, n: int = 25) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:n]
        return "\n".join(page.extract_text() or "" for page in pages)


def extract_text_from_outline(outline_path: str) -> str:
    with open(outline_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 6000, overlap: int = 500) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
