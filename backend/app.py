import sys
import os
import torch
from dotenv import load_dotenv
import re
from langchain.text_splitter import CharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain_core.documents import Document
# from langchain.embeddings 
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import HuggingFaceEmbeddings
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from flask import Flask, request, jsonify
import warnings
import traceback
import PROMPTS.system_prompt as system_prompt   
import PROMPTS.research_report_prompt as research_report_prompt
from service.context_rating_service import get_context_rating
from service.web_search_service import get_web_context
warnings.filterwarnings('ignore', category=DeprecationWarning)


load_dotenv()

# Validate Groq API key
if not os.getenv("GROQ_API_KEY"):
    print("❌ ERROR: GROQ_API_KEY not found in .env file!")
    print("Please add: GROQ_API_KEY='your_api_key_here' to backend/.env")
    sys.exit(1)

app=Flask(__name__)
text_splitter=CharacterTextSplitter(
    separator='\n',
    chunk_size=1000,
    chunk_overlap=190
)
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embedder = HuggingFaceEmbeddings(model_name=model_name)
groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
groqLlm = ChatGroq(model=groq_model, temperature=0.3)
chains_by_tab = {}
research_chains_by_tab = {}
memories_by_tab = {}
page_context_by_tab = {}
print(f"✅ Groq initialized with model: {groq_model}")



def _get_tab_id(data):
    tab_id = data.get("tabId", "default")
    return str(tab_id)


def _build_answer_urls(current_page_url, web_sources):
    urls = []
    seen = set()

    if current_page_url and str(current_page_url).strip():
        normalized = str(current_page_url).strip()
        urls.append({
            "title": "Current page",
            "url": normalized,
            "source_type": "page_context"
        })
        seen.add(normalized)

    for source in web_sources or []:
        candidate = str(source.get("url", "")).strip()
        if not candidate or candidate in seen:
            continue
        urls.append({
            "title": source.get("title", "Web source"),
            "url": candidate,
            "source_type": "web_fallback"
        })
        seen.add(candidate)

    return {
        "count": len(urls),
        "items": urls
    }

