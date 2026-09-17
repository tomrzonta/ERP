"""Repositório base das tabelas de empresa (multi-tenant).

Toda consulta a uma tabela com `empresa_id` passa por aqui. O filtro da
empresa é aplicado pela classe, não pelo módulo: ninguém precisa lembrar.

Uso:

    class ProdutoRepositorio(RepositorioDaEmpresa[Produto]):
        modelo = Produto
        mensagem_nao_encontrado = "Produto não encontrado."

    repo = ProdutoRepositorio(db, contexto.empresa_id)
    produto = repo.obter_ou_erro(produto_id)

Regras:
- A `empresa_id` vem do contexto da sessão, nunca do corpo da requisição.
- Registro de outra empresa se comporta como inexistente (404), para não
  revelar nem a existência dele.
- Não existe exclusão: registros referenciados por histórico são desativados.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NaoEncontrado
from app.shared.models import Base

ModeloT = TypeVar("ModeloT", bound=Base)


class RepositorioDaEmpresa(Generic[ModeloT]):
    #: Model da tabela, que precisa usar o EmpresaMixin
    modelo: type[ModeloT]
    #: Mensagem de "não encontrado" da entidade (sobrescreva na subclasse)
    mensagem_nao_encontrado: str = "Registro não encontrado."

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        modelo = getattr(cls, "modelo", None)
        if modelo is None:
            raise TypeError(f"{cls.__name__} precisa definir 'modelo'.")
        if not hasattr(modelo, "empresa_id"):
            raise TypeError(
                f"{modelo.__name__} não tem 'empresa_id'. Use um model com EmpresaMixin "
                f"ou consulte a tabela direto no repositório do módulo."
            )

    def __init__(self, db: Session, empresa_id: uuid.UUID) -> None:
        self.db = db
        self.empresa_id = empresa_id

    # --- consultas ---

    def selecionar(self) -> Select[tuple[ModeloT]]:
        """Consulta já restrita à empresa. Base para filtros do módulo."""
        return select(self.modelo).where(self.modelo.empresa_id == self.empresa_id)

    def obter(self, registro_id: uuid.UUID) -> ModeloT | None:
        return self.db.scalar(self.selecionar().where(self.modelo.id == registro_id))

    def obter_ou_erro(self, registro_id: uuid.UUID) -> ModeloT:
        registro = self.obter(registro_id)
        if registro is None:
            raise NaoEncontrado(self.mensagem_nao_encontrado)
        return registro

    def listar(self, *, limite: int = 50, deslocamento: int = 0) -> list[ModeloT]:
        consulta = self.selecionar().limit(limite).offset(deslocamento)
        return list(self.db.scalars(consulta))

    def contar(self) -> int:
        consulta = (
            select(func.count())
            .select_from(self.modelo)
            .where(self.modelo.empresa_id == self.empresa_id)
        )
        return self.db.scalar(consulta) or 0

    # --- escrita ---

    def adicionar(self, registro: ModeloT) -> ModeloT:
        """Grava o registro na empresa do repositório.

        Se o registro vier com outra empresa, é erro de programação: melhor
        estourar do que gravar dado no lugar errado.
        """
        atual = getattr(registro, "empresa_id", None)
        if atual is not None and atual != self.empresa_id:
            raise RuntimeError(
                f"Tentativa de gravar {type(registro).__name__} da empresa {atual} "
                f"pelo repositório da empresa {self.empresa_id}."
            )
        registro.empresa_id = self.empresa_id  # type: ignore[attr-defined]
        self.db.add(registro)
        self.db.flush()
        return registro
