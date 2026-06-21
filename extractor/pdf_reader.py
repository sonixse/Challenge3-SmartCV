"""Extracció de text de PDFs.

Estratègia en dues fases:
  1. `pypdf` — ràpid i suficient per a PDFs amb capa de text.
  2. Si el resultat és buit o gairebé buit (PDF escanejat / imatge),
     es cau a `docTR` (OCR) com a fallback.
"""

from pathlib import Path

# Llindar mínim de caràcters per considerar que pypdf ha extret text útil.
# Per sota, assumim PDF escanejat i activem OCR.
_MIN_TEXT_CHARS = 50


def _extract_with_pypdf(pdf_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            # Una pàgina corrupta no ha de tombar tota l'extracció.
            continue
    return "\n".join(parts).strip()


def _extract_with_doctr(pdf_path: str) -> str:
    # Import dins la funció: docTR és pesat (torch) i no volem carregar-lo
    # si el PDF ja ha funcionat amb pypdf.
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor

    model = ocr_predictor(pretrained=True)
    doc = DocumentFile.from_pdf(pdf_path)
    result = model(doc)

    lines = []
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                lines.append(" ".join(word.value for word in line.words))
    return "\n".join(lines).strip()


def extract_text(pdf_path: str) -> str:
    """Retorna el text pla del PDF; usa OCR només si cal."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF no trobat: {pdf_path}")

    text = _extract_with_pypdf(str(path))
    if len(text) >= _MIN_TEXT_CHARS:
        return text

    # Fallback OCR per a PDFs escanejats.
    return _extract_with_doctr(str(path))
