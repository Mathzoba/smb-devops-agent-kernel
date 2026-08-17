# kernel/config.py
import os
from dotenv import load_dotenv

load_dotenv()


def _obrigatorio(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(
            f"Variavel de ambiente obrigatoria ausente: {nome}. "
            f"Confira seu arquivo .env (veja .env.example como referencia)."
        )
    return valor


class Settings:
    PG_HOST = os.environ.get("PG_HOST", "localhost")
    PG_PORT = int(os.environ.get("PG_PORT", "5432"))
    PG_USER = os.environ.get("PG_USER", "demo")
    PG_DATABASE = os.environ.get("PG_DATABASE", "smb_demo")
    PG_PASSWORD = _obrigatorio("PG_PASSWORD")
    GROQ_API_KEY = _obrigatorio("GROQ_API_KEY")


settings = Settings()