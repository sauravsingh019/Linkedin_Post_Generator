# 🚀 LinkedIn Post Studio (LangGraph + RAG + AI Images)

An enterprise-grade AI system that generates, analyzes, and publishes **high-performing LinkedIn content** using a multi-agent workflow, RAG pipeline, and AI image generation.

---

## 🔥 What This Project Does

This is not a basic post generator.

It simulates a **complete content strategy system**:

* 🧠 Audits your niche
* 📊 Learns from high-performing posts (RAG)
* ✍️ Generates structured weekly content
* 🎨 Creates AI images
* 📅 Schedules & publishes directly to LinkedIn

---

## ⚡ Key Features

### 🧠 Multi-Agent Content Engine (LangGraph)

* Auditor → Validates niche & positioning
* Analyst → Extracts patterns using RAG
* Creator → Generates strategic posts
* Fallback state graph ensures reliability

---

### 📊 RAG-Based Content Intelligence

* Embeddings via Ollama / Gemini
* Cached in `embeddings_cache.json`
* Parallel cosine similarity search
* Ensures non-generic, high-performing outputs

---

### ⚙️ Dual AI Model Support

* **Ollama (Local)** → Offline, private
* **Gemini (Cloud)** → Faster, higher quality

---

### 🎨 AI Image Generation (Imagen 3)

* Prompt → Generate → Auto-attach
* Saved locally for persistence

---

### 📅 LinkedIn Integration

* Profile validation via API
* Schedule posts in calendar
* Publish using LinkedIn UGC API

---

### 🎯 Advanced UX

* LinkedIn-style preview popups
* Persistent media uploads
* Weekly content calendar
* Smooth UI interactions

---

## 🧠 How It Works Internally

### 🔄 System Flow

```id="flow1"
User Input → Auditor → Analyst → Creator → Output → Publish
```

---

### 🧩 Agent Responsibilities

**Auditor Agent**

* Refines niche clarity
* Prevents generic topics

**Analyst Agent (RAG)**

* Loads template posts
* Generates embeddings
* Finds best patterns via similarity

**Creator Agent**

* Combines:

  * User input
  * RAG insights
  * Prompt templates
* Produces final LinkedIn content

---

### ⚡ RAG Pipeline

* Embeddings:

  * Ollama (`/api/embeddings`)
  * Gemini (`text-embedding-004`)
* Stored in:

```id="rag1"
data/embeddings_cache.json
```

* Uses:

  * Parallel processing
  * Cosine similarity ranking

---

### 🤖 AI Execution Layer

* Local → Ollama daemon (auto-start + streaming)
* Cloud → Gemini API

---

### 🎨 Media Pipeline

```id="media1"
Text Prompt → Imagen 3 → Save → Attach to Post
```

---

### 📤 Output Layer

* Preview in UI
* Stored in calendar
* Scheduled / instantly published

---

## 🏗️ Architecture Diagram

```id="arch1"
                ┌──────────────────────────┐
                │       User Input         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │   LangGraph Orchestrator │
                └────────────┬─────────────┘
                             │
        ┌──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Auditor  │   │ Analyst  │   │ Creator  │
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        │              │              │
        │        ┌─────▼─────┐        │
        │        │   RAG     │        │
        │        │ Engine    │        │
        │        └─────┬─────┘        │
        └──────────────┴──────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │   AI Model Layer   │
            │ Ollama / Gemini    │
            └─────────┬──────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Image Generation   │
            │   (Imagen 3)       │
            └─────────┬──────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Preview + Calendar │
            └─────────┬──────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ LinkedIn API Post  │
            └────────────────────┘
```

---

## 📂 Project Structure

```id="struct1"
linkedin_post_generator/
│
├── app.py
├── requirements.txt
├── config/
├── data/
└── engine/
    ├── agents/
    ├── graph/
    ├── llm/
    ├── prompts/
    ├── services/
    └── utils/
```

---

## 🛠️ Setup & Run

### 1. Clone Repo

```bash id="run1"
git clone <your-repo-link>
cd linkedin_post_generator
```

### 2. Install Dependencies

```bash id="run2"
pip install -r requirements.txt
```

### 3. Run App

```bash id="run3"
streamlit run app.py
```

---

## 🔑 Configuration

### AI Models

* Add Gemini API key
* Use Ollama for local execution

---

### LinkedIn API

1. Create app
2. Enable "Share on LinkedIn"
3. Generate token
4. Paste in app

---

## 🎯 Use Cases

* Personal branding automation
* AI system design showcase
* Content strategy tools
* Developer portfolios

---

## 🚀 Future Improvements

* SaaS deployment
* Multi-platform publishing
* Analytics dashboard
* Team collaboration

---

## 💡 Why This Project Stands Out

* Multi-agent architecture
* RAG + real-world data usage
* Full pipeline (AI + UI + API)
* Production-ready system design

---

## 📬 Connect

Open to collaboration in AI, automation, and content systems.
