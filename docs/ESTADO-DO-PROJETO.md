# Estado do projeto — ERP SaaS

> Cole este arquivo no início de um chat novo, junto com o `ROADMAP.md` do repositório.
> Atualizado em: 19 de setembro de 2026 (Fase 6 iniciada: Painel)

## Contexto

ERP SaaS para microempreendedores. O planejamento completo (visão, planos Base/Pro,
modo offline, canais de venda, clientes, plataforma interna, fases) está no
**`ROADMAP.md`** na raiz do repositório — ele é a fonte da verdade.

Desenvolvedor: familiaridade com Python, conhecimento básico em geral, Windows +
Docker Desktop + VS Code. Já usava Supabase, Render e Vercel.

## Stack e ambientes

| Camada | Tecnologia | Local | Staging |
|---|---|---|---|
| Banco | PostgreSQL 17 | Docker (porta 5433) | Supabase `erp-staging` (us-east-1) |
| Backend | Python · FastAPI · SQLAlchemy 2 · Alembic | Docker (porta 8000) | Render `erp-api-staging` (Virginia, Docker) |
| Frontend | Next.js 16 · TypeScript · Tailwind | `npm run dev` (porta 3000) | Vercel (branch `develop`) |

- Monorepo: `backend/`, `frontend/` (e futuramente `loja/` e `admin/`).
- Fluxo: `feature/<nome>` → PR → `develop` (staging) → `main` (produção, ainda não existe).
- Migrações rodam no start do container (`alembic upgrade head` no Dockerfile).
- Variáveis: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `ENVIRONMENT` (backend);
  `NEXT_PUBLIC_API_URL` (frontend).

## O que já está pronto

**Fase 0 — Setup**: ambiente local em Docker, staging completo no ar, health check
(`/api/v1/health`) verde em local e staging.

**Fase 1 — Fundação**
- Tabelas: `usuarios` (global), `empresas`, `membros`, `papeis`, `papel_permissoes`,
  `planos`, `plano_regras`, `assinaturas`, `sessoes`.
- Autenticação própria: Argon2 (pwdlib) + JWT (PyJWT), token de acesso de 15 min e
  token de renovação rotativo de 30 dias guardado como hash; reuso de token revoga a sessão.
- Contexto de empresa vindo sempre da sessão; `requer_permissao(...)`, `requer_recurso(...)`.
- Catálogo de permissões definido no código de cada módulo (`permissions.py`).
- Papéis padrão por empresa: Dono (protegido, todas as permissões implícitas), Gerente,
  Caixa, Estoquista.
- Motor de planos: recursos e limites em `plano_regras`; plano efetivo com trial reverso
  (Pro por 14 dias), carência e cancelamento.
- `RepositorioDaEmpresa`: filtro automático de `empresa_id` em toda consulta.
- Frontend: telas de criar conta, entrar, escolher empresa e painel. Tokens em cookies
  httpOnly gravados pelo servidor do Next.js; renovação automática no `proxy.ts`
  (antigo `middleware.ts`).

**Fase 2 — Etapa 1 (produtos)**
- Tabelas: `unidades` (catálogo global), `categorias`, `produtos`, `produto_unidades`.
- Unidades de medida no código (`produtos/unidades.py`) espelhadas no banco por migração
  de dados; conversão só dentro da mesma grandeza.
- Produto com SKU único por empresa (gerado como `PRD-0001`), unidade de estoque,
  `vendavel` / `insumo` / `controla_estoque`, preço, custo médio, código de barras e
  campos fiscais previstos.
- Unidades alternativas por produto (fatia = 0,125 un; rolo = 1000 g).
- Custo e margem só para quem tem `produtos.ver_custo`.
- Frontend: cadastro, edição, unidades alternativas e a casca do sistema com menu
  lateral e submenus em sanfona (`components/navegacao/itens.ts` define o menu).
- A lista de produtos virou três telas por causa da Etapa 3 — ver abaixo.

**Fase 2 — Etapa 2 (estoque por movimentações)**
- Tabelas `movimentacoes_estoque` (entrada, saída, ajuste, montagem, reserva,
  liberação; `ocorrido_em` / `registrado_em`; `id` aceito do cliente para
  idempotência) e `saldos_estoque` (cache travado com `SELECT FOR UPDATE`).
- Custo médio ponderado recalculado a cada entrada; saída grava o custo vigente sem
  alterar a média; saldo físico negativo permitido (vendas sincronizadas), sem
  bloqueio; reserva/liberação com disponível = físico − reservado.
- Entrada em unidade alternativa (comprar 1 rolo = 1000 g), convertida para a
  unidade de estoque do produto.
- Permissões `estoque.ver`, `estoque.movimentar`, `estoque.ajustar`.
- Frontend: tela de saldos (`/estoque`) e a aba de estoque de cada produto
  (`/produtos/[id]/estoque`) com entrada, ajuste por contagem e histórico.

**Estoque — entrada rápida em modal** (2026-09-19, pedido do desenvolvedor: faltava
um jeito prático de lançar quantidade nos produtos já cadastrados)
- Botão "Estoque" (`modules/estoque/components/botao-estoque.tsx`) abre um modal
  com duas ações: **dar entrada** (soma; custo já vem preenchido com o custo
  médio atual) ou **contar** (define o total, gera ajuste pela diferença).
  Reaproveita as Server Actions `registrarEntrada`/`registrarAjuste`, sem
  backend novo. Aparece em `/estoque`, `/produtos` e `/produtos/insumos`
  (não em kits — kit ganha saldo montando), conforme `estoque.movimentar` /
  `estoque.ajustar`. Compra em unidade alternativa (rolo, caixa) continua na
  página do produto, com link no rodapé do modal. Regra geral daqui pra
  frente: ações rápidas de lista usam modal.

**Fase 6 — Painel / resumo de vendas (Base)** (começo da fase; o resto segue pendente)
- Módulo `app/modules/relatorios/` (router/schemas/permissions, sem tabelas):
  `GET /relatorios/resumo?inicio&fim` (padrão 30 dias; máx. 1 ano; dias em
  horário de Brasília por `ocorrido_em`) compõe `vendas_service.resumo_do_periodo`
  (agregações em `VendaRepositorio`) e `produtos_service`. Só vendas
  **fechadas** faturam; canceladas contadas à parte. Lucro bruto e margem só
  pra quem tem `produtos.ver_custo`. Permissão `relatorios.ver` (Gerente +
  Dono; migração `d5a7e1c39b48`).
