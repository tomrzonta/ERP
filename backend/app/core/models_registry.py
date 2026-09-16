"""Importa os models de todos os módulos.

O Alembic só enxerga tabelas cujos models foram importados.
Ao criar um módulo com models.py, adicione o import aqui.
"""

from app.modules.acesso import models as acesso_models  # noqa: F401
from app.modules.assinaturas import models as assinaturas_models  # noqa: F401
from app.modules.empresas import models as empresas_models  # noqa: F401
from app.modules.usuarios import models as usuarios_models  # noqa: F401
