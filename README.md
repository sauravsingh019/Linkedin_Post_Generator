# LinkedIn Weekly Post Generator

A cleaner Streamlit app for generating a weekly LinkedIn posting plan with Ollama.

## What changed

- simplified the architecture so the app is easier to run and maintain
- removed the brittle LangGraph and FAISS dependency chain
- improved the UI for strategy input, weekly planning, and downloads
- added Ollama model detection and clearer connection errors
- kept the original goal: weekly LinkedIn posts with tone, emojis, hashtags, CTA, and optional engagement questions

## Project structure

```text
linkedin_post_generator/
|- app.py
|- requirements.txt
|- README.md
|- config/
|  |- settings.py
|- data/
|  |- posts.json
`- engine/
   |- llm/
   |  `- ollama_client.py
   |- prompts/
   |  `- creator_prompt.py
   |- services/
   |  `- post_generator.py
   `- utils/
      `- helpers.py
```

## Run locally

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model:

```bash
ollama pull mistral
```

3. Install Python packages:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run app.py
```

## Notes

- Ollama must be running on `http://localhost:11434`
- the app uses `data/posts.json` as lightweight inspiration for writing style
- generated plans can be downloaded as Markdown or JSON
