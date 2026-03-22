import base64
import io
from .helpers.text_cleaners import _clip_text, _sanitize_extracted_text, _looks_like_gibberish
from .helpers.extract_text_with_ocr import _extract_pdf_text_with_ocr
import importlib

MAX_ADDITIONAL_CONTEXT_CHARS = 3500
MAX_BASE64_LENGTH = 6_000_000

PdfReader = None
DocxDocument = None
PdfiumDocument = None
RapidOCR = None
ocr_engine = None

try:
    pypdf_module = importlib.import_module("pypdf")
    PdfReader = getattr(pypdf_module, "PdfReader", None)
except Exception:
    PdfReader = None

try:
    docx_module = importlib.import_module("docx")
    DocxDocument = getattr(docx_module, "Document", None)
except Exception:
    DocxDocument = None

try:
    pdfium_module = importlib.import_module("pypdfium2")
    PdfiumDocument = getattr(pdfium_module, "PdfDocument", None)
except Exception:
    PdfiumDocument = None

try:
    rapidocr_module = importlib.import_module("rapidocr_onnxruntime")
    RapidOCR = getattr(rapidocr_module, "RapidOCR", None)
except Exception:
    RapidOCR = None


def extract_additional_context(data):
    payload = data.get("additional_context_payload")

    if isinstance(payload, dict):
        context_type = str(payload.get("type", "text")).strip().lower()
        context_name = str(payload.get("name", "")).strip()

        if context_type == "text":
            text_value = _clip_text(str(payload.get("text", "") or ""), MAX_ADDITIONAL_CONTEXT_CHARS)
            return text_value, context_name, "ok"

        if context_type in {"pdf", "docx"}:
            b64 = str(payload.get("base64", "") or "").strip()
            if not b64:
                return "", context_name, f"{context_type}_empty"
            if len(b64) > MAX_BASE64_LENGTH:
                return "", context_name, f"{context_type}_too_large"

            try:
                file_bytes = base64.b64decode(b64)
            except Exception:
                return "", context_name, f"{context_type}_invalid_base64"

            if context_type == "pdf":
                if PdfReader is None:
                    return "", context_name, "pdf_dependency_missing"

                try:
                    reader = PdfReader(io.BytesIO(file_bytes))
                    page_texts = []
                    for page in reader.pages[:30]:
                        extracted = (page.extract_text() or "").strip()
                        if extracted:
                            page_texts.append(extracted)
                    text_value = _sanitize_extracted_text("\n".join(page_texts))
                    if not text_value:
                        ocr_text, ocr_status = _extract_pdf_text_with_ocr(file_bytes,RapidOCR,PdfiumDocument)
                        if ocr_text:
                            return ocr_text, context_name, ocr_status
                        return "", context_name, ocr_status
                    if _looks_like_gibberish(text_value):
                        ocr_text, ocr_status = _extract_pdf_text_with_ocr(file_bytes,RapidOCR,PdfiumDocument)
                        if ocr_text:
                            return ocr_text, context_name, ocr_status
                        return "", context_name, ocr_status
                    return _clip_text(text_value, MAX_ADDITIONAL_CONTEXT_CHARS), context_name, "ok"
                except Exception:
                    return "", context_name, "pdf_parse_error"

            if context_type == "docx":
                if DocxDocument is None:
                    return "", context_name, "docx_dependency_missing"

                try:
                    document = DocxDocument(io.BytesIO(file_bytes))
                    paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
                    text_value = _sanitize_extracted_text("\n".join(paragraphs))
                    if not text_value:
                        return "", context_name, "docx_no_text"
                    if _looks_like_gibberish(text_value):
                        return "", context_name, "docx_text_unusable"
                    return _clip_text(text_value, MAX_ADDITIONAL_CONTEXT_CHARS), context_name, "ok"
                except Exception:
                    return "", context_name, "docx_parse_error"

    fallback_text = _clip_text(str(data.get("additional_context", "") or ""), MAX_ADDITIONAL_CONTEXT_CHARS)
    fallback_name = str(data.get("additional_context_name", "") or "").strip()
    return fallback_text, fallback_name, "ok" if fallback_text else "none"