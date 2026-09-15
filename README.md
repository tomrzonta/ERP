# ERP SaaS para Microempreendedores

Veja o planejamento completo em [ROADMAP.md](ROADMAP.md).

## Rodando localmente (Windows + Docker Desktop)

**1. Crie o arquivo de ambiente** (PowerShell, na raiz do projeto):

```powershell
Copy-Item backend\.env.example backend\.env
```

**2. Suba os containers:**

```powershell
docker compose up --build
```

Na primeira vez demora um pouco. Depois, `docker compose up` basta.

**3. Teste no navegador:**

- Health check: http://localhost:8000/api/v1/health
- Documentação da API: http://localhost:8000/docs

## Comandos do dia a dia

Rode em outro terminal, com os containers ligados.

| O que fazer | Comando |
|---|---|
| Rodar os testes | `docker compose exec backend pytest` |
| Verificar o código | `docker compose exec backend ruff check .` |
| Formatar o código | `docker compose exec backend ruff format .` |
| Criar migração | `docker compose exec backend alembic revision --autogenerate -m "descricao"` |
| Aplicar migrações | `docker compose exec backend alembic upgrade head` |
| Desligar | `docker compose down` |
| Desligar **e apagar o banco local** | `docker compose down -v` |

Após mudar o `requirements.txt`, rode `docker compose up --build` de novo.

## Acessar o banco local (DBeaver, pgAdmin etc.)

- Host: `localhost` · Porta: `5433`
- Usuário: `erp` · Senha: `erp` · Banco: `erp`

## Estrutura do backend

```
backend/app/
├── main.py          # cria a app e registra os routers
├── core/            # infraestrutura: config, banco, erros
├── shared/          # base dos models, dinheiro
└── modules/         # um módulo por domínio de negócio
    └── health/
```

Cada módulo de negócio terá: `router.py`, `schemas.py`, `models.py`, `service.py`,
`repository.py` e `permissions.py`.