@app.route("/prepareIt",methods=['POST'])
def prepare():
    global chains_by_tab
    global research_chains_by_tab
    global memories_by_tab
    global page_context_by_tab
    data = request.get_json()
    print(data)
    try:
        if not data:
            return jsonify({"error": "Request body must be valid JSON."}), 400

        page_text = data.get("result")
        if page_text is None:
            return jsonify({"error": "Missing 'result' field in request body."}), 400

        if not str(page_text).strip():
            return jsonify({"error": "The 'result' field is empty. No page content was extracted."}), 400

        tab_id = _get_tab_id(data)
        if tab_id in chains_by_tab and tab_id in research_chains_by_tab:
            return jsonify({"msg": "Chain already prepared for this tab."}), 200
        page_context_by_tab[tab_id] = str(page_text)
        docs = [Document(page_content=page_text)]

        
        text_chunks=text_splitter.split_documents(docs)

        vector_store=FAISS.from_documents(text_chunks,embedder)

        memory = memories_by_tab.get(tab_id)
        if memory is None:
            memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )
            memories_by_tab[tab_id] = memory

        chain = ConversationalRetrievalChain.from_llm(
            llm=groqLlm,
            memory=memory,
            retriever=vector_store.as_retriever(),
            combine_docs_chain_kwargs={"prompt": system_prompt.QA_PROMPT}
        )

        research_chain = ConversationalRetrievalChain.from_llm(
            llm=groqLlm,
            memory=memory,
            retriever=vector_store.as_retriever(),
            combine_docs_chain_kwargs={"prompt": research_report_prompt.RESEARCH_REPORT_PROMPT}
        )

        chains_by_tab[tab_id] = chain
        research_chains_by_tab[tab_id] = research_chain
        print(f"successfully prepared the chain for tab {tab_id}")
        
        return jsonify({"msg": "Success"}), 200
    except Exception as e:
        print(f"prepareIt error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
        

@app.route("/askIt", methods=["POST"])
def scrape():
    global chains_by_tab
    global research_chains_by_tab
    global page_context_by_tab
    data = request.get_json()
    print(data)
    try:
        if not data:
            return jsonify({"answer": "Invalid request", "error": "Request body must be valid JSON."}), 400

        tab_id = _get_tab_id(data)
        chain = chains_by_tab.get(tab_id)
        research_chain = research_chains_by_tab.get(tab_id)

        if chain is None or research_chain is None:
            return jsonify({"answer": "Please prepare the page first.", "error": "Chain is not initialized"}), 400

        que = data.get("question", "")
        if not str(que).strip():
            return jsonify({"answer": "Please enter a question.", "error": "Missing or empty 'question' field."}), 400

        response_mode = str(data.get("response_mode", "normal")).strip().lower()
        force_research = response_mode == "research"

        current_page_url = data.get("url", "")

        context_for_rating = page_context_by_tab.get(tab_id, "")
        rating_json = get_context_rating(
            llm=groqLlm,
            question=que,
            context=context_for_rating,
        )

        print(f"Relevance score result: {rating_json}")
        score = rating_json.get("relevance_score")
        score = score if isinstance(score, (int, float)) else 0

        active_chain = research_chain if force_research else chain

        if score > 40 and not force_research:

            result = active_chain.invoke({"question": f"Answer in English:{que}"})
            # print(result)

            answer_text = result.get("answer") or result.get("result") or str(result)
            # Format output: bold **...** and newlines
            ans = re.sub(r"\*\*(.*?)\*\*", r"\n<b>\1</b>", answer_text)
            ans = ans.replace("\\n", "\n")
            ans = ans.replace(r"\*", "/")

            # print(ans)
            return jsonify({
                "answer": ans,
                "context_rating": rating_json,
                "used_web_fallback": False,
                "web_sources": [],
                "answer_urls": _build_answer_urls(current_page_url, []),
                "response_mode": response_mode
            })
        else:
            web_result = get_web_context(question=que)
            snippets_text = web_result.get("snippets_text", "")

            if snippets_text:
                fallback_question = (
                    f"User Question: {que}\n\n"
                    "Additional web context (user-provided references):\n"
                    f"{snippets_text}\n\n"
                    "Use these web references because page-context relevance is low. "
                    "Be explicit about where web context informed the answer."
                )
            else:
                fallback_question = (
                    f"Question: {que}\n\n"
                    "Page-context relevance is low and no web fallback context was available. "
                    "If context is insufficient, say what is missing."
                )

            fallback_result = active_chain.invoke({"question": fallback_question})
            web_answer = fallback_result.get("answer") or fallback_result.get("result") or str(fallback_result)

            web_answer = re.sub(r"\*\*(.*?)\*\*", r"\n<b>\1</b>", web_answer)
            web_answer = web_answer.replace("\\n", "\n")
            web_answer = web_answer.replace(r"\*", "/")

            return jsonify({
                "answer": web_answer,
                "context_rating": rating_json,
                "used_web_fallback": web_result.get("used_web_fallback", False),
                "web_sources": web_result.get("sources", []),
                "fallback_reason": web_result.get("reason", "low_context_relevance"),
                "answer_urls": _build_answer_urls(current_page_url, web_result.get("sources", [])),
                "response_mode": response_mode
            })
                
    except Exception as e:
        error_text = str(e)
        print(f"askIt error: {error_text}")
        print(traceback.format_exc())
        if "model_decommissioned" in error_text:
            return jsonify({
                "answer": "The configured Groq model is no longer supported. Update GROQ_MODEL in backend/.env.",
                "error": error_text
            }), 500

        return jsonify({"answer": "Not able to extract data from the page", "error": error_text}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)