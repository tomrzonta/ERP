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
        e recusa erros comuns de montagem da URL."""
        valor = valor.strip()

        credenciais = valor.split("://", 1)[-1].rpartition("@")[0]
        if "[" in credenciais or "]" in credenciais:
            raise ValueError(
                "DATABASE_URL com colchetes na senha. Remova os colchetes do "
                "marcador, deixando apenas usuario:senha@host."
            )

        if valor.count("@") != 1:
            raise ValueError(
                "DATABASE_URL deve ter exatamente um '@', separando "
                "usuario:senha do host."
            )

        for prefixo in ("postgresql://", "postgres://"):
            if valor.startswith(prefixo):
                return "postgresql+psycopg://" + valor[len(prefixo) :]
        return valor

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
