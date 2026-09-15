# Roadmap — ERP SaaS para Microempreendedores

> Documento vivo. Atualize sempre que uma decisão mudar.
> Última revisão: setembro de 2026

---

## 1. Visão

Sistema de gestão simples para microempreendedores: produtos, PDV, estoque, financeiro e análises.

**Diferencial:** produtos compostos com profundidade real — kits, produtos montados, composição aninhada, custos adicionais (filamento, energia, embalagem, mão de obra) e margem esperada vs. real.

**Posicionamento dos planos:**
- **Base** → *operar* o negócio.
- **Pro** → *entender e crescer* o negócio.

---

## 2. Stack

| Camada | Tecnologia | Hospedagem |
|---|---|---|
| Backend (API e regras de negócio) | Python · FastAPI · SQLAlchemy 2 · Alembic · Pydantic | Render |
| Banco de dados | PostgreSQL | Supabase |
| Frontend | Next.js · TypeScript | Vercel |
| Pagamentos (futuro) | Asaas | — |

**Arquitetura:** monolito modular em monorepo (`backend/` e `frontend/`).

---

## 3. Princípios de arquitetura (valem para todas as fases)

1. **Multi-tenant desde o dia 1.** Toda tabela de negócio tem `empresa_id`, aplicado automaticamente na camada base — nunca "lembrado" manualmente.
2. **Estoque é um livro de movimentações.** O saldo é a soma das entradas, saídas, ajustes, vendas e montagens.
3. **Dinheiro nunca em `float`.** Usar `Decimal` (ou centavos em inteiro).
4. **Grava tudo em todos os planos, limita só o acesso.** Cada venda guarda o custo do momento, mesmo no Base. Ao virar Pro, o histórico já está pronto.
5. **Permissões granulares.** Papéis compostos por permissões (`produto.editar`, `venda.cancelar`). Nada de `if admin` espalhado.
6. **Planos são dados, não código.** Recursos, limites e estado ficam em tabela; o código só pergunta.
7. **Campos fiscais previstos no produto** (NCM, CEST, origem, unidade) mesmo sem uso até a NF-e.
8. **Camadas com responsabilidade única por módulo:** `router` → `service` → `repository`. Módulos não acessam tabelas uns dos outros; conversam via services.

---

## 4. Planos

### 4.1 Divisão Base vs. Pro

| Recurso | Base (operar) | Pro (gerir e crescer) |
|---|---|---|
| Produtos simples | Até 200 | Ilimitado |
| Produto composto | Kit simples (só produtos), até 5 | Ilimitado |
| Custos adicionais (filamento, energia, embalagem, mão de obra) | — | ✓ |
| Composto montado (baixa de componentes na montagem) | — | ✓ |
| Composto dentro de composto | — | ✓ |
| Margem | Margem simples do produto | Esperada vs. real, histórico, por venda |
| PDV e baixa de estoque | ✓ | ✓ |
| Financeiro | Caixa do dia, entradas e saídas | Contas a pagar/receber, fluxo projetado |
| Usuários | 1 a 2, papéis fixos | Vários, papéis editáveis |
| Gráficos e relatórios | Resumo básico | Completos, exportáveis |
| Alertas (estoque baixo, margem caindo) | — | ✓ |

### 4.2 Estratégias de conversão para o Pro

- **Teste reverso:** todo cliente novo começa com o Pro completo por 14 dias; se não assinar, cai para o Base.
- **Aviso contextual com dados reais:** ex. "3 produtos estão vendendo abaixo da margem esperada este mês". Só com informação verdadeira e útil.
- **Aviso de limite antes de bater:** "você usou 4 de 5 compostos", em vez de bloqueio seco.
- **Desconto no plano anual.**

### 4.3 Downgrade (Pro → Base)

Nada é apagado. Os compostos acima do limite do Base ficam **congelados**:

- O cliente escolhe quais compostos (até o limite) continuam **ativos**.
- Compostos **congelados**: sem edição, sem novos cadastros, sem montagem.
- O estoque já existente dos congelados **pode ser vendido até zerar**.
- O histórico de vendas permanece intacto.
- Ao voltar para o Pro, tudo reativa imediatamente.

