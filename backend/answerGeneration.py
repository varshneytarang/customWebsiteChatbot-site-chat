import sys
import json
import os
import torch
from dotenv import load_dotenv
import textwrap
from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
# from langchain.embeddings 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.embeddings import HuggingFaceEmbeddings
import nltk

from scrapeTheLink import crawl

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

@app.route("/askIt", methods=["POST"])
def scrape():
    data = request.get_json()
    print(data)
    urls = data["url"]
    data1=crawl(urls,0)
    print(data1)
    docs=[Document(page_content=item["text"],metadata={'source':item["url"]}) for item in data1]

    text_chunks=text_splitter.split_documents(docs)

    vector_store=FAISS.from_documents(text_chunks,embedder)
    
    chain=RetrievalQAWithSourcesChain.from_llm(llm=geminiLlm,retriever=vector_store.as_retriever())
    que=data["question"]
    result=chain({"question":que},return_only_outputs=True)
    
    print(result)
    return jsonify({"answer": result['answer']}) 


if __name__ == "__main__":
    app.run(port=5000)