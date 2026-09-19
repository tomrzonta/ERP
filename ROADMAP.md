# Roadmap — ERP SaaS para Microempreendedores

> Documento vivo. Atualize sempre que uma decisão mudar.
> Última revisão: setembro de 2026

---

## 1. Visão

Sistema de gestão simples para microempreendedores: produtos, PDV, estoque, financeiro e análises.

**Diferencial:** produtos compostos com profundidade real — kits com montagem e baixa automática, composição aninhada, custos adicionais (filamento, energia, embalagem, mão de obra) e margem esperada vs. real.

**Continuidade:** o PDV continua vendendo e consultando preços mesmo sem internet, sincronizando quando a conexão volta.

**Todos os canais, um só estoque:** balcão, vitrine online e marketplaces (Mercado Livre, Shopee) descontam do mesmo estoque — inclusive produtos compostos — com margem real por canal.

**Relacionamento com clientes:** cadastro com histórico de compras, cupons, fidelidade e campanhas para quem já compra, respeitando a LGPD.

**Produção artesanal e insumos:** produtos e insumos em frações (gramas, mililitros, fatias).

**Operação do próprio SaaS:** console interno com gestão de assinantes, cobrança integrada à fintech e CRM com métricas do negócio.

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
| Console da plataforma (equipe interna) | Next.js · TypeScript (aplicação separada) | Vercel |
| Modo offline | PWA · IndexedDB | Navegador do cliente |
| Pagamentos (assinaturas) | Provedor via adaptador (Asaas é candidato) | — |
| App desktop (evolução futura) | Tauri ou Electron · SQLite | Máquina do cliente |

**Arquitetura:** monolito modular em monorepo (`backend/`, `frontend/`, `loja/` e `admin/`).

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
18. **Usuário não é cliente.** Usuários operam o sistema e fazem login (globais, ligados a empresas por `membros`). Clientes compram do lojista, pertencem a uma única empresa e nunca são cruzados entre empresas.
19. **Saldos como livro de movimentações.** Assim como o estoque, o saldo de fidelidade é a soma de créditos, resgates, expirações e estornos.
20. **Preço de tabela, desconto e preço final separados na venda.** Permite medir quanto da margem foi consumido por descontos, cupons e fidelidade.
21. **Nada referenciado por histórico é excluído.** Usuários, membros e produtos são desativados; dados pessoais de clientes podem ser anonimizados, mas as vendas permanecem.
22. **Quantidades nunca em `float`.** Quantidades em `Decimal` com até 4 casas; custos unitários com até 6 casas (ex. custo por grama); valores finais em dinheiro com 2 casas.
23. **Estoque e custo sempre na unidade base do produto.** Conversões (caixa, fatia, quilo) acontecem só na entrada e na saída; o livro de movimentações nunca mistura unidades.
24. **Plataforma separada dos assinantes.** A equipe interna usa aplicação, rotas e contas próprias, com MFA e auditoria total. É o único lugar com visão entre empresas, e por isso nunca reaproveita o contexto de empresa dos assinantes.
25. **Pagamentos por adaptadores.** O sistema conhece operações genéricas (criar assinatura, gerar cobrança, processar evento); cada fintech é um adaptador. Dados de cartão nunca passam pelo sistema.
26. **Exceções de plano são dados com validade e motivo.** Ajustes por empresa (liberar recurso, ampliar limite) ficam registrados, expiram e são aplicados pelo motor de planos, nunca por condições no código.

---

## 4. Planos

### 4.1 Divisão Base vs. Pro

| Recurso | Base (operar) | Pro (gerir e crescer) |
|---|---|---|
| Produtos simples | Até 200 | Ilimitado |
| Kit (componentes + montagem, dá baixa e credita saldo próprio) | Até 5 | Ilimitado |
| Custos adicionais (filamento, energia, embalagem, mão de obra) | — | ✓ |
| Kit dentro de kit | — | ✓ |
| Margem | Margem simples do produto | Esperada vs. real, histórico, por venda |
| PDV e baixa de estoque | ✓ | ✓ |
| Unidades fracionadas (g, kg, ml, l, m) e unidades alternativas (caixa, fatia) | ✓ | ✓ |
| Insumos e composição com quantidades fracionadas | ✓ | ✓ |
| Perda percentual por componente | — | ✓ |
| PDV offline | 1 caixa | Vários caixas simultâneos |
| Vitrine online com pedido via WhatsApp | Produtos publicados limitados, endereço padrão | Ilimitado, domínio próprio |
| Integração com marketplaces | — | ✓ |
| Estoque de segurança por canal | — | ✓ |
| Margem real por canal (comissões e frete) | — | ✓ |
| Cadastro de clientes e histórico de compras | ✓ Ilimitado | ✓ |
| Desconto manual com limite por permissão | ✓ | ✓ |
| Cupons | — | ✓ |
| Fidelidade (carimbos e cashback) | — | ✓ |
| Segmentação de clientes e campanhas | — | ✓ |
| Financeiro | Caixa do dia, entradas e saídas | Contas a pagar/receber, fluxo projetado |
| Usuários | 1 a 2, papéis fixos | Vários, papéis editáveis |
| Gráficos e relatórios | Resumo básico | Completos, exportáveis, por canal e por cliente |
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
- **Cupons:** deixam de ser aceitos em novas vendas; histórico de uso preservado.
- **Fidelidade:** para de acumular, mas **os saldos já conquistados pelos clientes continuam resgatáveis** até a expiração prevista nas regras. O cliente final não pode ser prejudicado pela troca de plano do lojista.
- **Produção:** recursos produtivos e custo por hora ficam somente leitura; o custo já calculado dos produtos é preservado. Perdas percentuais continuam aplicadas às composições existentes, mas não podem ser editadas.
- **Ajustes por empresa** concedidos pela equipe continuam valendo até a validade, independentemente do plano.

