import os
import tiktoken
from dotenv import load_dotenv

load_dotenv()


DEFAULT_SETTINGS = {
    "provider": "gpt4free",
    "mode": "prompt",
    "prompt_category": "Default",
    "prompt_name": "Chat",
    "embeddings_provider": "default",
    "tts_provider": "None",
    "transcription_provider": "default",
    "translation_provider": "default",
    "image_provider": "None",
    "vision_provider": "None",
    "AI_MODEL": "mixtral-8x7b",
    "AI_TEMPERATURE": "0.7",
    "AI_TOP_P": "1",
    "MAX_TOKENS": "4096",
    "helper_agent_name": "gpt4free",
    "websearch": False,
    "websearch_depth": 3,
    "WEBSEARCH_TIMEOUT": 0,
    "WAIT_BETWEEN_REQUESTS": 1,
    "WAIT_AFTER_FAILURE": 3,
    "WORKING_DIRECTORY": "./WORKSPACE",
    "WORKING_DIRECTORY_RESTRICTED": True,
    "persona": "",
}


def getenv(var_name: str):
    default_values = {
        "AGIXT_URI": "http://localhost:7437",
        "AGIXT_API_KEY": None,
        "ALLOWED_DOMAINS": "*",
        "ALLOWLIST": "*",
        "WORKSPACE": os.path.join(os.getcwd(), "WORKSPACE"),
        "APP_NAME": "AGiXT",
        "EMAIL_SERVER": "",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "%(asctime)s | %(levelname)s | %(message)s",
        "UVICORN_WORKERS": 10,
        "DATABASE_NAME": "postgres",
        "DATABASE_USER": "postgres",
        "DATABASE_PASSWORD": "postgres",
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "DEFAULT_USER": "user",
        "USING_JWT": "false",
        "CHROMA_PORT": "8000",
        "CHROMA_SSL": "false",
        "DISABLED_EXTENSIONS": "",
        "DISABLED_PROVIDERS": "",
        "AUTH_PROVIDER": "",
    }
    default_value = default_values[var_name] if var_name in default_values else ""
    return os.getenv(var_name, default_value)


def get_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(text))
    return num_tokens


DEFAULT_USER = str(getenv("DEFAULT_USER")).lower()
