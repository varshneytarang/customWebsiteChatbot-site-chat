from .text_cleaners import _clip_text

MAX_ADDITIONAL_CONTEXT_CHARS = 3500

def _invoke_with_uploaded_context(question, uploaded_context, uploaded_name, page_context, groqLlm):
    safe_question = str(question or "").strip()
    safe_uploaded = _clip_text(uploaded_context, MAX_ADDITIONAL_CONTEXT_CHARS)
    safe_uploaded_name = str(uploaded_name or "uploaded file").strip()
    safe_page_context = _clip_text(page_context or "", 4500)

    prompt = (
        "You are a precise assistant.\n"
        f"User question:\n{safe_question}\n\n"
        f"Uploaded context ({safe_uploaded_name}):\n{safe_uploaded}\n\n"
        f"Current page context:\n{safe_page_context or 'No page context available.'}\n\n"
        "Rules:\n"
        "1) If the question asks about the uploaded file/PDF/document, prioritize Uploaded context.\n"
        "2) If uploaded context is irrelevant, say that briefly and use Current page context.\n"
        "3) Be explicit in the answer about which context you used.\n"
        "4) Answer in English.\n"
    )

    llm_response = groqLlm.invoke(prompt)
    return getattr(llm_response, "content", str(llm_response))