### 4.4 Modelo de regras de plano

| Tipo | Exemplos |
|---|---|
| Recursos (liga/desliga) | `custos_adicionais`, `composto_aninhado`, `papeis_editaveis`, `margem_avancada`, `alertas`, `marketplaces`, `dominio_proprio`, `margem_por_canal`, `cupons`, `fidelidade`, `segmentacao_clientes`, `perda_na_composicao` |
| Limites (numéricos) | `max_produtos_simples = 200`, `max_compostos = 5`, `max_usuarios = 2`, `max_caixas_offline = 1`, `max_produtos_vitrine` |
| Estado da assinatura | `trial` · `ativa` · `inadimplente` · `cancelada` |
| Ajustes por empresa | Recurso liberado ou limite alterado para uma empresa específica, com validade e motivo, sobrepondo as regras do plano |

Pagamento em atraso **não bloqueia no mesmo dia**: há um período de carência antes de qualquer congelamento.

### 4.5 Decisões ainda em aberto

- [ ] Valores exatos dos limites do Base (200 simples / 5 compostos são provisórios)
- [ ] Duração do teste reverso (14 dias provisório)
- [ ] Duração da carência por inadimplência
- [ ] Preços mensal e anual de cada plano
- [x] Tempo máximo de operação offline — decidido não ter limite por
      enquanto (Fase 4 Bloco 1); revisar quando houver uso real pra calibrar
- [ ] Limite de produtos publicados na vitrine do Base
- [ ] Primeiro marketplace a integrar (decidir com base em onde os primeiros clientes vendem)
- [ ] Ferramenta de tarefas em segundo plano
- [ ] Provedor de envio de e-mails (recuperação de senha, verificação, convites) — escolher antes do beta
- [ ] Política de anonimização de clientes e prazos de guarda de dados (validar com assessoria jurídica)
- [x] Limites de desconto padrão por papel — Caixa 10%, Gerente e Dono sem
      limite (Fase 3 Bloco 2); ainda só ajustável no banco, sem tela
- [ ] Região de produção: manter Render + Supabase nos EUA ou migrar API e banco juntos para São Paulo (decidir com medições reais antes dos primeiros clientes)
- [ ] Fintech de pagamentos (Asaas é candidata; escolher antes da Fase 7)
- [ ] CRM de vendas para leads antes do cadastro: construir ou integrar ferramenta de mercado
- [ ] Política de acesso do suporte aos dados do assinante (duração da liberação, somente leitura, LGPD)
- [ ] Lista inicial de unidades de medida e casas decimais exibidas por unidade

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

## 7. Clientes e relacionamento

### 7.1 Cadastro

- Cada cliente pertence a **uma empresa**; dados nunca são compartilhados ou cruzados entre empresas.
- Campos: nome, **telefone** (principal meio de contato), e-mail, CPF (opcional; necessário para CPF na nota), data de nascimento, endereço, **consentimento de marketing** (com data) e origem (balcão, vitrine, marketplace).
- Cliente é **opcional na venda**; vendas de balcão sem identificação continuam rápidas.
- UUID gerado no dispositivo, permitindo cadastro no PDV offline.
- **Mesclar clientes duplicados** (ex. mesmo telefone cadastrado em dois caixas), unindo histórico e saldos.
- Clientes vindos de marketplaces ficam marcados e **fora de ações de marketing**, respeitando as regras de cada marketplace.

### 7.2 Histórico de compras

- O histórico é **derivado das vendas** ligadas ao cliente, não uma cópia separada.
- Na ficha do cliente: compras, itens, valores, descontos, cupons usados, canal e movimentações de fidelidade.
- Métricas mantidas por cliente para consultas rápidas (recalculáveis a partir das vendas): primeira e última compra, quantidade de compras, valor total e ticket médio.
- Cancelamento de venda atualiza as métricas.
- No PDV offline, o caixa consulta apenas os dados básicos do cliente; o histórico completo é consultado online.

