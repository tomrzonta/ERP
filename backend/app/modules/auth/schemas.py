"""Formatos de entrada e saída da API de autenticação."""

import uuid

from pydantic import BaseModel, EmailStr, Field


class CadastroEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    nome_empresa: str = Field(min_length=2, max_length=120)


class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class RenovarEntrada(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class EmpresaAtivaEntrada(BaseModel):
    empresa_id: uuid.UUID


class TokensSaida(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmpresaDisponivelSaida(BaseModel):
    id: uuid.UUID
    nome: str
    papel: str


class LoginSaida(BaseModel):
    tokens: TokensSaida
    empresa_ativa_id: uuid.UUID | None
    empresas: list[EmpresaDisponivelSaida]


class UsuarioSaida(BaseModel):
    id: uuid.UUID
    nome: str
    email: str


class EmpresaSaida(BaseModel):
    id: uuid.UUID
    nome: str
    slug: str


class EuSaida(BaseModel):
    usuario: UsuarioSaida
    empresa: EmpresaSaida
    papel: str
    permissoes: list[str]
    plano: str
