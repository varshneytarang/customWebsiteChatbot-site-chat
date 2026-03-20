import sys
import json
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
warnings.filterwarnings('ignore', category=DeprecationWarning)


load_dotenv()
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
chain=None



@app.route("/prepareIt",methods=['POST'])
def prepare():
    global chain
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

        docs = [Document(page_content=page_text)]

        
        text_chunks=text_splitter.split_documents(docs)

        vector_store=FAISS.from_documents(text_chunks,embedder)
        
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=groqLlm,
            memory=memory,
            retriever=vector_store.as_retriever()
        )
        print("successfully prepared the chain")
        
        return jsonify({"msg": "Success"}), 200
    except Exception as e:
        print(f"prepareIt error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
        

@app.route("/askIt", methods=["POST"])
def scrape():
    global chain
    data = request.get_json()
    print(data)
    try:
        if not data:
            return jsonify({"answer": "Invalid request", "error": "Request body must be valid JSON."}), 400

        if chain is None:
            return jsonify({"answer": "Please prepare the page first.", "error": "Chain is not initialized"}), 400

        que = data.get("question", "")
        if not str(que).strip():
            return jsonify({"answer": "Please enter a question.", "error": "Missing or empty 'question' field."}), 400

        result = chain.invoke({"question": f"Answer in English:{que}"})
        print(result)

        answer_text = result.get("answer") or result.get("result") or str(result)
        # Format output: bold **...** and newlines
        ans = re.sub(r"\*\*(.*?)\*\*", r"\n<b>\1</b>", answer_text)
        ans = ans.replace("\\n", "\n")
        ans=ans.replace("\*","/")

        print(ans)
        return jsonify({"answer": ans}) 
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
    app.run(port=5000)