### 7.3 Segmentação ("febre" do cliente)

Classificação pelo método **RFM**: **R**ecência (há quanto tempo comprou), **F**requência (quantas vezes) e **V**alor (quanto gastou).

| Segmento | Perfil típico | Ação sugerida |
|---|---|---|
| Campeões | Compraram recentemente, com frequência e alto valor | Bonificação, acesso antecipado |
| Fiéis | Compram com frequência | Fidelidade, cupons exclusivos |
| Novos | Primeira compra recente | Incentivo à segunda compra |
| Em risco | Compravam bem, mas sumiram | Campanha de retorno |
| Perdidos | Sem compras há muito tempo | Reativação ou nenhuma ação |

- Segmentos recalculados periodicamente em segundo plano.
- Faixas de recência e frequência ajustáveis, pois variam por tipo de negócio.

### 7.4 Descontos, cupons e fidelidade

**Descontos**
- Venda guarda preço de tabela, desconto e preço final.
- Limite de desconto por papel; acima dele, autorização de quem tem `vendas.desconto_acima_limite`, registrada na auditoria.

**Cupons**
- Código, tipo (percentual ou valor fixo), validade, valor mínimo, produtos e canais válidos, limite total e por cliente.
- Cada uso ligado à venda; cancelamento devolve o uso.
- **Cupons com limite de uso só funcionam online**; cupons sem limite funcionam também offline.
- Alerta quando o cupom leva a venda abaixo do custo.
- Aceitos na vitrine.

**Fidelidade**
- Modelos iniciais: **cartão de carimbos** e **cashback**. Pontos com catálogo de recompensas fica como evolução futura.
- Saldo como livro de movimentações (crédito, resgate, expiração, estorno).
- Regras de acúmulo, uso e expiração exibidas de forma clara ao cliente final.

### 7.5 Campanhas

- Selecionar clientes por segmento, aniversário, inatividade ou histórico de compra.
- Ações: bonificar com cashback, gerar cupom exclusivo, exportar lista para contato.
- **Contato de marketing só com clientes que deram consentimento.** Bonificação no saldo não depende de consentimento; o envio de mensagem, sim.
- Envio automático por WhatsApp ou e-mail fica como evolução futura.

### 7.6 Direitos do cliente (LGPD)

- **Exportar** os dados e o histórico de compras de um cliente, quando ele solicitar.
- **Corrigir** dados cadastrais.
- **Anonimizar** a pedido: dados pessoais substituídos, vendas preservadas para fins contábeis e fiscais.
- Registro na auditoria de exportações e anonimizações.
- Regras e prazos a validar com assessoria jurídica.

---

## 8. Unidades, insumos e produção

### 8.1 Unidades de medida

- Cada produto tem uma **unidade de estoque** (base): unidade, grama, quilo, mililitro, litro, centímetro, metro ou metro quadrado.
- Quantidades **decimais** em estoque, composições, movimentações e vendas.
- **Conversões fixas** entre unidades da mesma grandeza (kg ↔ g, l ↔ ml, m ↔ cm).
- **Unidades alternativas por produto**, com fator de conversão definido pelo lojista:
  - de compra: rolo de filamento de 1 kg, saco de terra de 5 kg, caixa com 12 unidades;
  - de venda: fatia = 1/8 do bolo, porção de 250 g.
- Estoque e custo **registrados sempre na unidade base**; a conversão acontece apenas na entrada e na saída.

### 8.2 Insumos e composição fracionada

- O produto pode ser **vendável**, **insumo** ou os dois — os dois ao mesmo tempo é normal (ex. um vaso vendido solto e também usado como componente de outro kit); não precisa cadastrar duas vezes.
- Cada componente da composição tem **quantidade fracionada** na unidade dele, e o custo é proporcional.
- Kit tem saldo próprio; a **montagem** dá baixa **exatamente na fração consumida** de cada componente, nunca em uma unidade inteira, e credita o saldo do kit com o custo do que foi consumido. Kit dentro de kit é permitido, com bloqueio de ciclo.
- A venda de um kit (quando a Fase 3 existir) desconta do saldo dele como qualquer produto — a baixa nos componentes já aconteceu na montagem, não na venda.
- **Perda percentual por componente** (Pro): ex. 5% de filamento em suportes e falhas de impressão, somada ao consumo e ao custo — só entra na montagem, nunca é descontada do saldo do kit antes disso.
- Venda fracionada no PDV (ex. 0,350 kg); integração com balança como evolução futura.

**Exemplo — Vaso impresso com suculenta**