- **Painel = página inicial `/` e primeiro item do menu** (substituiu "Início"
  e a rota `/relatorios`, que agora só redireciona pra `/`). **Só administrador**
  = quem tem `relatorios.ver` (Dono e Gerente); os demais perfis são
  redirecionados à primeira tela que podem usar (vendas → estoque → produtos →
  clientes). Mostra "Agora" (vendas de hoje, tickets abertos, caixa aberto/
  fechado com quem abriu, contas vencidas se Pro) e o resumo de 7/30/90 dias
  (cartões, barras por dia em CSS puro, mais vendidos, formas de pagamento).
- **Alertas de estoque (Pro, `Recurso.ALERTAS`)**: `Produto.estoque_minimo`
  (opcional, migração `e9b3c7a41f52`; zero na tela = sem mínimo, vira nulo) e
  `GET /estoque/alertas` (`estoque_service.alertas_de_estoque`): **negativo**
  (físico < 0) e **baixo** (disponível ≤ mínimo, já descontando reservas),
  negativos primeiro. Aparece no Painel só no Pro (no Base a API recusa e o
  bloco some). Campo "Estoque mínimo" no formulário do produto.
- **Relatório de clientes (Pro, `Recurso.RELATORIOS_CLIENTES`, migração
  `f2c8d4b6a913`)**: `GET /relatorios/clientes` (`vendas_service.resumo_de_clientes`).
  **Novo** = a primeira compra fechada de sempre caiu no período;
  **recorrente** = já tinha comprado antes. Médias (ticket, compras por cliente)
  só de vendas fechadas de clientes identificados; o resto aparece como "vendas
  sem cliente". Top 5 por valor. Bloco "Clientes no período" no Painel (Pro).
- **Impacto de descontos na margem (Pro, reaproveita `Recurso.MARGEM_AVANCADA`,
  sem migração)**: `GET /relatorios/descontos` (`vendas_service.resumo_de_descontos`)
  a partir de preço de tabela / desconto / preço final / custo gravados em cada
  item fechado: receita a preço de tabela, descontos (valor e % da tabela),
  vendas e itens com desconto, top 5 produtos por desconto; **lucro sem vs. com
  desconto e "lucro cedido" só com `produtos.ver_custo`** (item sem custo, como
  serviço, conta custo zero). Bloco "Impacto dos descontos" no Painel (Pro).
- **Consumo e perdas de insumos (Pro, `MARGEM_AVANCADA`, sem migração)**:
  `GET /relatorios/insumos` (`estoque_service.consumo_de_insumos`, consulta em
  `MovimentoRepositorio.consumo_e_perdas`). Por produto **marcado como insumo**:
  o que as montagens consumiram (movimentos `montagem` negativos — a perda
  percentual da composição já vem somada, não aparece separada) e o que saiu
  por **ajuste de contagem para baixo** (perda/divergência de inventário), com
  quantidade e custo (custo só com `produtos.ver_custo`). Ajuste para cima e a
  produção do kit não contam. Maior custo primeiro; bloco no Painel (Pro).
- **Exportação em CSV (Pro, `Recurso.EXPORTACAO_RELATORIOS`, migração
  `b7e1a5c93d26`)**: `GET /relatorios/exportar/vendas` — uma linha por item de
  venda fechada no período (venda, data BRT, cliente, SKU, produto, quantidade,
  preço de tabela/desconto/final, total, formas de pagamento; **custo unitário e
  lucro só com `produtos.ver_custo`**). Formato Excel-BR (`;`, vírgula decimal,
  UTF-8 com BOM) em `relatorios/exportacao.py`, que também neutraliza CSV
  injection (texto começando com `= + - @` ganha apóstrofo). Máx. 50 mil linhas.
  Frontend: botão "Exportar vendas (CSV)" no Painel (só se `eu.plano === "pro"`)
  → route handler `app/(app)/relatorios/exportar/route.ts`, que busca no servidor
  com o token do cookie e repassa o arquivo (o navegador não vê token). Só a
  exportação de vendas existe; outros relatórios não exportam ainda.
- **Gráficos no Painel (2026-09-19)**: `components/graficos/graficos.tsx`, SVG
  puro sem biblioteca e sem JS no navegador (server components; `<title>` como
  dica no hover; sempre com legenda/rótulo em texto): `GraficoColunas`
  (faturamento por dia, dias sem venda como zero, eixo em R$ compacto),
  `GraficoBarras` (mais vendidos, com quantidade) e `GraficoRosca` (formas de
  pagamento com % e total no centro; novos × recorrentes no bloco de clientes,
  Pro). Os gráficos base valem pra todos os planos; os de dados Pro seguem
  atrás do plano. Não há gráfico de linha nem de lucro por dia (o backend
  ainda não agrega lucro diário) — seria o próximo passo natural.
