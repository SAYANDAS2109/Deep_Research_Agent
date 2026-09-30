import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


load_dotenv()


def get_llm():

    provider = os.getenv(
        "LLM_PROVIDER",
        "ollama"
    ).lower()

    if provider == "ollama":

        model = os.getenv(
            "OLLAMA_MODEL",
            "qwen3:4b"
        )

        return ChatOllama(
            model=model,
            temperature=0,
            
            
            
        )

    elif provider == "openai":

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6"
        )

        return ChatOpenAI(
            model=model,
            temperature=0,
            
            
        )

    else:

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )