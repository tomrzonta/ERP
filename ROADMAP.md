# Roadmap — ERP SaaS para Microempreendedores

> Documento vivo. Atualize sempre que uma decisão mudar.
> Última revisão: setembro de 2026

---

## 1. Visão

Sistema de gestão simples para microempreendedores: produtos, PDV, estoque, financeiro e análises.

**Diferencial:** produtos compostos com profundidade real — kits, produtos montados, composição aninhada, custos adicionais (filamento, energia, embalagem, mão de obra) e margem esperada vs. real.

**Continuidade:** o PDV continua vendendo e consultando preços mesmo sem internet, sincronizando quando a conexão volta.

**Todos os canais, um só estoque:** balcão, vitrine online e marketplaces (Mercado Livre, Shopee) descontam do mesmo estoque — inclusive produtos compostos — com margem real por canal.

**Posicionamento dos planos:**
- **Base** → *operar* o negócio.
- **Pro** → *entender e crescer* o negócio.

---

## 2. Stack

| Camada | Tecnologia | Hospedagem |
|---|---|---|
| Backend (API e regras de negócio) | Python · FastAPI · SQLAlchemy 2 · Alembic · Pydantic | Render |
| Tarefas em segundo plano (sincronização com canais) | Worker Python (ferramenta a definir) | Render (serviço separado) |
| Banco de dados | PostgreSQL | Supabase |
| Arquivos (fotos de produtos) | Supabase Storage | Supabase |
| Frontend de gestão | Next.js · TypeScript | Vercel |
| Vitrine online | Next.js · TypeScript (aplicação separada) | Vercel |
| Modo offline | PWA · IndexedDB | Navegador do cliente |
| Pagamentos (assinaturas) | Asaas | — |
| App desktop (evolução futura) | Tauri ou Electron · SQLite | Máquina do cliente |

**Arquitetura:** monolito modular em monorepo (`backend/`, `frontend/` e `loja/`).

---

## 3. Princípios de arquitetura (valem para todas as fases)

1. **Multi-tenant desde o dia 1.** Toda tabela de negócio tem `empresa_id`, aplicado automaticamente na camada base — nunca "lembrado" manualmente.
2. **Estoque é um livro de movimentações.** O saldo é a soma das entradas, saídas, ajustes, vendas, montagens, reservas e liberações.
3. **Dinheiro nunca em `float`.** Usar `Decimal` (ou centavos em inteiro).
4. **Grava tudo em todos os planos, limita só o acesso.** Cada venda guarda o custo do momento, mesmo no Base. Ao virar Pro, o histórico já está pronto.
5. **Permissões granulares.** Papéis compostos por permissões (`produto.editar`, `venda.cancelar`). Nada de `if admin` espalhado.
6. **Planos são dados, não código.** Recursos, limites e estado ficam em tabela; o código só pergunta.
7. **Campos fiscais previstos no produto** (NCM, CEST, origem, unidade) mesmo sem uso até a NF-e.
8. **Camadas com responsabilidade única por módulo:** `router` → `service` → `repository`. Módulos não acessam tabelas uns dos outros; conversam via services.
9. **IDs gerados no cliente.** Registros que podem nascer offline (vendas, itens, movimentações de caixa) usam UUID gerado no próprio dispositivo, sem depender do servidor.
10. **Operações idempotentes.** Enviar a mesma venda ou notificação duas vezes nunca a duplica: a API reconhece o identificador já recebido e ignora a repetição.
11. **Duas datas por registro sincronizável.** `ocorrido_em` (quando aconteceu) e `registrado_em` (quando chegou ao servidor). Relatórios usam `ocorrido_em`.
12. **Venda que já aconteceu não é recusada.** Vendas vindas do PDV offline ou de marketplaces são aceitas mesmo que deixem o estoque negativo; o sistema gera alerta para ajuste.
13. **Estoque único para todos os canais.** Nenhum canal tem estoque próprio, exceto fulfillment controlado pelo marketplace.
14. **Canais por adaptadores.** O sistema conhece apenas operações genéricas (enviar estoque, importar pedidos); cada marketplace é um adaptador isolado.
15. **API pública separada da API de gestão.** A vitrine usa rotas próprias, sem login, somente leitura de dados públicos e com limite de requisições. Custo e margem nunca saem por elas.
16. **Credenciais de terceiros criptografadas.** Tokens de acesso aos marketplaces nunca ficam em texto puro no banco.
17. **Integrações fora da requisição.** Sincronizações, notificações e novas tentativas rodam em tarefas de segundo plano, não enquanto o usuário espera.

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
| PDV offline | 1 caixa | Vários caixas simultâneos |
| Vitrine online com pedido via WhatsApp | Produtos publicados limitados, endereço padrão | Ilimitado, domínio próprio |
| Integração com marketplaces | — | ✓ |
| Estoque de segurança por canal | — | ✓ |
| Margem real por canal (comissões e frete) | — | ✓ |
| Financeiro | Caixa do dia, entradas e saídas | Contas a pagar/receber, fluxo projetado |
| Usuários | 1 a 2, papéis fixos | Vários, papéis editáveis |
| Gráficos e relatórios | Resumo básico | Completos, exportáveis, por canal |
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

Recursos exclusivos do Pro ficam somente leitura enquanto o cliente estiver no Base. Além disso:

- **PDV offline:** apenas um dispositivo permanece autorizado a operar offline.
- **Marketplaces:** a sincronização é pausada e o cliente é avisado de que o estoque dos anúncios deixa de ser atualizado. Os vínculos entre anúncios e produtos são mantidos.
- **Vitrine:** volta ao endereço padrão; produtos acima do limite deixam de ser exibidos.

### 4.4 Modelo de regras de plano

| Tipo | Exemplos |
|---|---|
| Recursos (liga/desliga) | `custos_adicionais`, `composto_montado`, `composto_aninhado`, `papeis_editaveis`, `margem_avancada`, `alertas`, `marketplaces`, `dominio_proprio`, `margem_por_canal` |
| Limites (numéricos) | `max_produtos_simples = 200`, `max_compostos = 5`, `max_usuarios = 2`, `max_caixas_offline = 1`, `max_produtos_vitrine` |
| Estado da assinatura | `trial` · `ativa` · `inadimplente` · `cancelada` |

Pagamento em atraso **não bloqueia no mesmo dia**: há um período de carência antes de qualquer congelamento.

### 4.5 Decisões ainda em aberto

- [ ] Valores exatos dos limites do Base (200 simples / 5 compostos são provisórios)
- [ ] Duração do teste reverso (14 dias provisório)
- [ ] Duração da carência por inadimplência
- [ ] Preços mensal e anual de cada plano
- [ ] Tempo máximo de operação offline (48 a 72 horas em avaliação)
- [ ] Limite de produtos publicados na vitrine do Base
- [ ] Primeiro marketplace a integrar (decidir com base em onde os primeiros clientes vendem)
- [ ] Ferramenta de tarefas em segundo plano
- [ ] Região de produção: manter Render + Supabase nos EUA ou migrar API e banco juntos para São Paulo (decidir com medições reais antes dos primeiros clientes)

---

## 5. Modo offline

### 5.1 Escopo

O objetivo é manter o balcão funcionando sem internet, não o sistema inteiro.

| Funciona offline | Só online |
|---|---|
| Consultar produtos, preços e estoque (última cópia sincronizada) | Cadastrar e editar produtos e composições |
| Lançar vendas no PDV | Usuários, papéis e permissões |
| Cancelar venda feita offline, antes de sincronizar | Financeiro completo e relatórios |
| Registrar entradas e saídas simples de caixa | Assinatura, planos, vitrine e marketplaces |

### 5.2 Formato

- **Primeiro: PWA.** O próprio frontend instalável pelo Chrome/Edge, com dados locais em IndexedDB. Mesmo código, sem instalador nem atualização manual.
- **Evolução futura: app desktop** (Tauri ou Electron + SQLite), quando houver necessidade de hardware (impressora térmica, gaveta, NFC-e em contingência) ou de armazenamento local mais robusto.

### 5.3 Sincronização

- Registros feitos offline entram numa **fila de pendências** local.
- A tela mostra o status: online, offline e quantidade de itens aguardando sincronização.
- Ao reconectar, a fila é enviada em ordem para a API, que processa de forma idempotente.
- Envio interrompido é simplesmente reenviado, sem risco de duplicar.

### 5.4 Regras de conflito

| Situação | Regra |
|---|---|
| Mesmo item vendido por dois caixas offline | Ambas as vendas são aceitas; estoque pode ficar negativo; alerta para ajuste |
| Preço alterado enquanto o caixa estava offline | Vale o preço cobrado no caixa, gravado no item da venda |
| Venda cancelada offline antes de sincronizar | Removida da fila; não chega ao servidor |
| Login sem internet | Último usuário logado no dispositivo continua, com as permissões da última sincronização, por tempo limitado |
| Tempo offline acima do limite | PDV bloqueia novas vendas até sincronizar |

---

## 6. Canais de venda

### 6.1 Visão geral

| Canal | Tipo | Como o pedido chega ao ERP |
|---|---|---|
| PDV (balcão) | Interno | Venda direta, online ou sincronizada do offline |
| Vitrine online | Interno | Pedido pendente, finalizado via WhatsApp |
| Marketplaces (Mercado Livre, Shopee...) | Externo | Importado automaticamente via integração |

Toda venda registra o **canal de origem** e, quando houver, as **taxas do canal** (comissão e frete cobrados), permitindo relatórios e margem real por canal.

### 6.2 Vitrine

- Produtos marcados como **publicados**, com fotos, descrição pública e endereço amigável (ex. `/vaso-com-suculenta`).
- Custo e margem nunca aparecem.
- Cliente final monta o pedido e finaliza pelo WhatsApp; o pedido entra no ERP como **pendente**.
- Pedido pendente **reserva estoque** por tempo limitado; ao confirmar vira venda, ao expirar ou cancelar a reserva é liberada.
- Endereço padrão (ex. `nomedaloja.dominio-do-erp.com.br`) e **domínio próprio** no Pro.
- Com caixas offline, o estoque exibido pode estar defasado: a vitrine é conservadora (ex. "últimas unidades" em vez do número exato quando o estoque está baixo).
- Campos e textos padrão para ajudar o lojista com as obrigações legais de venda online (dados do vendedor, direito de arrependimento, LGPD). Validar com assessoria jurídica antes do lançamento.

### 6.3 Marketplaces

**Etapa 1 — Vincular e sincronizar** (escopo inicial)
- Lojista autoriza o ERP na conta do marketplace.
- Importação dos anúncios existentes e vínculo com produtos do ERP, pelo SKU ou manualmente.
- Anúncios podem ser vinculados a **produtos compostos**: a disponibilidade vem do estoque dos componentes, e cada venda dá baixa neles.
- Envio automático do estoque para os anúncios vinculados.
- Importação automática de pedidos, com baixa de estoque e registro de comissão e frete.

**Etapa 2 — Gestão de anúncios pelo ERP** (evolução futura)
- Criar e editar anúncios, com categorias, atributos e variações de cada marketplace.

**Regras**
- **Um marketplace de cada vez:** o primeiro muito bem feito antes de adicionar o segundo.
- **Estoque de segurança por canal:** ex. mostrar sempre 1 unidade a menos no marketplace do que existe no estoque.
- **Pedido de marketplace nunca é recusado:** registrado mesmo com estoque negativo, com alerta.
- **Fulfillment (ex. Full do Mercado Livre):** estoque no armazém do marketplace, tratado separadamente e sem baixa no estoque próprio.
- **Notificações dos marketplaces** processadas em segundo plano, de forma idempotente, com novas tentativas.
- **Respeitar limites de requisições** de cada marketplace (envios em lote e fila).
- **Renovação automática de acesso** e aviso ao lojista quando a autorização expirar.
- Verificar requisitos atuais de cadastro de aplicativo/parceiro de cada marketplace antes de iniciar a fase.

---

## 7. Ambientes e fluxo de deploy

### 7.1 Ambientes

| Ambiente | Para quê | Backend e worker | Banco | Frontend e vitrine |
|---|---|---|---|---|
| **Local (dev)** | Programar e testar livremente | Docker na máquina | PostgreSQL no Docker | Máquina local (fora do Docker) |
| **Staging** | Validar antes de liberar | Render (branch `develop`) | Projeto Supabase de staging | Vercel (preview) |
| **Produção** | Clientes reais | Render (branch `main`) | Projeto Supabase de produção | Vercel (produção) |

A troca entre ambientes é feita só por variáveis (ex. `DATABASE_URL`), nunca por mudança de código.

### 7.2 Fluxo de branches

```
feature/<nome>  →  develop  →  main
 (local)          (staging)   (produção)
```

1. Cada funcionalidade nasce em uma branch `feature/...` e é desenvolvida localmente.
2. Pull Request para `develop` → deploy automático em staging → teste manual.
3. Merge de `develop` em `main` → deploy automático em produção.

### 7.3 Regras

- **Staging e produção nunca compartilham banco.**
- **Migrações sempre passam pelo staging antes da produção.**
- **Dados de clientes reais nunca vão para staging ou máquina local** (risco de vazamento e LGPD). Usar o script de seed.
- **Segredos fora do código:** `.env` local fora do Git; em nuvem, variáveis nos painéis do Render e da Vercel, separadas por ambiente.
- **Repositório privado** no GitHub.
- **Conexão Render → Supabase pelo Session pooler** (o Render exige IPv4).
- **Data API do Supabase desativada:** todo acesso aos dados passa pelo FastAPI.
- **Staging conectado a contas de teste dos marketplaces**, nunca às contas reais dos clientes.
- **API e banco sempre na mesma região** (hoje: Render Virginia + Supabase us-east-1 + funções da Vercel em iad1).
- **Senha do banco só com letras e números**, gerada aleatoriamente e trocada se aparecer em logs ou prints.
- **Testar antes de enviar:** rodar `pytest` e só fazer commit se todos os testes passarem.
- **CORS com endereços exatos:** o endereço fixo da branch na Vercel, sem barra no final. Variáveis `NEXT_PUBLIC_` exigem novo deploy ao mudar.
- Planos gratuitos são aceitáveis para staging; produção com clientes pagantes deve usar planos pagos.

---

## 8. Fases de desenvolvimento

> **Mudanças em relação ao rascunho inicial:**
> - O *motor de planos* sobe para a Fase 1, porque quase todos os módulos dependem dele. A *cobrança* com Asaas fica na Fase 7.
> - O *PDV offline* entra como Fase 4, logo após o PDV online.
> - *Vitrine* (Fase 8) e *marketplaces* (Fase 9) entram depois das assinaturas, com o núcleo validado. As bases que eles exigem (SKU, dados públicos, reserva de estoque, canal e taxas na venda) já entram nas Fases 2 e 3.

### Fase 0 — Setup do projeto e ambientes
**Código e ambiente local**
- [x] Monorepo com `backend/` e `frontend/`
- [x] `docker-compose` com FastAPI + PostgreSQL (mesma versão principal do Supabase)
- [x] FastAPI rodando com estrutura de módulos
- [x] Alembic configurado (migrações idênticas em todos os ambientes)
- [x] Next.js com TypeScript e estrutura `modules/`
- [x] `.env` local + `.env.example` versionado (`.env` no `.gitignore`)
- [x] Linting e formatação (ruff, ESLint)
- [ ] Script de seed com dados fictícios (quando existirem tabelas)

**Git e ambientes na nuvem**
- [x] Branches `main` (produção) e `develop` (staging)
- [x] Projeto Supabase de staging (us-east-1)
- [x] Serviço Render de staging apontando para `develop` (Virginia, Docker, health check)
- [x] Vercel com previews por branch (endereço fixo da branch `develop` liberado no CORS)
- [x] Deploy inicial em staging logo no começo (não esperar o beta)
- [x] Validação da `DATABASE_URL` e senha mascarada nos logs

