"""Importa os models de todos os módulos.

O Alembic só enxerga tabelas cujos models foram importados.
Ao criar um módulo com models.py, adicione o import aqui.
"""

from app.modules.acesso import models as acesso_models  # noqa: F401
from app.modules.assinaturas import models as assinaturas_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.clientes import models as clientes_models  # noqa: F401
from app.modules.composicao import models as composicao_models  # noqa: F401
from app.modules.empresas import models as empresas_models  # noqa: F401
from app.modules.estoque import models as estoque_models  # noqa: F401
from app.modules.financeiro import models as financeiro_models  # noqa: F401
from app.modules.produtos import models as produtos_models  # noqa: F401
from app.modules.usuarios import models as usuarios_models  # noqa: F401
from app.modules.vendas import models as vendas_models  # noqa: F401
