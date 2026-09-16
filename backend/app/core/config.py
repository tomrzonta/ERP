"""Configurações da aplicação, lidas das variáveis de ambiente (.env)."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ERP"
    environment: Literal["local", "staging", "production"] = "local"
    database_url: str
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("database_url")
    @classmethod
    def validar_database_url(cls, valor: str) -> str:
        """Aceita a URL como o provedor entrega, força o driver psycopg 3
        e recusa marcadores esquecidos, como colchetes em volta da senha."""
        valor = valor.strip()

        credenciais = valor.split("://", 1)[-1].rpartition("@")[0]
        if "[" in credenciais or "]" in credenciais:
            raise ValueError(
                "DATABASE_URL com colchetes na senha. Remova os colchetes do "
                "marcador, deixando apenas usuario:senha@host."
            )

        for prefixo in ("postgresql://", "postgres://"):
            if valor.startswith(prefixo):
                return "postgresql+psycopg://" + valor[len(prefixo) :]
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
