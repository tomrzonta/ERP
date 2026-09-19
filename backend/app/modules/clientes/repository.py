"""Consultas do módulo de clientes."""

from sqlalchemy import Select, or_

from app.modules.clientes.models import Cliente
from app.shared.repository import RepositorioDaEmpresa


class ClienteRepositorio(RepositorioDaEmpresa[Cliente]):
    modelo = Cliente
    mensagem_nao_encontrado = "Cliente não encontrado."

    def buscar(
        self,
        *,
        termo: str | None = None,
        limite: int = 50,
        deslocamento: int = 0,
    ) -> list[Cliente]:
        # Cadastro mesclado em outro não aparece mais na listagem — as
        # vendas dele já foram reatribuídas ao sobrevivente.
        consulta: Select[tuple[Cliente]] = self.selecionar().where(
            Cliente.mesclado_com_id.is_(None)
        )
        if termo:
            like = f"%{termo.strip()}%"
            consulta = consulta.where(
                or_(Cliente.nome.ilike(like), Cliente.telefone.ilike(like), Cliente.email.ilike(like))
            )
        consulta = consulta.order_by(Cliente.nome).limit(limite).offset(deslocamento)
        return list(self.db.scalars(consulta))