| Componente | Unidade base | Quantidade no composto | Baixa na montagem |
|---|---|---|---|
| Filamento PLA | g | 85 g (+5% de perda no Pro) | 85 g (ou 89,25 g) |
| Terra adubada | kg | 0,150 kg | 0,150 kg |
| Suculenta | un | 1 | 1 un |
| Embalagem | un | 1 | 1 un |

### 8.3 Tempo de preparo e capacidade de produção — removido

Decisão de 19/09/2026: atribuir tempo de máquina e de pessoa ficaria confuso demais para o usuário final. Tempo de preparo, recursos produtivos, capacidade diária e custo por hora foram retirados do escopo (código e tabelas removidos). Permanecem os **custos adicionais manuais** (energia, embalagem, mão de obra) como valor fixo por produto.

---

## 9. Plataforma: console interno e CRM de assinantes

### 9.1 Separação e segurança

- **Aplicação própria** (`admin/`) e rotas próprias (`/api/v1/plataforma/...`).
- **Operadores** (equipe interna) em tabela própria, sem relação com os usuários dos assinantes.
- **MFA obrigatório** e papéis internos (administrador, suporte, financeiro, comercial) com permissões próprias.
- **Auditoria da plataforma** em toda ação: quem, o quê, em qual empresa e com qual motivo.
- **Acesso do suporte aos dados de negócio** do assinante somente com liberação temporária feita pelo próprio assinante, somente leitura por padrão, e registrado também na auditoria da empresa.

### 9.2 Gestão de assinantes

- **Ficha do assinante:** empresa, dono e contatos, documento, plano, status, trial, datas, uso versus limites, última atividade, dispositivos e canais conectados.
- **Ações:** trocar plano, estender trial, conceder carência, aplicar desconto ou cortesia, suspender e reativar.
- **Ajustes por empresa:** liberar um recurso ou alterar um limite para uma empresa específica, com validade e motivo, aplicados pelo motor de planos.

### 9.3 Cobrança e integração com a fintech

- Módulo `pagamentos` com **interface genérica e um adaptador por provedor**.
- Operações: cadastrar cliente, criar, alterar e cancelar assinatura, gerar cobrança, segunda via e estorno.
- **Webhooks idempotentes** processados em segundo plano, com registro dos eventos recebidos.
- **Faturas e pagamentos espelhados no banco**, com o identificador do provedor, para consulta e relatórios.
- Pagamento pelo checkout do provedor; **dados de cartão nunca passam pelo sistema**.
- **Régua de cobrança:** lembrete antes do vencimento, aviso de atraso, carência e suspensão.
- Cupons e descontos **da assinatura do SaaS**, separados dos cupons que os lojistas criam para os clientes deles.

### 9.4 CRM

- **Funil do assinante:** lead → trial → pagante → em risco → cancelado → reativado.
- **Linha do tempo** por assinante, reunindo interações da equipe (notas, ligações, e-mails, reuniões) e eventos do sistema (cadastro, upgrade, falha de pagamento).
- Tarefas e lembretes para a equipe; tags e segmentos.
- **Motivo de cancelamento** obrigatório e pesquisa de saída.
- **Saúde da conta:** uso recente, recursos ativados, falhas de pagamento e chamados, compondo um indicador de risco de cancelamento.
- Avisos dentro do sistema e comunicados segmentados por plano, uso ou situação.

### 9.5 Métricas do negócio

- Receita recorrente mensal (MRR) e anual (ARR), com novos, expansão, contração e perdas.
- Churn de clientes e de receita, conversão do trial em pagante, receita média por conta (ARPA), valor do cliente ao longo do tempo (LTV) e coortes.
- Uso de cada recurso por plano, para entender o que de fato leva ao upgrade.

### 9.6 Construir ou integrar

- **Construir:** tudo que depende dos dados do sistema — assinaturas, ajustes, cobrança, saúde da conta, suporte e métricas.
- **Avaliar integração** com ferramentas de mercado para a parte de vendas antes do cadastro (captação de leads, e-mail marketing), em vez de reconstruir o que já existe.

---

## 10. Ambientes e fluxo de deploy

### 10.1 Ambientes

| Ambiente | Para quê | Backend e worker | Banco | Frontend e vitrine |
|---|---|---|---|---|
| **Local (dev)** | Programar e testar livremente | Docker na máquina | PostgreSQL no Docker | Máquina local (fora do Docker) |
| **Staging** | Validar antes de liberar | Render (branch `develop`) | Projeto Supabase de staging | Vercel (preview) |
| **Produção** | Clientes reais | Render (branch `main`) | Projeto Supabase de produção | Vercel (produção) |

A troca entre ambientes é feita só por variáveis (ex. `DATABASE_URL`), nunca por mudança de código.

### 10.2 Fluxo de branches

