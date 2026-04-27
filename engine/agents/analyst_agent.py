from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from engine.llm.ollama_client import call_llm

def analyst_agent(state):
    embeddings = OllamaEmbeddings(model="mistral")
    db = FAISS.load_local(
    "vector_db",
    embeddings,
    allow_dangerous_deserialization=True
)

    niche = state["user_profile"]["expertise"]

    docs = db.similarity_search(niche, k=5)
    examples = "\n".join([d.page_content for d in docs])

    prompt = f"""
These are high-performing LinkedIn posts:
{examples}

Analyze them and extract:
- Hook patterns
- CTA styles
- Content formats

Return bullet points only.
"""

    patterns = call_llm(prompt)
    state["patterns"] = patterns
    return state