Recursos exclusivos do Pro (custos adicionais, papéis editáveis etc.) ficam somente leitura enquanto o cliente estiver no Base.

### 4.4 Modelo de regras de plano

| Tipo | Exemplos |
|---|---|
| Recursos (liga/desliga) | `custos_adicionais`, `composto_montado`, `composto_aninhado`, `papeis_editaveis`, `margem_avancada`, `alertas` |
| Limites (numéricos) | `max_produtos_simples = 200`, `max_compostos = 5`, `max_usuarios = 2` |
| Estado da assinatura | `trial` · `ativa` · `inadimplente` · `cancelada` |

Pagamento em atraso **não bloqueia no mesmo dia**: há um período de carência antes de qualquer congelamento.

### 4.5 Decisões ainda em aberto

- [ ] Valores exatos dos limites do Base (200 simples / 5 compostos são provisórios)
- [ ] Duração do teste reverso (14 dias provisório)
- [ ] Duração da carência por inadimplência
- [ ] Preços mensal e anual de cada plano

---

## 5. Ambientes e fluxo de deploy

### 5.1 Ambientes

| Ambiente | Para quê | Backend | Banco | Frontend |
|---|---|---|---|---|
| **Local (dev)** | Programar e testar livremente | Docker na máquina | PostgreSQL no Docker | Máquina local |
| **Staging** | Validar antes de liberar | Render (branch `develop`) | Projeto Supabase de staging | Vercel (preview) |
| **Produção** | Clientes reais | Render (branch `main`) | Projeto Supabase de produção | Vercel (produção) |

A troca entre ambientes é feita só por variáveis (ex. `DATABASE_URL`), nunca por mudança de código.

### 5.2 Fluxo de branches

```
feature/<nome>  →  develop  →  main
 (local)          (staging)   (produção)
```

1. Cada funcionalidade nasce em uma branch `feature/...` e é desenvolvida localmente.
2. Pull Request para `develop` → deploy automático em staging → teste manual.
3. Merge de `develop` em `main` → deploy automático em produção.

### 5.3 Regras

- **Staging e produção nunca compartilham banco.**
- **Migrações sempre passam pelo staging antes da produção.**
- **Dados de clientes reais nunca vão para staging ou máquina local** (risco de vazamento e LGPD). Usar o script de seed.
- **Segredos fora do código:** `.env` local fora do Git; em nuvem, variáveis nos painéis do Render e da Vercel, separadas por ambiente.
- Planos gratuitos são aceitáveis para staging; produção com clientes pagantes deve usar planos pagos.

---

## 6. Fases de desenvolvimento

> **Mudança em relação ao rascunho inicial:** o *motor de planos* (recursos, limites, estado) sobe para a Fase 1, porque quase todos os módulos dependem dele para liberar ou limitar funções. A *cobrança* com Asaas continua na Fase 6.

### Fase 0 — Setup do projeto e ambientes
**Código e ambiente local**
- [ ] Monorepo com `backend/` e `frontend/`
- [ ] `docker-compose` com FastAPI + PostgreSQL (mesma versão principal do Supabase)
- [ ] FastAPI rodando com estrutura de módulos
- [ ] Alembic configurado (migrações idênticas em todos os ambientes)
- [ ] Next.js com TypeScript e estrutura `modules/`
- [ ] `.env` local + `.env.example` versionado (`.env` no `.gitignore`)
- [ ] Linting e formatação (ex. ruff, prettier)
- [ ] Script de seed com dados fictícios

**Git e ambientes na nuvem**
- [ ] Branches `main` (produção) e `develop` (staging)
- [ ] Projeto Supabase de staging
- [ ] Serviço Render de staging apontando para `develop`
- [ ] Vercel com previews por branch
- [ ] Deploy inicial em staging logo no começo (não esperar o beta)

**Mais adiante (antes dos primeiros clientes)**
- [ ] Projeto Supabase de produção
- [ ] Serviço Render de produção apontando para `main`
- [ ] Migração para planos pagos de hospedagem
- [ ] GitHub Actions rodando testes a cada Pull Request