```
feature/<nome>  →  develop  →  main
 (local)          (staging)   (produção)
```

1. Cada funcionalidade nasce em uma branch `feature/...` e é desenvolvida localmente.
2. Pull Request para `develop` → deploy automático em staging → teste manual.
3. Merge de `develop` em `main` → deploy automático em produção.

### 10.3 Regras

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

## 11. Fases de desenvolvimento

> **Mudanças em relação ao rascunho inicial:**
> - O *motor de planos* sobe para a Fase 1, porque quase todos os módulos dependem dele. A *cobrança* com Asaas fica na Fase 7.
> - O *PDV offline* entra como Fase 4, logo após o PDV online.
> - O *console da plataforma* nasce junto com a cobrança (Fase 7), porque ninguém deve cobrar assinantes sem conseguir gerenciá-los. O *CRM completo e as métricas* vêm logo depois (Fase 8).
> - *Unidades fracionadas, insumos e tempo de preparo* entram na Fase 2, porque mudam o modelo de estoque e de composição desde o início.
> - *Clientes, cupons e fidelidade* (Fase 9), *vitrine* (Fase 10) e *marketplaces* (Fase 11) entram depois das assinaturas, com o núcleo validado. As bases que eles exigem (SKU, dados públicos, reserva de estoque, cliente, canal, descontos e taxas na venda) já entram nas Fases 2 e 3.

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

**Decisões**
- Autenticação **própria no FastAPI** (portabilidade, sessão offline e multi-empresa), com bibliotecas consolidadas para hash e tokens.
- Usuário **global**, podendo pertencer a **várias empresas** via `membros`.
- Permissões **definidas no código** de cada módulo; o banco guarda só os códigos concedidos a cada papel.
- Papéis **por empresa**, criados a partir de padrões (Dono protegido, Gerente, Caixa, Estoquista).
- Permissões fora do token: consultadas a cada requisição (com cache curto) para revogação imediata.

**Tabelas**
- [x] `usuarios` (global), `empresas` (com `slug` e fuso horário), `membros` (status ativo, convidado, desativado)
- [x] `papeis` e `papel_permissoes`
- [x] `planos`, `plano_regras` (recursos e limites) e `assinaturas`
- [x] `sessoes` (token de renovação guardado como hash)
- [ ] `dispositivos`, `convites` e `auditoria`

**Funcionalidades**
- [x] Primeira migração e execução de migrações no staging
- [x] Cadastro de conta criando empresa, papéis padrão e assinatura Pro em trial
- [x] Login com escolha de empresa quando o usuário pertence a mais de uma
- [x] Token de acesso curto e token de renovação rotativo e revogável, com revogação por reuso
- [x] "Sair de todos os dispositivos" e revogação imediata de membros desativados
- [ ] Limite de tentativas de login
- [x] Empresa sempre vinda da sessão validada (`obter_contexto`)
- [ ] Filtro automático de `empresa_id` na camada base dos repositórios
- [x] Registro de outra empresa retorna "não encontrado"
- [ ] Testes automatizados de isolamento entre empresas (obrigatórios em cada módulo novo)
- [x] Catálogo de permissões por módulo, validado na inicialização
- [x] Permissões dos próximos módulos (`produtos.ver_custo`, `clientes.ver`, `clientes.editar`, `vendas.desconto_acima_limite`) junto com cada módulo
- [ ] Papéis fixos (Base) e papéis editáveis (Pro)
- [x] **Motor de planos:** plano efetivo, `requer_recurso(...)`, `requer_permissao(...)` e `verificar_limite(...)`
- [x] Trial reverso: empresa nova nasce com Pro por 14 dias
- [ ] Convites por e-mail com link de validade limitada
- [ ] Auditoria de ações sensíveis (permissões, membros, assinatura)
- [ ] Estrutura de recuperação de senha e verificação de e-mail (envio real depende do provedor de e-mail)
- [ ] Telas de cadastro, login e escolha de empresa no frontend (Next.js como intermediário, tokens em cookie protegido)

### Fase 2 — Produtos e estoque (coração do sistema)
- [x] Produto simples (preço, custo, campos fiscais previstos)
- [x] **SKU único por empresa** (chave para vínculo com marketplaces)
- [ ] Campos públicos previstos: publicado na vitrine, fotos, descrição pública, endereço amigável (publicado/descrição prontos; fotos e endereço amigável não)
- [ ] Upload de fotos (Supabase Storage)
- [x] Produto composto tipo **kit** — kit e "montado" viraram um tipo só: kit sempre tem saldo próprio, a montagem dá baixa nos componentes e credita o saldo dele (ver Decisões em aberto)
- [x] Composto dentro de composto (kit dentro de kit), com bloqueio de ciclos — Pro
- [ ] Custos adicionais por produto — Pro
- [ ] Margem simples (Base) pronta; margem esperada vs. real (Pro) não
- [ ] Status do produto: `ativo` / `congelado` — campo existe, mas nada ainda dispara o congelamento automático no downgrade
- [x] Estoque por movimentações (entrada, saída, ajuste, montagem)
- [x] Entrada e contagem rápidas por modal nas listas (Estoque, Produtos, Insumos), sem abrir a página do produto
- [x] Movimentações de **reserva** e **liberação** previstas no modelo
- [x] Saldo negativo permitido para vendas sincronizadas e de marketplaces, com alerta
- [x] Aplicação dos limites de plano (produtos e kits)

