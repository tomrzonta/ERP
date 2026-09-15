"""Erros de negócio padronizados.

Services lançam essas exceções; o handler converte em resposta HTTP.
Assim, o service não precisa saber nada de HTTP.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 400
    code: str = "erro"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NaoEncontrado(AppError):
    status_code = 404
    code = "nao_encontrado"


class PermissaoNegada(AppError):
    status_code = 403
    code = "permissao_negada"


class RecursoDoPlano(AppError):
    """Recurso não incluso no plano atual (ex.: custos adicionais no Base)."""

    status_code = 402
    code = "recurso_do_plano"


class LimiteDoPlano(AppError):
    """Limite do plano atingido (ex.: 6º produto composto no Base)."""

    status_code = 402
    code = "limite_do_plano"


class RegraDeNegocio(AppError):
    status_code = 422
    code = "regra_de_negocio"


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"erro": exc.code, "mensagem": exc.message},
        )
