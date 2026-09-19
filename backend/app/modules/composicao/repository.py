"""Consultas do módulo de composição."""

import uuid

from app.modules.composicao.models import ComponenteComposto
from app.shared.repository import RepositorioDaEmpresa


class ComponenteRepositorio(RepositorioDaEmpresa[ComponenteComposto]):
    modelo = ComponenteComposto
    mensagem_nao_encontrado = "Componente não encontrado."

    def do_composto(self, produto_composto_id: uuid.UUID) -> list[ComponenteComposto]:
        consulta = self.selecionar().where(
            ComponenteComposto.produto_composto_id == produto_composto_id
        )
        return list(self.db.scalars(consulta))

    def existente(
        self, produto_composto_id: uuid.UUID, componente_id: uuid.UUID
    ) -> ComponenteComposto | None:
        consulta = self.selecionar().where(
            ComponenteComposto.produto_composto_id == produto_composto_id,
            ComponenteComposto.componente_id == componente_id,
        )
        return self.db.scalar(consulta)
