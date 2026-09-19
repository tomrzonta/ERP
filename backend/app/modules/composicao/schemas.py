"""Formatos de entrada e saída da API de composição."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ComponenteEntrada(BaseModel):
    componente_id: uuid.UUID
    quantidade: Decimal = Field(gt=0)
    perda_percentual: Decimal = Field(default=Decimal("0"), ge=0, lt=100)


class ComponenteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    componente_id: uuid.UUID
    quantidade: Decimal
    perda_percentual: Decimal


class MontagemEntrada(BaseModel):
    id: uuid.UUID | None = None
    quantidade: Decimal = Field(gt=0)
    ocorrido_em: datetime | None = None
    origem: str | None = Field(default=None, max_length=60)
