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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceEmbeddings
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from flask import Flask, request, jsonify


os.environ["GOOGLE_API_KEY"] = "AIzaSyDKfRPxBog_QbF6PfFV01X5yUc_M-w2sSE"
app=Flask(__name__)
text_splitter=CharacterTextSplitter(
    separator='\n',
    chunk_size=1000,
    chunk_overlap=190
)
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embedder = HuggingFaceEmbeddings(model_name=model_name)
geminiLlm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
chain=None



@app.route("/prepareIt",methods=['POST'])
def prepare():
    global chain
    data = request.get_json()
    print(data)
    try:
        docs = [Document(page_content=data["result"])]

        
        text_chunks=text_splitter.split_documents(docs)

        vector_store=FAISS.from_documents(text_chunks,embedder)
        
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        
        chain=ConversationalRetrievalChain.from_llm(llm=geminiLlm,memory=memory,retriever=vector_store.as_retriever())
        
        return jsonify({"msg": "Success"}), 200
    except Exception as e:
        return jsonify({"error":str(e)}),400
        

@app.route("/askIt", methods=["POST"])
def scrape():
    global chain
    data = request.get_json()
    print(data)
    try:
        que=data["question"]
        result=chain({"question":f"Answer in English:{que}"},return_only_outputs=True)
        print(result)
        # Format output: bold **...** and newlines
        ans = re.sub(r"\*\*(.*?)\*\*", r"\n<b>\1</b>", result['answer'])
        ans = ans.replace("\\n", "\n")
        ans=ans.replace("\*","/")

        print(ans)
        return jsonify({"answer": ans}) 
    except Exception:
        return jsonify({"answer":"Not able to extract data from the page"})


if __name__ == "__main__":
    app.run(port=5000)