import sys
import json
import os
import torch
from dotenv import load_dotenv
import textwrap
from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import CharacterTextSplitter
# from langchain.embeddings 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


os.environ["GOOGLE_API_KEY"] = "AIzaSyDKfRPxBog_QbF6PfFV01X5yUc_M-w2sSE"


data = json.loads(sys.stdin.read())
print(json.dumps({"answer": f"Echo: {data['question']}"}))
