from engine.llm.ollama_client import call_ollama
from engine.prompt_builder import build_prompt

def generate_post(user_input: dict):
    prompt = build_prompt(user_input)
    return call_ollama(prompt)