**Mais adiante (antes dos primeiros clientes)**
- [ ] Projeto Supabase de produção
- [ ] Serviço Render de produção apontando para `main`
- [ ] Migração para planos pagos de hospedagem
- [ ] GitHub Actions rodando testes a cada Pull Request
- [ ] Execução automática de migrações no deploy
- [ ] Definir região de produção com medições reais a partir do Brasil
- [ ] Plano pago da Vercel para uso comercial (e avaliar time próprio para o ERP)

### Fase 1 — Fundação
- [ ] Autenticação (login, JWT, hash de senha)
- [ ] Empresas e isolamento multi-tenant automático
- [ ] Usuários, papéis e permissões granulares
- [ ] Papéis fixos (Base) e papéis editáveis (Pro)
- [ ] **Motor de planos:** tabela de planos, recursos, limites e estado da assinatura
- [ ] Helpers `requer_recurso(...)` e `verificar_limite(...)`
- [ ] Trial reverso: empresa nova nasce com Pro por 14 dias
- [ ] Cadastro de dispositivos (base para caixas offline)

### Fase 2 — Produtos e estoque (coração do sistema)
- [ ] Produto simples (preço, custo, campos fiscais previstos)
- [ ] **SKU único por empresa** (chave para vínculo com marketplaces)
- [ ] Campos públicos previstos: publicado na vitrine, fotos, descrição pública, endereço amigável
- [ ] Upload de fotos (Supabase Storage)
- [ ] Produto composto tipo **kit** (estoque calculado pelos componentes)
- [ ] Produto composto **montado** (montagem dá baixa nos componentes e entrada no composto) — Pro
- [ ] Composto dentro de composto, com bloqueio de ciclos — Pro
- [ ] Custos adicionais por produto — Pro
- [ ] Margem simples (Base) e margem esperada (Pro)
- [ ] Status do produto: `ativo` / `congelado`
- [ ] Estoque por movimentações (entrada, saída, ajuste, montagem)
- [ ] Movimentações de **reserva** e **liberação** previstas no modelo
- [ ] Saldo negativo permitido para vendas sincronizadas e de marketplaces, com alerta
- [ ] Aplicação dos limites de plano (produtos e compostos)

### Fase 3 — PDV e vendas (online)
- [ ] Tela de PDV
- [ ] Venda com baixa de estoque (inclusive componentes de kits)
- [ ] Registro do preço e do custo no momento da venda em **todos os planos**
- [ ] **Canal de origem** da venda (PDV, vitrine, marketplace)
- [ ] **Taxas do canal** na venda (comissão e frete)
- [ ] UUID da venda e dos itens gerado no frontend
- [ ] Endpoint de venda idempotente
- [ ] Datas `ocorrido_em` e `registrado_em`
- [ ] Descontos e formas de pagamento
- [ ] Cancelamento de venda com estorno de estoque
- [ ] Venda de compostos congelados até zerar o estoque

### Fase 4 — PDV offline
- [ ] Frontend como PWA instalável
- [ ] Cópia local de produtos, preços e estoque (IndexedDB)
- [ ] Atualização periódica da cópia local enquanto online
- [ ] Fila local de vendas e movimentações de caixa pendentes
- [ ] Indicador de status (online, offline, pendências)
- [ ] Sincronização automática ao reconectar
- [ ] Tratamento de conflitos conforme seção 5.4
- [ ] Sessão offline do último usuário, com tempo limite
- [ ] Limite de caixas offline por plano (1 no Base, vários no Pro)

### Fase 5 — Financeiro
- [ ] Caixa do dia: entradas e saídas (Base)
- [ ] Contas a pagar e a receber (Pro)
- [ ] Fluxo de caixa projetado (Pro)
- [ ] Integração automática vendas → lançamentos (inclusive vendas sincronizadas)