**Unidades e insumos (seção 8.1 e 8.2)**
- [x] Unidade de estoque por produto, com quantidades decimais em todo o modelo
- [x] Conversões fixas entre unidades da mesma grandeza
- [x] Unidades alternativas de compra e de venda por produto, com fator de conversão
- [x] Produto vendável e/ou insumo
- [x] Composição com quantidades fracionadas e custo proporcional
- [x] Baixa da fração exata de cada componente na montagem — na venda ainda não existe (Fase 3)
- [x] Perda percentual por componente — Pro

**Tempo de preparo e produção (seção 8.3)** — removido do escopo (ver 8.3).

### Fase 3 — PDV e vendas (online)
- [x] Tela de PDV — painel de tickets com status (aberto/fechado/cancelado),
      filtro por status e detalhe do ticket selecionado ao lado, layout
      inspirado no gerenciador de pedidos do iFood
- [x] Venda com baixa de estoque — cada item **reserva** estoque ao ser
      adicionado ao ticket aberto (evita vender o que não tem) e a reserva
      só vira baixa de verdade no fechamento (pago); remover item ou
      cancelar o ticket libera a reserva. Kit reserva e debita só o próprio
      saldo — os componentes já foram debitados na montagem; não existe
      mais baixa "nos componentes" na venda, diferente do texto original
      deste item, por causa da unificação kit/montado da Fase 2 Etapa 3
- [x] Registro do preço e do custo no momento da venda em **todos os planos**
- [x] **Canal de origem** da venda (PDV, vitrine, marketplace) — só `pdv` é
      aceito por enquanto; vitrine e marketplace são Fases 10/11
- [ ] **Taxas do canal** na venda (comissão e frete)
- [x] UUID da venda gerado no frontend, com idempotência por venda (os itens
      não têm UUID próprio do cliente — a deduplicação acontece no nível da
      venda inteira, que já cobre reenvio)
- [x] Endpoint de venda idempotente
- [x] Datas `ocorrido_em` e `registrado_em`
- [x] Formas de pagamento — dinheiro/cartão/pix, podendo dividir uma venda em
      mais de uma forma
- [x] Venda fracionada (peso, volume, comprimento) e em unidades alternativas no PDV
- [x] Preço de tabela, desconto e preço final separados na venda
- [x] Limite de desconto por papel, com autorização acima do limite — Caixa
      10%, Gerente e Dono sem limite; ainda só ajustável no banco (sem tela
      de papéis editáveis)
- [x] **Cadastro de clientes** (seção 7.1), com UUID gerado no dispositivo
- [x] Cliente opcional na venda, busca rápida por telefone ou nome — inclui
      cadastro de cliente novo inline, direto no fluxo da venda
- [x] Histórico de compras na ficha do cliente e métricas por cliente —
      só conta vendas fechadas; métricas calculadas por agregação SQL
- [x] Mesclar clientes duplicados — preenche no sobrevivente só os campos
      vazios, reatribui as vendas do duplicado, nunca exclui (só marca
      como mesclado e some da listagem)
- [x] Exportar, corrigir e anonimizar dados de clientes (LGPD) — corrigir
      já existia desde o Bloco 1; exportar baixa um `.json`; anonimizar
      apaga dado pessoal mas mantém o registro e o vínculo com as vendas
- [x] Cancelamento de venda com estorno de estoque — `TipoMovimento.ESTORNO`
      novo; exige a permissão `vendas.cancelar` (Gerente e Dono, não
      Caixa); não estorna pagamento (sem integração de reembolso ainda)
- [x] Venda de compostos congelados até zerar o estoque

### Fase 4 — PDV offline
- [x] Frontend como PWA instalável — manifest + service worker mínimo
      (só cacheia a página de fallback `/offline`, sem cache agressivo de
      assets nem de API)
- [x] Cópia local de produtos, preços e estoque (IndexedDB) — só leitura
      por enquanto; ligada na página `/vendas`
- [ ] Atualização periódica da cópia local enquanto online — hoje só
      atualiza quando a página `/vendas` é carregada, não em intervalo