- **Avisos de plano no Painel (Base)**: `GET /assinatura/uso`
  (`app/modules/assinaturas/router.py` — a composição com `produtos_service`
  fica no router pra evitar import circular) devolve, por limite realmente
  aplicado hoje (produtos simples e kits), usado × limite × %. No Base o Painel
  mostra faixa amarela a partir de 80% e vermelha ao bater 100%, e um aviso de
  upgrade com dado real (ex.: "você concedeu R$ X em descontos... no Pro vê o
  impacto na margem"). `max_usuarios` **não** entra: nada aplica esse limite
  ainda (não há convite de membros). Como toda empresa nova nasce em trial =
  Pro, esses avisos só aparecem depois do trial ou forçando o plano.
- **Dados de demonstração** (só dev/staging): `docker compose exec backend python
  -m app.scripts.popular_demo --email <usuario>` cria produtos `DEMO-*`, insumos,
  um kit com montagens e perda, 8 clientes, ~45 dias de vendas (descontos,
  crédito/débito/Pix/dinheiro, cancelamentos, pagamento dividido), alertas de
  estoque e contas a pagar/receber. Recusa rodar em produção e duas vezes na
  mesma empresa. Já rodado no banco local do desenvolvedor (empresa do e-mail
  dele): ~260 vendas fechadas.
- Ainda pendente na Fase 6: margem esperada vs. real, vendas por canal, alerta de margem caindo, avisos de upgrade. Testes: 198 passando.

**Cartão de crédito e débito** (2026-09-19, pedido do desenvolvedor)
- `FormaPagamento` agora tem `cartao_credito` e `cartao_debito` (migração
  `a4d6f8b2c015`: recria os 3 CHECKs — pagamentos de venda, lançamentos de caixa,
  contas — com nomes "crus"; `drop_constraint` pede `op.f(nome_completo)`). O
  valor antigo `cartao` **continua válido** como histórico (não dizia se era
  crédito ou débito): aparece nos relatórios como "Cartão (antes da separação)",
  mas nenhuma tela o oferece. Downgrade converte crédito/débito de volta em `cartao`.
- Frontend: `lib/formas-pagamento.ts` centraliza tipo, rótulos e
  `FORMAS_SELECIONAVEIS` (dinheiro, crédito, débito, Pix) — todo select de forma
  usa isso. Acompanhamento: o Painel (recebido por forma) e o relatório já
  agrupam por forma, então crédito e débito saem separados; o caixa ganhou
  `ResumoPorForma` (entradas − saídas por forma, na sessão aberta e no detalhe)
  pra conferir a maquininha. "Esperado em dinheiro" segue contando só `dinheiro`.
  Vendas offline já enfileiradas com `cartao` continuam sincronizando (o valor
  antigo é aceito).
- Testes: 198 passando.

**Digitação padronizada de números** (2026-09-19, refeita no mesmo dia após feedback)
- `components/ui/campo-numero.tsx`: `CampoNumero` (com rótulo) e `InputNumero`
  (sem rótulo, pra tabelas/carrinhos) substituem todo `<input type="number">`.
  Estilo **maquininha**: o campo sempre mostra o formato completo (R$ 0,00 ·
  0,0 g · 0 un) e cada dígito entra pela direita, empurrando os zeros
  (5, 3, 5 → 0,05 → 0,53 → 5,35); apagar tira o último dígito; cursor sempre
  no fim; milhar com ponto. Formatos: `dinheiro` (2 casas, R$), `custo` (4
  casas, R$ — custo por grama/ml; decisão minha, 6 casas seria inviável de
  digitar), `percentual` (2, sufixo %, teto 100 ou `maximo`), `quantidade`
  (casas da `unidade`, em `lib/unidades.ts`: un 0 · g 3 · kg 3 · ml 3 · l 3 ·
  cm 1 · m 2 · m2 2 — 0,000 g, digitando da direita; não confundir com
  `casas_exibidas` do backend, que só arredonda listas; sigla da
  unidade como sufixo; sem unidade conhecida — kit/insumo onde a unidade é
  escolhida no mesmo formulário — usa 3 casas). `positivo` exige > 0; valor
  sai sempre com ponto e todas as casas ("5.35"). Efeito colateral aceito:
  valor com mais casas que o campo é arredondado ao abrir (ex. 0,125 un
  aparece 0 em "un"). Novo campo numérico: usar sempre esses componentes.

**Fase 2 — Etapa 3 (composição / kit)**
- **Decisão tomada nesta etapa**: kit e "produto montado" foram unificados num
  único tipo (`kit`). Não existe mais um kit "calculado" sem estoque próprio — todo
  kit tem saldo de verdade, alimentado pela ação de montar (que dá baixa exata nos
  componentes, incluindo perda percentual, e credita o saldo do kit com o custo
  calculado a partir do que foi consumido). Isso também tirou a diferenciação
  Base/Pro que existia entre "kit simples" e "composto montado": hoje qualquer
  kit pode montar, em qualquer plano; só a quantidade de kits continua limitada
  no Base (`max_compostos`).
- Tabela `componentes_compostos` (receita do kit: componente, quantidade, perda
  percentual). Kit dentro de kit é permitido, com bloqueio de ciclo — ainda
  Pro (`composto_aninhado`), mas vale reavaliar se essa trava Base/Pro faz
  sentido (ver Decisões em aberto).
- Perda percentual por componente (Pro, `perda_na_composicao`) só entra na
  quantidade consumida na montagem, nunca em disponibilidade projetada (kit não
  tem mais isso — ele só mostra o saldo real).
- Módulo `app/modules/composicao/`, depende de `produtos` e `estoque` só via
  service, nunca toca as tabelas deles direto.
- Frontend: três telas de cadastro em vez de uma — **Produtos** (`/produtos`,
  simples vendáveis), **Insumos** (`/produtos/insumos`, `insumo=true` de
  qualquer tipo) e **Kits** (`/produtos/kits`, `tipo=kit`); um item marcado
  como vendável e insumo ao mesmo tempo aparece nas duas primeiras sem
  duplicar cadastro. Seção "Componentes" e ação "Montar" na página de cada kit.

**Ajuste de UX/layout do cadastro de produtos** (implementado em 2026-09-18,
testado e confirmado pelo desenvolvedor):
- Fonte base do sistema maior (`html { font-size: 112.5% }` em `globals.css`)
  — como o Tailwind usa `rem`, isso aumenta texto, espaçamento e área de
  toque em tudo de uma vez. Containers de lista (`/produtos`, `/produtos/insumos`,
  `/produtos/kits`, `/estoque`) alargados de `max-w-4xl` para `max-w-6xl`;
  páginas de detalhe/formulário para `max-w-5xl`.
- Componente `components/ui/modal.tsx` (fecha com Esc/clique fora/X).
- `BotaoEditarProduto` (`modules/produtos/components/`): botão "Editar"
  autocontido (botão + modal + formulário) reaproveitado em quatro lugares —
  no fim de cada linha das tabelas de Produtos/Insumos/Kits, no fim de cada
  linha da tela de Estoque, e na página de detalhe do produto. Mesma
  experiência em todo canto, um só componente pra manter.
- `custo_medio` do produto é editável manualmente no formulário (correção de
  preço de compra/fornecedor, sem precisar lançar uma entrada de estoque).
  `ProdutoAtualizacao.custo_medio` no backend.
- No modal de edição, dois botões: "Salvar e sair" (fecha o modal) e "Salvar
  e continuar editando" (mantém aberto). Depois de qualquer um dos dois,
  aparece um aviso "Desfazer" por 8s (`ToastDesfazer`) que restaura todos os
  campos pro valor de antes daquela edição (snapshot tirado ao abrir o modal,
  reconstruído em FormData por `produtoParaFormData` e reenviado pra
  `atualizarProduto` — chamada direto, sem passar por formulário).
- `SecaoComponentes` (kit): modal "Novo insumo" que cadastra e já vincula
  como componente numa ação só, sem sair da página do kit.
- `BuscaSelecao` (`components/ui/busca-selecao.tsx`): campo de busca com
  filtro client-side, substitui o `<select>` gigante ao escolher um
  componente. "Perda percentual" escondida atrás de `<details>` ("Mais opções").

**Fase 2 — Etapa 4 (tempo de preparo, recursos produtivos, capacidade) — REMOVIDA**
- Decisão do desenvolvedor (2026-09-19): atribuir tempo de máquina e de
  pessoa ficaria confuso demais pro usuário final. Saíram: módulo
  `app/modules/producao/`, tabelas `producao_produtos` e
  `recursos_produtivos` (migração `7d2c41a9e5b3` derruba as duas e o recurso
  de plano `capacidade_producao`), seção "Tempo de preparo" do produto,
  tela `/recursos-produtivos`, capacidade diária, tempo total do kit e o
  custo de produção que somava na margem.
- **Ficou**: custos adicionais manuais (`custos_adicionais_produto`, Pro,
  `Recurso.CUSTOS_ADICIONAIS`) — `custo_adicional_total` agora é só a soma
  deles; margem = `custo_medio + custo_adicional_total`.
- Seções 8.3 do ROADMAP (tempo/capacidade) e itens de Fase 6 que dependiam
  disso ficam sem implementação prevista.

**Fase 3 — Bloco 1 (clientes)**
- Tabela `clientes`: nome, telefone (não único — duplicados existem, mesclagem
  fica pro Bloco 3), e-mail, CPF (opcional, validado só quando informado),
  data de nascimento, endereço, consentimento de marketing (com data, gravada
  automaticamente sempre que o campo vira `true`, limpa quando vira `false`),
  origem (`balcao`/`vitrine`/`marketplace`, só `balcao` usável por enquanto).
  **Sem campo de desativação** — decisão do desenvolvedor: o cadastro de
  cliente não tem estado ativo/inativo, fica simplesmente armazenado até
  ser necessário de novo (diferente da convenção geral do projeto de
  desativar em vez de excluir, que aqui nem se aplica: nunca se exclui nem
  se esconde). `id` aceito do cliente (mesmo padrão de idempotência do
  estoque), pro cadastro no PDV offline não duplicar ao reenviar.
- Permissões próprias `clientes.ver`/`clientes.editar` (Gerente e Caixa têm as
  duas; Estoquista não tem nenhuma). Sem gate de plano.
- Frontend: lista com busca por nome/telefone/e-mail (`/clientes`), criação
  (`/clientes/novo`) e edição em modal na própria linha da lista (mesmo
  padrão `BotaoEditar*` + `ToastDesfazer` dos produtos). Ainda sem página de
  detalhe — fica pro Bloco 3, quando houver histórico de compras pra mostrar.
  Ainda sem teste de uso do desenvolvedor.

**Fase 3 — Bloco 2 (vendas/PDV)**

Uma venda é um **ticket com ciclo de vida** (decisão do desenvolvedor, depois
de ver a primeira versão que só criava a venda já paga de uma vez —
"não sabemos pra que tipo de negócio isso vai servir, então o ticket
precisa poder ficar em aberto até fechar"):

- `StatusVenda`: `aberto` (nasce assim, o caixa ainda pode adicionar/remover
  item) → `fechado` (pago, definitivo) ou `cancelado` (ticket em aberto
  descartado). Cancelar aqui **não** é o "cancelamento de venda com estorno"
  do ROADMAP (seção Fase 3) — isso é só descartar um ticket que nunca chegou
  a fechar; cancelar uma venda já **fechada**, com estorno de estoque de
  verdade (`TipoMovimento.ESTORNO`), continua sendo o Bloco 3.
- **Cada item adicionado reserva estoque na hora** (decisão do
  desenvolvedor: "podem existir reservas, então ao adicionar o produto ao
  pedido é uma boa pedida") — usa `estoque_service.reservar`/`liberar_reserva`,
  que já existiam pra vitrine/marketplace. `ItemVenda` guarda
  `movimento_reserva_id` (criado ao adicionar) e `movimento_estoque_id`
  (a saída de verdade, só criada no fechamento). Remover um item de um
  ticket aberto libera a reserva na hora — sem precisar de estorno.
  Fechar a venda converte cada reserva em saída real
  (`liberar_reserva` + `registrar_saida`) e só então grava o custo unitário
  vigente no item. Cancelar um ticket aberto só libera as reservas.
  Produto sem `controla_estoque` (serviço, mão de obra) nunca reserva nem
  debita nada. **Kit reserva e debita só o próprio saldo** — os componentes
  já foram debitados na montagem (diferente da seção 6.3 do ROADMAP, que
  fala em baixa "inclusive componentes", por causa da unificação kit/montado
  da Etapa 3).
- Tabelas `vendas` (numerada `VD-0001`, `id` aceito do cliente pra
  idempotência), `itens_venda` e `pagamentos_venda` (ambas sem `empresa_id`
  própria, escopadas por `venda_id`, igual `ProdutoUnidade`). Pagamentos só
  existem a partir do fechamento — **pagamento dividido** (decisão do
  desenvolvedor): uma venda pode ter mais de uma forma (ex.: parte dinheiro,
  parte cartão), a soma precisa bater exatamente com o total.
- Cada item guarda preço de tabela, desconto e preço final **por unidade**
  — desconto só aceita percentual na entrada.
- **Limite de desconto por papel**: campo `Papel.limite_desconto_percentual`
  (nulo = sem limite). Caixa = 10%, Gerente e Dono sem limite. Acima do
  limite, só passa se quem está adicionando o item tiver
  `vendas.desconto_acima_limite` (Gerente e Dono têm; Caixa não). **Ainda
  sem tela de papéis editáveis** — o limite só é ajustável direto no banco.
- **Cliente é opcional e pode mudar enquanto o ticket está aberto**: ao abrir
  a venda (`cliente_id` ou `cliente_novo`, cadastro inline reaproveitando
  `clientes_service.criar_cliente`) ou depois, via
  `PATCH /vendas/{id}/cliente` — dá pra atribuir, trocar ou remover o
  cliente de um ticket aberto a qualquer momento.
- Canal de origem (`CanalVenda`) e taxas do canal: mesma decisão do Bloco 2
  original — só `pdv` aceito por enquanto, taxas ficam pra quando existir
  canal cobrando de verdade (Fases 10/11).
- Permissões `vendas.ver`, `vendas.registrar` (Gerente e Caixa) e
  `vendas.desconto_acima_limite` (só Gerente, além do Dono implícito). Sem
  gate de plano.
- **Sem abertura/fechamento de caixa (financeiro)** — fora de escopo da
  Fase 3, é do módulo Financeiro (fase futura).
- Endpoints: `POST /vendas` (abre), `GET /vendas` (lista, filtro por
  `status`/`cliente_id`), `GET /vendas/{id}`, `PATCH /vendas/{id}/cliente`,
  `POST /vendas/{id}/itens`, `DELETE /vendas/{id}/itens/{item_id}`,
  `POST /vendas/{id}/fechar`, `POST /vendas/{id}/cancelar`.
- **Frontend redesenhado como painel único** (`/vendas`), inspirado no
  gerenciador de pedidos do iFood, com paleta própria (não vermelho): abas
  de status com contador (Todos/Abertos/Fechados/Cancelados), lista de
  tickets à esquerda (numero, cliente, total, hora, selo de status
  colorido) e detalhe do ticket selecionado à direita. Botão "+ Iniciar
  venda" abre um modal de seleção de produtos (`ModalSelecionarProdutos`,
  com busca — `SeletorBusca`, componente genérico novo); ao confirmar, abre
  o ticket e adiciona os itens escolhidos. O mesmo modal é reaproveitado no
  painel de detalhe pra "+ Adicionar produto" a um ticket já aberto. Detalhe
  do ticket: atribuir/trocar/remover cliente (`AtribuirCliente`), remover
  item, fechar (`FormularioFechamento`, com divisão de pagamento) ou
  cancelar (com confirmação inline, sem `window.confirm`). Sem
  `useActionState`/FormData nessas telas — todas as ações chamam a Server
  Action direto, e o estado (lista de tickets, seleção, carrinho do modal)
  é local do painel. Sem página de detalhe separada nem tela de PDV
  isolada — tudo dentro do painel de `/vendas`. Ainda sem teste de uso do
  desenvolvedor.

**Fase 3 — Bloco 3 (histórico, cancelamento, LGPD)** — fecha a Fase 3

- **Histórico de compras e métricas na ficha do cliente** (`/clientes/{id}`):
  derivado das vendas **fechadas** desse cliente (nunca uma cópia).
  `vendas_service.metricas_do_cliente` calcula quantidade de compras, valor
  total, ticket médio, primeira e última compra via agregação SQL
  (`func.count`/`sum`/`min`/`max`), direto no `VendaRepositorio` — não em
  Python, pra não trazer todas as vendas pra memória à toa. Endpoint
  `GET /clientes/{id}/metricas` mora no router de clientes (que importa
  `vendas_service` — mesmo padrão de composição no router usado entre
  produtos/produção; sem risco de import circular porque `vendas/service.py`
  importa `clientes/service.py`, nunca o router).
- **Mesclar clientes duplicados**: `Cliente.mesclado_com_id` (auto-FK,
  nulo = não mesclado). `clientes_service.mesclar_clientes` só preenche no
  sobrevivente os campos que ele não tinha (telefone/e-mail/CPF/data de
  nascimento/endereço) — nunca sobrescreve o que já existia; consentimento
  de marketing é reunido (se qualquer um dos dois tinha consentido, o
  sobrevivente passa a ter). As vendas do duplicado são reatribuídas por
  `vendas_service.reatribuir_cliente` (`UPDATE` em massa), chamado do
  router de clientes logo depois de `mesclar_clientes` — os dois numa
  transação só. O duplicado **nunca é excluído**: fica com
  `mesclado_com_id` preenchido e some da listagem (`ClienteRepositorio.buscar`
  filtra por padrão), mas continua respondendo em `obter_cliente` direto
  por id.
- **LGPD**: `anonimizar_cliente` apaga nome/telefone/e-mail/CPF/data de
  nascimento/endereço (nome vira "Cliente anonimizado"), mas mantém o
  registro e o vínculo com as vendas — métricas e histórico continuam
  batendo, só sem dado pessoal. Depois de anonimizado, o cadastro não pode
  mais ser editado (`atualizar_cliente` bloqueia, igual produto congelado).
  `exportar_dados` (`GET /clientes/{id}/exportar`) devolve os dados do
  cliente + lista de compras (número, data, total) — o frontend baixa como
  `.json` (Blob + link temporário no navegador).
- **Cancelamento de venda com estorno de estoque**: `TipoMovimento.ESTORNO`
  novo no enum de movimentação (exigiu migração manual de novo — autogenerate
  não detecta mudança em CHECK constraint, mesmo gotcha de sempre).
  `estoque_service.estornar_saida` credita a quantidade de volta com o
  custo histórico daquele item (não o custo médio atual) e, como o ajuste,
  **não recalcula a média ponderada**. `vendas_service.cancelar_venda` agora
  se ramifica pelo status: ticket **ABERTO** cancelado só libera reservas
  (like antes); venda **FECHADA** cancelada estorna estoque de cada item e
  exige a permissão nova `vendas.cancelar` (só Gerente e Dono — Caixa não;
  reverter uma venda paga é mais sensível que descartar um ticket que nunca
  foi pago). Os pagamentos já registrados **não são estornados
  automaticamente** — não existe integração de reembolso real, fica como
  nota/limitação. `ItemVenda` ganhou `movimento_estorno_id` pra rastrear
  isso também, junto com `movimento_reserva_id`/`movimento_estoque_id`.
  `Venda.cancelado_em` novo (paralelo ao `fechado_em`).
- Frontend: `/clientes/{id}` — dados, métricas em destaque, tabela de
  compras (link pra `/vendas?ticket={id}`, que agora aceita esse parâmetro
  pra abrir o painel já com aquele ticket selecionado, buscando-o à parte
  se não estiver entre os mais recentes carregados), botão "Mesclar
  cadastro duplicado" (busca + confirmação inline) e "Exportar dados" /
  "Anonimizar" (LGPD, com confirmação). Botão "Cancelar venda (estorna
  estoque)" novo no painel de vendas, só aparece pra quem tem
  `vendas.cancelar` e só numa venda fechada. `SeletorBusca` (antes só do
  módulo vendas) virou componente compartilhado
  (`components/ui/seletor-busca.tsx`), reaproveitado também na busca de
  cliente duplicado. Ainda sem teste de uso do desenvolvedor — e, por
  pedido do desenvolvedor, as telas em geral vão passar por uma rodada de
  refinamento visual mais adiante (não é prioridade agora).

**Fase 4 — Bloco 1 (fundação PWA: instalável + catálogo offline, só leitura)**

- **Decisão tomada nesta etapa**: a regra do modo offline (seção 5.4 do
  ROADMAP — aceitar a venda mesmo com estoque negativo) e a reserva de
  estoque do PDV online (Fase 3 Bloco 2) são fluxos **separados**. O PDV
  online continua reservando e bloqueando estoque insuficiente; a venda
  feita offline (ainda não implementada — é o próximo bloco) vai entrar
  direto como venda fechada, sem passar pela reserva. Tempo máximo de
  operação offline (ROADMAP citava "48 a 72h em avaliação): decidido não
  ter limite por enquanto — falta uso real pra calibrar esse número.
- **Sem exposição de token no navegador**: a arquitetura atual (cookies
  httpOnly, o navegador nunca fala com a API direto) continua intacta. A
  fila de sincronização (Bloco 2) não vai exigir isso — o plano é gravar
  localmente enquanto offline e, ao reconectar, reenviar cada item pela
  mesma Server Action de sempre (que já roda no servidor Next.js,
  autenticada pelo cookie existente). "Login sem internet" (Bloco 3) só
  precisa cachear localmente os dados de autorização (`eu`: usuário, papel,
  permissões) pra liberar a UI — nunca um token de verdade; a validação de
  verdade continua acontecendo no servidor quando sincroniza.
- App instalável: `public/manifest.json` (ícone `public/icon.svg`, um SVG
  simples) e `public/sw.js` (service worker mínimo: só cacheia `/offline` e
  serve essa página quando a navegação falha por falta de rede — não faz
  cache agressivo de assets nem de chamadas à API, pra nunca servir dado
  velho quando há conexão). Registrado por
  `components/pwa/registrar-service-worker.tsx` no layout raiz.
- **Bug real encontrado e corrigido**: o `proxy.ts` (guarda de rotas)
  interceptava **todas** as rotas — inclusive `/manifest.json`, `/icon.svg`,
  `/sw.js` e a futura `/offline` — e redirecionava pra `/entrar` sem sessão.
  Isso quebrava o PWA inteiro (nem o manifest carregava sem estar logado).
  Corrigido no `matcher` do proxy, igual já era feito pra `_next/static`.
- Cache local do catálogo: `src/lib/client/banco-local.ts` (IndexedDB cru,
  sem biblioteca nova — o projeto não tinha nenhuma dependência além do
  framework, então não introduzi uma só pra isso). Grava produto + preço +
  saldo (fisico/reservado/disponível). `SincronizarCatalogo` (componente
  client, sem renderizar nada) grava no IndexedDB os dados que a própria
  página já buscou no servidor — sem chamada extra à API. Ligado por
  enquanto só na página `/vendas` (a mais relevante pro PDV offline futuro).
- `/offline`: página fora do grupo `(app)` (não depende de `obterEu()` nem
  de sessão pra renderizar) que lê o catálogo salvo e mostra nome, preço e
  disponível — só leitura, sem registrar venda ainda (isso é o próximo
  bloco). É o que o service worker mostra quando a navegação falha.
- `IndicadorConexao` (`components/pwa/`): mostra online/offline em tempo
  real (`useSyncExternalStore` nos eventos `online`/`offline` do
  navegador) e a hora do catálogo salvo, no topo do menu (mobile) e no
  cabeçalho da barra lateral (desktop).
- Verificação: rodei o frontend e confirmei por HTTP que `/manifest.json`,
  `/icon.svg`, `/sw.js` e `/offline` respondem certo sem sessão, que rotas
  protegidas continuam redirecionando pra `/entrar` normalmente (sem
  regressão no login) e que o build compila sem erro. **Não tive um
  navegador headless disponível neste ambiente** (Windows, sem
  `chromium-cli`) pra verificar interativamente o registro do service
  worker e a leitura/escrita no IndexedDB pelo DevTools — vale o
  desenvolvedor abrir o app, checar a aba Application → Service Workers, e
  testar "offline" no DevTools antes de considerar validado de verdade.
**Fase 4 — Bloco 2 (fila de vendas offline + sincronização)**

- **Endpoint novo, separado do fluxo online**:
  `POST /vendas/sincronizar` (`vendas_service.sincronizar_venda_offline`) —
  recebe a venda offline **já completa** (itens + pagamento) e cria direto
  como `FECHADO`, sem passar pela reserva. Debita estoque na hora
  (`estoque_service.registrar_saida`), permitindo saldo negativo — regra do
  ROADMAP (seção 5.4). `id` obrigatório (gerado no dispositivo): reenviar o
  mesmo não duplica, mesmo padrão de idempotência de sempre. `ocorrido_em`
  também obrigatório — é quando a venda aconteceu de verdade, não quando
  sincronizou (`fechado_em` usa o mesmo valor).
- **Preço vem do dispositivo, não do catálogo atual**: cada item manda
  `preco_tabela` (o que estava em cache no momento da venda) em vez do
  servidor buscar `produto.preco_venda` — se o preço mudou enquanto o
  caixa estava offline, vale o que foi cobrado (regra do ROADMAP,
  seção 5.4). Limite de desconto por papel continua valendo, checado com
  as permissões de quem está sincronizando (normalmente o mesmo
  dispositivo/sessão que fez a venda).
- **Fila local** (`lib/client/banco-local.ts`, nova loja `filaVendas` no
  IndexedDB, banco subiu pra versão 2): cada venda offline vira um registro
  com `id` (o mesmo que vai virar o id da venda), itens, pagamentos,
  `ocorridoEm`, e um campo `erro` (preenchido só se o servidor recusou —
  falha de rede não marca nada, só tenta de novo).
- **Motor de sincronização** (`components/pwa/motor-sincronizacao.tsx`):
  no evento `online` do navegador (e ao montar, se já estiver online),
  processa a fila **em ordem**, um item por vez. Erro de rede no meio para
  o loop inteiro (o resto tenta de novo na próxima reconexão, sem
  duplicar — é só um `catch` em volta do laço). Erro de negócio (chegou no
  servidor, mas foi recusado) marca aquele item com o motivo e segue pros
  próximos, sem travar a fila inteira por causa de um item ruim. Montado
  duas vezes — no layout autenticado e na página `/offline` — pra cobrir
  os dois lugares de onde dá pra reconectar.
- **`/offline` virou um PDV de verdade**: busca produto no catálogo salvo
  (reaproveita o `SeletorBusca` compartilhado), carrinho com quantidade e
  desconto, cliente novo inline (**buscar cliente existente não funciona
  offline** — não cacheamos a lista de clientes, só o catálogo; ficou
  como limitação clara, não silenciosa), pagamento dividido igual ao PDV
  online. "Registrar venda offline" grava na fila local (não chama a
  rede). Lista "vendas aguardando sincronizar" com botão "Cancelar" —
  cancelar uma venda offline **antes** de sincronizar só remove da fila
  local, nunca chega a existir no servidor (regra do ROADMAP,
  seção 5.4) — diferente de cancelar uma venda já sincronizada
  (fechada), que é o fluxo de estorno do Bloco 3 da Fase 3.
- `IndicadorConexao` agora mostra quantas vendas estão pendentes de
  sincronizar, mesmo quando online (enquanto a fila está sendo enviada).
- Testes novos em `test_vendas.py`: idempotência do endpoint de
  sincronização, preço travado no que foi enviado (mesmo com o catálogo
  tendo mudado depois), saldo negativo permitido, limite de desconto ainda
  válido, kit debitando só o próprio saldo, cliente novo inline.
- Ainda sem teste de uso do desenvolvedor, e sem navegador headless neste
  ambiente pra verificar interativamente (mesma limitação do Bloco 1) —
  verifiquei via testes automatizados (backend) e checagem de compilação +
  respostas HTTP (frontend).

**Fase 4 — Bloco 3 (login sem internet, parcial)**

- **Escopo revisado**: o item "fila pra movimentações de caixa avulsas" do
  Bloco 3 (ROADMAP, seção 5.1) depende do módulo Financeiro (Fase 5, "Caixa
  do dia: entradas e saídas"), que ainda não existe — nenhuma linha de
  código dele foi escrita. Em vez de inventar um conceito provisório de
  "caixa" só pra ter algo pra enfileirar, deixei isso claramente bloqueado
  no ROADMAP, esperando a Fase 5 existir de verdade.
- **Sessão cacheada**: `CascaDoApp` já recebe `eu` (usuário, empresa,
  papel, permissões) do servidor — `SincronizarSessao` grava isso no
  IndexedDB (reaproveita a loja `meta` já existente, sem subir a versão do
  banco). Não é uma sessão de verdade nem um token — é só o suficiente
  pra `/offline` saber **quem parece estar logado** e o que essa pessoa
  pode fazer, pra decidir o que mostrar. A validação de verdade continua
  sendo só do servidor, na hora de sincronizar.
- **Por que não precisou de "tela de login offline"**: como o serviço
  worker já serve `/offline` pra qualquer navegação que falhe por falta de
  rede (Bloco 1), a continuidade de sessão já acontece "de graça" — o
  usuário nunca vê uma tela de login pedindo pra entrar de novo enquanto
  offline, só continua vendo o app (a versão offline dele). Não havia nada
  de fato faltando aí além de mostrar quem está logado e travar a parte de
  registrar venda pra quem não tem `vendas.registrar` no papel cacheado.
- `/offline` agora mostra "Logado como {nome} ({papel}) em {empresa}" e
  quanto tempo faz que o app está offline (baseado na mesma hora do
  catálogo salvo). Se não houver sessão cacheada (nunca abriu o app
  online), ou se o papel não tiver `vendas.registrar`, a seção de montar
  venda fica escondida com uma explicação — mas o catálogo salvo e a fila
  de pendências continuam visíveis, porque consultar preço/estoque não
  devia depender dessa permissão.
- **Decisão já tomada antes** (Bloco 1) continua valendo: sem limite de
  tempo offline por enquanto — a infraestrutura pra isso
  (`obterUltimaSincronizacao`) já existe e agora também alimenta o texto
  "você está offline há X", só que sem nenhum bloqueio.
- Ainda sem teste de uso do desenvolvedor, mesma limitação de ambiente das
  vezes anteriores (sem navegador headless aqui pra verificar
  interativamente) — validado por lint, `tsc` e checagem de resposta HTTP.

Testes: 173 passando (`docker compose exec backend pytest`) — Bloco 3 é só
frontend, sem mudança no backend.

**Fase 5 — Financeiro (caixa do dia, plano Base)**

- O ROADMAP só dá pinceladas gerais dessa fase (sem seção detalhada como
  teve Fase 3/4) — o desenho de "caixa" abaixo foi decidido nesta etapa.
- **Decisão tomada**: caixa é uma **sessão de verdade** (abre com valor
  inicial, fecha com conferência do que devia ter vs. o que tem), não só
  um livro de lançamentos soltos — bate com o padrão de PDV brasileiro e
  com a pista que já existia no ROADMAP ("1 caixa no Base, vários
  simultâneos no Pro" só faz sentido pra uma sessão). **Abrir caixa não é
  obrigatório pra vender** — o PDV (Fase 3) continua funcionando igual,
  com ou sem caixa aberto.
- Módulo novo `app/modules/financeiro/`: `CaixaSessao` (status
  aberto/fechado, valor inicial, valor contado no fechamento,
  aberto/fechado por, observação) e `LancamentoCaixa` (entrada ou saída,
  origem venda/manual, forma de pagamento, valor, descrição, `venda_id`
  quando vier de uma venda — sem `empresa_id` própria, escopado pela
  sessão, igual `ProdutoUnidade`).
- **Integração automática, sem quebrar nada que já existia**:
  `vendas_service.fechar_venda` e `sincronizar_venda_offline` chamam
  `financeiro_service.registrar_lancamentos_de_venda` depois de gravar os
  pagamentos — se **houver** um caixa aberto na empresa, cada forma de
  pagamento vira um lançamento automático nele; sem caixa aberto, não faz
  nada (a venda segue normal). `vendas/service.py` importa
  `financeiro/service.py` (nunca o contrário) — sem risco de import
  circular, mesmo padrão já usado entre vendas e clientes.
- **Conferência do fechamento considera só dinheiro**: `resumo_caixa`
  soma entradas/saídas de **todas** as formas pro "total do dia", mas o
  "esperado na gaveta" (usado pra calcular a diferença no fechamento) só
  soma lançamentos em `dinheiro` — cartão e pix nunca caem fisicamente na
  gaveta, então não entram nessa conta. `diferenca` só existe depois de
  fechado (`valor_contado - saldo_esperado_dinheiro`).
- **Limite do plano reaproveitado**: `Limite.MAX_CAIXAS_OFFLINE` já
  existia no catálogo (seed antigo: Base = 1, Pro = ilimitado, mesma
  chave citada na tabela de planos do ROADMAP) mas nunca tinha sido usada
  em código nenhum — `abrir_caixa` agora chama
  `assinaturas_service.verificar_limite` contando quantos caixas estão
  abertos na empresa.
- Permissões novas `financeiro.ver`/`financeiro.operar` (Gerente e Caixa
  têm as duas — a descrição do papel Caixa já dizia "Vendas e caixa do
  dia" desde a Fase 1). Sem gate de plano nas permissões em si (é Base).
- **Abrir caixa mudou de lugar (2026-09-19)**: o botão "Abrir caixa" (modal com
  valor inicial e observação) fica no topo de `/vendas` (`BarraCaixa`), que
  também mostra "Caixa aberto · quem abriu · hora" quando há sessão. `/caixa`
  não tem mais formulário de abertura (só um aviso apontando pra Vendas).
  O histórico guarda e mostra **quem abriu e quem fechou** (`aberto_por_nome`/
  `fechado_por_nome` na API, a partir do usuário logado na ação), em
  `/caixa/historico` e no detalhe.
- Frontend: `/caixa` mostra o caixa aberto (resumo em cards, lançamentos,
  formulário de lançar entrada/saída manual, "conferir e fechar" com
  prévia da diferença calculada no cliente antes de confirmar); `/caixa/historico`
  lista sessões passadas; `/caixa/{id}` é o detalhe só-leitura de uma
  sessão específica. Menu "Financeiro → Caixa do dia" deixou de ser
  "em breve".
- Testes cobrem: abrir/fechar, limite do plano (forçando a regra do Pro,
  já que empresa nova nasce em trial = Pro por 14 dias — mesmo truque já
  usado nos testes de limite de produtos), diferença com e sem conferência
  batendo, lançamento manual bloqueado em caixa fechado, geração
  automática de lançamento em venda fechada (online e sincronizada
  offline) só quando há caixa aberto.
- **Fila offline de entradas/saídas de caixa** (fecha o último item da
  Fase 4): `POST /caixa/lancamentos/sincronizar`
  (`financeiro_service.sincronizar_lancamento_offline`), `id` do dispositivo
  (idempotente), entra no caixa aberto **no momento da sincronização** —
  sem caixa aberto, recusa com mensagem clara e o item fica marcado com o
  erro na fila. No frontend: nova loja `filaLancamentos` no IndexedDB
  (banco na versão 3), formulário em `/offline` (só pra quem tem
  `financeiro.operar` no papel cacheado), lista de pendências com
  "Cancelar", motor de sincronização envia vendas primeiro (que geram
  lançamento automático) e depois os lançamentos avulsos, e o indicador
  de conexão conta as duas filas.
- Ainda sem teste de uso do desenvolvedor, mesma limitação de ambiente das
  vezes anteriores.

- **Contas a pagar e a receber + fluxo de caixa projetado (Pro)**: tabela
  `contas_financeiras` (tipo pagar/receber, status aberta/paga/cancelada,
  descrição, contraparte em texto livre, valor, vencimento, data e forma da
  baixa). Recurso de plano novo `contas_pagar_receber` (só Pro, migração
  `c81f5a3d7e20`); as rotas usam `requer_recurso` + `financeiro.ver`
  (leitura) / `financeiro.operar` (escrita) — sem permissão nova. **Não
  mexe no caixa do dia**: dar baixa numa conta não gera lançamento de
  caixa (decisão minha, simples; pode virar integração depois). "Vencida" é
  derivada (aberta com vencimento < hoje, no horário de Brasília), não um
  status. Só conta em aberto pode ser baixada ou cancelada; nada é excluído.
  `fluxo_projetado(dias)` agrega só contas abertas por dia, sem saldo
  inicial (o caixa é por sessão): o acumulado é o resultado líquido, e as
  vencidas ficam à parte, somadas ao acumulado do primeiro dia.
  Endpoints: `GET/POST /contas`, `GET /contas/fluxo-projetado`,
  `POST /contas/{id}/baixa`, `POST /contas/{id}/cancelar`. Frontend:
  `/contas` (cards do fluxo, tabela de dias com movimento, formulário,
  filtros e baixa/cancelar inline); no Base mostra aviso de plano Pro.
  Ainda sem teste de uso do desenvolvedor.

Testes: 198 passando (`docker compose exec backend pytest`).

## Convenções do código

- Camadas por módulo: `router.py` → `service.py` → `repository.py`; módulos conversam
  por services, nunca pelas tabelas uns dos outros.
- Services fazem `flush`; quem faz `commit` é o router.
- Dinheiro em `Decimal` (2 casas), quantidades com 4 casas, custos unitários com 6.
- Estoque e custo sempre na unidade base do produto.
- Nada referenciado por histórico é excluído: desativa-se.
- Registro de outra empresa responde "não encontrado" (404).
- Toda tabela de empresa usa `EmpresaMixin` + `RepositorioDaEmpresa`, com testes de isolamento.
- Migrações de dados ficam em `migrations/pendentes/` até receberem o `down_revision`.
- Cuidado ao usar `op.create_check_constraint` em migração: a metadata tem
  `naming_convention` configurada, então o nome passado deve ser "cru" (sem o
  prefixo `ck_<tabela>_`), senão ele duplica (`ck_produtos_ck_produtos_...`).

## Próximo passo

**Fase 3 completa** (clientes, vendas/PDV, histórico/cancelamento/LGPD).
**Fase 5 (Financeiro) parcialmente feita** — caixa do dia (plano Base)
pronto: abrir/fechar sessão, lançamento manual, lançamento automático de
venda; contas a pagar/receber e fluxo de caixa projetado (Pro) também
prontos. **Fase 5 completa.**

**Fase 4 completa** — PWA, fila de vendas offline, sessão cacheada e fila
de entradas/saídas de caixa offline. Ainda sem teste de uso do
desenvolvedor.

Fora de escopo da Fase 3 (fica pra Fase 9, conforme o ROADMAP): segmentação
RFM, cupons, fidelidade, campanhas.

Ainda em aberto dentro do que já foi construído (não bloqueia nada, só não
foi implementado): tela de papéis editáveis (o limite de desconto do Caixa
e as permissões de cada papel só são ajustáveis direto no banco); estorno
de pagamento na hora de cancelar uma venda fechada (hoje só estorna
estoque; não existe integração de reembolso real ainda).

Nota: não foi adicionado um campo de "fornecedor" ao produto — não existe
hoje no modelo nem no ROADMAP; a edição de preço/fornecedor citada pelo
desenvolvedor foi entendida como motivação para o botão "Editar", não um
pedido de campo novo. Se for necessário, é uma migração pequena em `produtos`.

## Decisões em aberto

- **Composição aninhada (kit dentro de kit) exclusiva do Pro**: faz sentido
  manter essa trava, ou deveria ser liberada geral agora que kit/montado
  viraram um tipo só? Suspenso desde a unificação da Etapa 3.
- Tela de categorias: página própria ou criar categoria direto no formulário do produto.
- Ícones no menu lateral (exigiria instalar `lucide-react`).
- Fintech de pagamentos (Asaas é candidata), provedor de e-mail, região de produção.
- Demais decisões estão listadas no `ROADMAP.md`, seção "Decisões ainda em aberto".
