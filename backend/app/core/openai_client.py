import os
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """
    Returns a configured OpenAI client.

    This should be the ONLY place where the OpenAI client is constructed.
    All jobs and services should import and use this function.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    return OpenAI(api_key=api_key)