### Fase 1 — Fundação
- [ ] Autenticação (login, JWT, hash de senha)
- [ ] Empresas e isolamento multi-tenant automático
- [ ] Usuários, papéis e permissões granulares
- [ ] Papéis fixos (Base) e papéis editáveis (Pro)
- [ ] **Motor de planos:** tabela de planos, recursos, limites e estado da assinatura
- [ ] Helpers `requer_recurso(...)` e `verificar_limite(...)`
- [ ] Trial reverso: empresa nova nasce com Pro por 14 dias

### Fase 2 — Produtos e estoque (coração do sistema)
- [ ] Produto simples (preço, custo, campos fiscais previstos)
- [ ] Produto composto tipo **kit** (estoque calculado pelos componentes)
- [ ] Produto composto **montado** (montagem dá baixa nos componentes e entrada no composto) — Pro
- [ ] Composto dentro de composto, com bloqueio de ciclos — Pro
- [ ] Custos adicionais por produto — Pro
- [ ] Margem simples (Base) e margem esperada (Pro)
- [ ] Status do produto: `ativo` / `congelado`
- [ ] Estoque por movimentações (entrada, saída, ajuste, montagem)
- [ ] Aplicação dos limites de plano (produtos e compostos)

### Fase 3 — PDV e vendas
- [ ] Tela de PDV
- [ ] Venda com baixa de estoque (inclusive componentes de kits)
- [ ] Registro do custo no momento da venda em **todos os planos**
- [ ] Descontos e formas de pagamento
- [ ] Cancelamento de venda com estorno de estoque
- [ ] Venda de compostos congelados até zerar o estoque

### Fase 4 — Financeiro
- [ ] Caixa do dia: entradas e saídas (Base)
- [ ] Contas a pagar e a receber (Pro)
- [ ] Fluxo de caixa projetado (Pro)
- [ ] Integração automática vendas → lançamentos

### Fase 5 — Relatórios, gráficos e alertas
- [ ] Resumo básico (Base)
- [ ] Margem esperada vs. real, histórico e por venda (Pro)
- [ ] Gráficos completos e exportação (Pro)
- [ ] Alertas de estoque baixo e margem caindo (Pro)
- [ ] Avisos contextuais de upgrade com dados reais (Base)
- [ ] Aviso de proximidade de limite

### Fase 6 — Assinaturas e cobrança
- [ ] Integração com Asaas (checkout e webhooks)
- [ ] Planos mensal e anual (com desconto)
- [ ] Transições de estado: trial → ativa → inadimplente → cancelada
- [ ] Período de carência por inadimplência
- [ ] Fluxo de downgrade: escolha dos compostos ativos e congelamento dos demais
- [ ] Reativação automática ao voltar para o Pro

### Fase 7 — Fiscal (futuro)
- [ ] Entrada de notas (XML de compra → movimentação de estoque)
- [ ] Emissão de NF-e / NFC-e
- [ ] Saída de notas

---

## 7. Estrutura de pastas (referência)

```
erp/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, database, security, tenancy, permissions, plans, exceptions
│   │   ├── shared/        # money, pagination
│   │   └── modules/
│   │       ├── auth/
│   │       ├── empresas/
│   │       ├── usuarios/
│   │       ├── produtos/
│   │       ├── estoque/
│   │       ├── vendas/
│   │       ├── financeiro/
│   │       ├── relatorios/
│   │       ├── assinaturas/
│   │       └── fiscal/
│   ├── migrations/
│   └── tests/
└── frontend/
    └── src/
        ├── app/
        ├── modules/
        ├── components/ui/
        └── lib/
```

Cada módulo do backend:

```
<modulo>/
├── router.py        # HTTP: recebe, valida, chama o service
├── schemas.py       # Pydantic: entrada e saída da API
├── models.py        # SQLAlchemy: tabelas
├── service.py       # regras de negócio
├── repository.py    # consultas ao banco
└── permissions.py   # permissões definidas pelo módulo
```