- [x] Fila local de vendas pendentes — cliente novo inline já funciona
      dentro da venda offline (mesmo padrão do PDV online); cliente
      *existente* não dá pra buscar offline (não cacheamos a lista) e
      movimentação de caixa avulsa (sem venda) ainda não existe
- [x] Indicador de status (online, offline, pendências)
- [x] Sincronização automática ao reconectar — em ordem, uma venda por
      vez; erro de rede para e tenta tudo de novo na próxima reconexão
      (sem duplicar); erro de negócio marca só aquele item e segue
- [x] Tratamento de conflitos conforme seção 5.4 — venda offline não passa
      pela reserva do PDV online (endpoint `POST /vendas/sincronizar`
      separado), debita direto permitindo saldo negativo; preço de cada
      item é o que o dispositivo tinha em cache, não o catálogo atual;
      cancelar antes de sincronizar só remove da fila local
- [x] Sessão offline do último usuário, com tempo limite — o service
      worker já serve `/offline` pra qualquer navegação sem rede (não tem
      "tela de login offline" separada porque não é necessária); usuário,
      papel e permissões cacheados no dispositivo pra saber quem parece
      estar logado e o que essa pessoa pode fazer, sem validar isso de
      verdade (a validação real é sempre do servidor, na sincronização).
      Tempo limite: decisão tomada de não ter limite por enquanto (falta
      uso real pra calibrar) — o texto "offline há X" já aparece, sem
      nenhum bloqueio
- [ ] Limite de caixas offline por plano (1 no Base, vários no Pro)
- [x] Fila pra entradas e saídas simples de caixa (seção 5.1) — entra no
      caixa aberto na hora de sincronizar; sem caixa aberto, fica marcada
      com o erro na fila

### Fase 5 — Financeiro
- [x] Caixa do dia: entradas e saídas (Base) — sessão de verdade (abre com
      valor inicial, fecha com conferência); abrir não é obrigatório pra
      vender, é oportunista: com caixa aberto, a venda vira lançamento; sem
      caixa, a venda funciona igual e simplesmente não gera lançamento
- [x] Contas a pagar e a receber (Pro) — sem integração com o caixa do dia
- [x] Fluxo de caixa projetado (Pro) — resultado líquido das contas abertas, sem saldo inicial
- [x] Integração automática vendas → lançamentos (inclusive vendas sincronizadas) —
      cobre tanto o fechamento online quanto a sincronização offline

### Fase 6 — Relatórios, gráficos e alertas
- [x] Resumo básico (Base) — Painel (`/`, só administrador): faturamento, ticket médio, por dia, mais vendidos, formas de pagamento; lucro só com `produtos.ver_custo`
- [ ] Margem esperada vs. real, histórico e por venda (Pro)
- [ ] Vendas e margem por canal (Pro)
- [x] Relatórios de clientes: ticket médio, recorrência, novos vs. recorrentes (Pro) — bloco no Painel
- [x] Impacto de descontos na margem (Pro) — bloco no Painel
- [x] Consumo e perdas de insumos no período (Pro) — montagens + baixas por ajuste, no Painel
- [x] Exportação em CSV das vendas (Pro) — botão no Painel
- [x] Gráficos no Painel: colunas por dia, barras dos mais vendidos e roscas (pagamento, clientes)
- [ ] Gráficos completos (Pro): linha de margem/lucro no tempo, comparação entre períodos
- [x] Alertas de estoque baixo e estoque negativo (Pro) — no Painel, com `estoque_minimo` por produto
- [ ] Alerta de margem caindo (Pro)
- [x] Avisos contextuais de upgrade com dados reais (Base) — descontos concedidos, no Painel
- [x] Aviso de proximidade de limite — produtos e kits, a partir de 80%

### Fase 7 — Assinaturas, cobrança e console da plataforma

**Cobrança (seção 9.3)**
- [ ] Módulo `pagamentos` com interface genérica e adaptador do provedor escolhido
- [ ] Checkout pelo provedor, sem dados de cartão no sistema
- [ ] Webhooks idempotentes em segundo plano, com registro dos eventos
- [ ] Faturas e pagamentos espelhados no banco
- [ ] Régua de cobrança (lembrete, atraso, carência, suspensão)
- [ ] Planos mensal e anual (com desconto)
- [ ] Transições de estado: trial → ativa → inadimplente → cancelada
- [ ] Período de carência por inadimplência
- [ ] Fluxo de downgrade: compostos, caixas offline, vitrine, marketplaces, cupons e fidelidade (seção 4.3)
- [ ] Reativação automática ao voltar para o Pro

**Console da plataforma (seções 9.1 e 9.2)**
- [ ] Aplicação `admin/` e rotas `/api/v1/plataforma`, com operadores separados, papéis internos e MFA
- [ ] Auditoria da plataforma
- [ ] Ficha do assinante: dados, plano, status, uso versus limites e última atividade
- [ ] Ações: trocar plano, estender trial, conceder carência, cortesia, suspender e reativar
- [ ] **Ajustes por empresa** no motor de planos, com validade e motivo
- [ ] Liberação temporária de acesso do suporte pelo assinante