### Fase 6 — Relatórios, gráficos e alertas
- [ ] Resumo básico (Base)
- [ ] Margem esperada vs. real, histórico e por venda (Pro)
- [ ] Vendas e margem por canal (Pro)
- [ ] Gráficos completos e exportação (Pro)
- [ ] Alertas de estoque baixo, estoque negativo e margem caindo (Pro)
- [ ] Avisos contextuais de upgrade com dados reais (Base)
- [ ] Aviso de proximidade de limite

### Fase 7 — Assinaturas e cobrança
- [ ] Integração com Asaas (checkout e webhooks)
- [ ] Planos mensal e anual (com desconto)
- [ ] Transições de estado: trial → ativa → inadimplente → cancelada
- [ ] Período de carência por inadimplência
- [ ] Fluxo de downgrade: compostos, caixas offline, vitrine e marketplaces (seção 4.3)
- [ ] Reativação automática ao voltar para o Pro

### Fase 8 — Vitrine online
- [ ] Aplicação `loja/` no monorepo, publicada na Vercel
- [ ] API pública separada, somente leitura, com limite de requisições
- [ ] Página da loja e página de produto, otimizadas para busca (SEO)
- [ ] Carrinho e finalização do pedido via WhatsApp
- [ ] Pedido pendente com reserva de estoque e expiração
- [ ] Confirmação do pedido no ERP (vira venda com canal "vitrine")
- [ ] Endereço padrão por loja
- [ ] Domínio próprio (Pro)
- [ ] Limite de produtos publicados por plano
- [ ] Textos e campos de apoio às obrigações legais

### Fase 9 — Marketplaces (etapa 1: vincular e sincronizar)
- [ ] Módulo `canais` com interface genérica e adaptadores
- [ ] Worker de tarefas em segundo plano (serviço separado)
- [ ] Credenciais criptografadas e renovação automática de acesso
- [ ] Adaptador do primeiro marketplace
- [ ] Autorização da conta do lojista
- [ ] Importação de anúncios e vínculo com produtos (SKU ou manual)
- [ ] Vínculo de anúncios com produtos compostos
- [ ] Envio automático de estoque, com estoque de segurança por canal
- [ ] Recebimento de notificações e importação de pedidos (idempotente, com novas tentativas)
- [ ] Registro de comissão e frete por pedido
- [ ] Tratamento separado de anúncios em fulfillment
- [ ] Painel de status da integração (última sincronização, erros, autorização expirada)

### Fase 10 — Fiscal (futuro)
- [ ] Entrada de notas (XML de compra → movimentação de estoque)
- [ ] Emissão de NF-e / NFC-e
- [ ] NFC-e em contingência offline, integrada à fila de sincronização
- [ ] Saída de notas

### Evoluções futuras
- [ ] Segundo marketplace (novo adaptador)
- [ ] Marketplaces etapa 2: criar e editar anúncios pelo ERP
- [ ] App desktop (Tauri ou Electron + SQLite) com acesso a impressora térmica e gaveta

---

## 9. Estrutura de pastas (referência)

```
erp/
├── backend/
│   ├── app/
│   │   ├── main.py            # API
│   │   ├── worker.py          # tarefas em segundo plano (Fase 9)
│   │   ├── core/              # config, database, security, tenancy, permissions, plans, exceptions
│   │   ├── shared/            # models base, money, pagination
│   │   └── modules/
│   │       ├── auth/
│   │       ├── empresas/
│   │       ├── usuarios/
│   │       ├── dispositivos/
│   │       ├── produtos/
│   │       ├── estoque/
│   │       ├── vendas/
│   │       ├── financeiro/
│   │       ├── relatorios/
│   │       ├── assinaturas/
│   │       ├── vitrine/       # rotas públicas da loja
│   │       ├── canais/
│   │       │   └── adaptadores/   # um por marketplace
│   │       └── fiscal/
│   ├── migrations/
│   └── tests/
├── frontend/                  # sistema de gestão
│   └── src/
│       ├── app/
│       ├── modules/
│       ├── components/ui/
│       └── lib/
│           └── offline/       # banco local, fila de pendências, sincronização (Fase 4)
└── loja/                      # vitrine pública (Fase 8)
    └── src/
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
