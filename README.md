# ERP SaaS para Microempreendedores

Veja o planejamento completo em [ROADMAP.md](ROADMAP.md).

## Como o ambiente local funciona

| Parte | Onde roda | Endereço |
|---|---|---|
| Banco (PostgreSQL) | Docker | `localhost:5433` |
| Backend (FastAPI) | Docker | http://localhost:8000 |
| Frontend (Next.js) | Direto no Windows | http://localhost:3000 |

O frontend roda fora do Docker porque, no Windows, o recarregamento do Next.js
dentro de containers fica lento.

## Primeira vez

Na raiz do projeto (PowerShell):

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
docker compose up --build -d
cd frontend
npm install
```

## Dia a dia

**Terminal 1**, na raiz:

```powershell
docker compose up -d
```

**Terminal 2**, em `frontend`:

```powershell
npm run dev
```

Abra http://localhost:3000. A documentação da API fica em http://localhost:8000/docs.

## Comandos do backend

Rode na raiz, com os containers ligados.

| O que fazer | Comando |
|---|---|
| Ver logs | `docker compose logs -f backend` |
| Rodar os testes | `docker compose exec backend pytest` |
| Verificar o código | `docker compose exec backend ruff check .` |
| Formatar o código | `docker compose exec backend ruff format .` |
| Criar migração | `docker compose exec backend alembic revision --autogenerate -m "descricao"` |
| Aplicar migrações | `docker compose exec backend alembic upgrade head` |
| Desligar | `docker compose down` |
| Desligar **e apagar o banco local** | `docker compose down -v` |

Após mudar o `requirements.txt`, rode `docker compose up --build -d`.

## Comandos do frontend

Rode dentro de `frontend`.

| O que fazer | Comando |
|---|---|
| Servidor de desenvolvimento | `npm run dev` |
| Verificar o código | `npm run lint` |
| Build de produção (teste local) | `npm run build` |

## Acessar o banco local (DBeaver, pgAdmin etc.)

- Host: `localhost` · Porta: `5433`
- Usuário: `erp` · Senha: `erp` · Banco: `erp`

## Estrutura

```
backend/app/
├── main.py          # cria a app e registra os routers
├── core/            # infraestrutura: config, banco, erros
├── shared/          # base dos models, dinheiro
└── modules/         # um módulo por domínio de negócio

frontend/src/
├── app/             # rotas (páginas) do Next.js
├── lib/             # env e cliente HTTP da API
├── components/ui/   # componentes visuais genéricos
└── modules/         # espelha os módulos do backend
    └── <modulo>/
        ├── api.ts         # chamadas à API
        ├── types.ts       # tipos do módulo
        ├── components/    # componentes do módulo
        └── hooks/         # lógica reutilizável de tela
```
