from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import json

def build_vector_db():
    with open("data/posts.json", encoding="utf-8") as f:
        posts = json.load(f)

    texts = [p["text"] for p in posts]

    embeddings = OllamaEmbeddings(model="mistral")
    db = FAISS.from_texts(texts, embeddings)
    db.save_local("vector_db")
