import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(num_predict=None):

    provider = os.getenv(
        "LLM_PROVIDER",
        "ollama"
    ).lower()


    # ======================================
    # LOCAL OLLAMA
    # ======================================

    if provider == "ollama":

        from langchain_ollama import ChatOllama

        model = os.getenv(
            "OLLAMA_MODEL",
            "qwen3:4b"
        )

        kwargs = {
            "model": model,
            "temperature": 0,
            "reasoning": False
        }

        if num_predict is not None:
            kwargs["num_predict"] = num_predict

        return ChatOllama(
            **kwargs
        )


    # ======================================
    # GROQ
    # ======================================

    elif provider == "groq":

        from langchain_groq import ChatGroq

        model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        kwargs = {
            "model": model,
            "temperature": 0
        }

        if num_predict is not None:
            kwargs["max_tokens"] = num_predict

        return ChatGroq(
            **kwargs
        )


    # ======================================
    # OPENAI
    # ======================================

    elif provider == "openai":

        from langchain_openai import ChatOpenAI

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6"
        )

        kwargs = {
            "model": model,
            "temperature": 0
        }

        if num_predict is not None:
            kwargs["max_tokens"] = num_predict

        return ChatOpenAI(
            **kwargs
        )


    else:

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )
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
