from .text_cleaners import _clip_text, _sanitize_extracted_text, _looks_like_gibberish
import tempfile
import importlib
import os

MAX_ADDITIONAL_CONTEXT_CHARS = 3500
MAX_BASE64_LENGTH = 6_000_000
ocr_engine = None



def _get_ocr_engine(RapidOCR):
    global ocr_engine
    if ocr_engine is not None:
        return ocr_engine

    if RapidOCR is None:
        return None

    try:
        ocr_engine = RapidOCR()
    except Exception:
        ocr_engine = None
    return ocr_engine

def _extract_pdf_text_with_ocr(file_bytes,RapidOCR,PdfiumDocument):
    if PdfiumDocument is None or RapidOCR is None:
        return "", "pdf_ocr_dependency_missing"

    engine = _get_ocr_engine(RapidOCR)
    if engine is None:
        return "", "pdf_ocr_init_failed"

    try:
        pdf_doc = PdfiumDocument(file_bytes)
    except Exception:
        return "", "pdf_ocr_parse_error"

    ocr_text_lines = []

    try:
        page_count = min(len(pdf_doc), 12)
        for page_index in range(page_count):
            page = pdf_doc[page_index]
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()

            tmp_path = ""
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                pil_image.save(tmp_path, format="PNG")
                result, _ = engine(tmp_path)
            finally:
                try:
                    bitmap.close()
                except Exception:
                    pass
                try:
                    page.close()
                except Exception:
                    pass
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

            if not result:
                continue

            for item in result:
                # rapidocr result item format: [box, text, score]
                text_piece = ""
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text_piece = str(item[1] or "").strip()
                if text_piece:
                    ocr_text_lines.append(text_piece)

        try:
            pdf_doc.close()
        except Exception:
            pass

        ocr_text = _sanitize_extracted_text("\n".join(ocr_text_lines))
        if not ocr_text:
            return "", "pdf_ocr_no_text"
        if _looks_like_gibberish(ocr_text):
            return "", "pdf_ocr_text_unusable"

        return _clip_text(ocr_text, MAX_ADDITIONAL_CONTEXT_CHARS), "pdf_ocr_ok"
    except Exception:
        try:
            pdf_doc.close()
        except Exception:
            pass
        return "", "pdf_ocr_failed"