### Fase 8 — CRM da plataforma e métricas
- [ ] Funil do assinante e linha do tempo de interações e eventos (seção 9.4)
- [ ] Tarefas, lembretes, tags e segmentos
- [ ] Motivo de cancelamento e pesquisa de saída
- [ ] Saúde da conta e indicador de risco de cancelamento
- [ ] Métricas: MRR, ARR, churn, conversão do trial, ARPA, LTV e coortes (seção 9.5)
- [ ] Uso de recursos por plano
- [ ] Avisos dentro do sistema e comunicados segmentados
- [ ] Cupons e descontos da assinatura do SaaS

### Fase 9 — Clientes: cupons, fidelidade e campanhas
- [ ] Cupons com regras de validade, valor mínimo, produtos, canais e limites (seção 7.4)
- [ ] Cupons com limite de uso apenas online; sem limite também offline
- [ ] Alerta de cupom que leva a venda abaixo do custo
- [ ] Fidelidade por cartão de carimbos
- [ ] Fidelidade por cashback, com saldo como livro de movimentações e expiração
- [ ] Estorno de fidelidade e de uso de cupom no cancelamento da venda
- [ ] Segmentação RFM recalculada em segundo plano, com faixas ajustáveis (seção 7.3)
- [ ] Aniversariantes e clientes inativos
- [ ] Campanhas: bonificar segmento com cashback, gerar cupom exclusivo, exportar lista para contato
- [ ] Respeito ao consentimento de marketing e exclusão de clientes de marketplaces

### Fase 10 — Vitrine online
- [ ] Aplicação `loja/` no monorepo, publicada na Vercel
- [ ] API pública separada, somente leitura, com limite de requisições
- [ ] Página da loja e página de produto, otimizadas para busca (SEO)
- [ ] Carrinho e finalização do pedido via WhatsApp
- [ ] Aplicação de cupons na vitrine
- [ ] Identificação do cliente pelo telefone, ligando o pedido ao cadastro
- [ ] Pedido pendente com reserva de estoque e expiração
- [ ] Confirmação do pedido no ERP (vira venda com canal "vitrine")
- [ ] Endereço padrão por loja
- [ ] Domínio próprio (Pro)
- [ ] Limite de produtos publicados por plano
- [ ] Textos e campos de apoio às obrigações legais

### Fase 11 — Marketplaces (etapa 1: vincular e sincronizar)
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

### Fase 12 — Fiscal (futuro)
- [ ] Entrada de notas (XML de compra → movimentação de estoque)
- [ ] Emissão de NF-e / NFC-e
- [ ] NFC-e em contingência offline, integrada à fila de sincronização
- [ ] CPF do cliente na nota a partir do cadastro
- [ ] Saída de notas

### Evoluções futuras
- [ ] Segundo marketplace (novo adaptador)
- [ ] Fila e ordens de produção para encomendas
- [ ] Integração com balança no PDV
- [ ] Pesquisa de satisfação (NPS) dos assinantes
- [ ] Integração com ferramenta externa de CRM de vendas, se decidido
- [ ] Fidelidade por pontos com catálogo de recompensas
- [ ] Envio automático de campanhas por WhatsApp ou e-mail
- [ ] Marketplaces etapa 2: criar e editar anúncios pelo ERP
- [ ] App desktop (Tauri ou Electron + SQLite) com acesso a impressora térmica e gaveta

---

## 12. Estrutura de pastas (referência)

```
erp/
├── backend/
│   ├── app/
│   │   ├── main.py            # API
│   │   ├── worker.py          # tarefas em segundo plano (a partir da Fase 7)
│   │   ├── core/              # config, database, security, tenancy, permissions, plans, exceptions
│   │   ├── shared/            # models base, money, pagination
│   │   └── modules/
│   │       ├── auth/
│   │       ├── empresas/
│   │       ├── usuarios/
│   │       ├── dispositivos/
│   │       ├── produtos/      # inclui unidades de medida e composição
│   │       ├── estoque/
│   │       ├── vendas/
│   │       ├── clientes/
│   │       ├── promocoes/     # cupons e campanhas
│   │       ├── fidelidade/
│   │       ├── financeiro/
│   │       ├── relatorios/
│   │       ├── assinaturas/
│   │       ├── pagamentos/
│   │       │   └── adaptadores/   # um por provedor de pagamento
│   │       ├── plataforma/    # operadores, console, CRM e métricas
│   │       ├── auditoria/
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
├── loja/                      # vitrine pública (Fase 10)
│   └── src/
└── admin/                     # console da plataforma (Fase 7)
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
