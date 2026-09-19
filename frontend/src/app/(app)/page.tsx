import { ROTULOS_FORMA } from "@/lib/formas-pagamento";
import Link from "next/link";
import { redirect } from "next/navigation";

import { GraficoBarras, GraficoColunas, GraficoRosca } from "@/components/graficos/graficos";
import { moeda, numero, porcentagem } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import type { Caixa, FluxoProjetado } from "@/modules/financeiro/types";
import type { Uso } from "@/modules/assinatura/types";
import type { AlertaEstoque } from "@/modules/estoque/types";
import type { Venda } from "@/modules/vendas/types";
import type { Resumo, ResumoClientes, ResumoDescontos, ResumoInsumos } from "@/modules/relatorios/types";

export const metadata = { title: "Painel · ERP" };

const PERIODOS = [
  { dias: 7, texto: "7 dias" },
  { dias: 30, texto: "30 dias" },
  { dias: 90, texto: "90 dias" },
];

/** AAAA-MM-DD no horário de Brasília, deslocado `dias` pra trás. */
function dataBrasilia(deslocamentoEmDias: number): string {
  const alvo = new Date(Date.now() - deslocamentoEmDias * 86_400_000);
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo" }).format(alvo);
}

/** Todos os dias de `inicio` a `fim` (AAAA-MM-DD), inclusive. */
function diasDoPeriodo(inicio: string, fim: string): string[] {
  const dias: string[] = [];
  const cursor = new Date(`${inicio}T00:00:00Z`);
  const limite = new Date(`${fim}T00:00:00Z`);
  while (cursor <= limite) {
    dias.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return dias;
}

function dataBr(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export default async function PainelPage({
  searchParams,
}: {
  searchParams: Promise<{ dias?: string }>;
}) {
  const eu = await obterEu();
  // O painel é só de administrador (quem tem `relatorios.ver`); os demais
  // perfis caem direto na primeira tela que podem usar.
  if (!eu.permissoes.includes("relatorios.ver")) {
    const destino = [
      ["vendas.ver", "/vendas"],
      ["estoque.ver", "/estoque"],
      ["produtos.ver", "/produtos"],
      ["clientes.ver", "/clientes"],
    ].find(([permissao]) => eu.permissoes.includes(permissao));
    if (destino) redirect(destino[1]);
    return (
      <div className="mx-auto max-w-3xl px-6 py-10 text-sm text-[#5b6b75]">
        Seu perfil ainda não tem acesso a nenhuma tela. Peça a um administrador para liberar.
      </div>
    );
  }

  const { dias: diasTexto } = await searchParams;
  const dias = PERIODOS.some((p) => String(p.dias) === diasTexto) ? Number(diasTexto) : 30;

  const hoje = dataBrasilia(0);
  const [resumo, resumoHoje, abertos, caixa, contas, alertas, clientes, uso, insumos, descontos] =
    await Promise.all([
    carregarDaSessao<Resumo>(`/relatorios/resumo?inicio=${dataBrasilia(dias - 1)}&fim=${hoje}`),
    carregarDaSessao<Resumo>(`/relatorios/resumo?inicio=${hoje}&fim=${hoje}`),
    carregarDaSessao<Venda[]>("/vendas?status=aberto&limite=200"),
    eu.permissoes.includes("financeiro.ver")
      ? carregarDaSessao<Caixa | null>("/caixa/aberto")
      : Promise.resolve(null),
    // Contas a pagar/receber são Pro: no Base a API recusa e o bloco some.
    carregarDaSessao<FluxoProjetado>("/contas/fluxo-projetado?dias=1").catch(() => null),
    // Alertas de estoque também são Pro.
    carregarDaSessao<AlertaEstoque[]>("/estoque/alertas").catch(() => null),
    // Relatório de clientes também é Pro.
    carregarDaSessao<ResumoClientes>(
      `/relatorios/clientes?inicio=${dataBrasilia(dias - 1)}&fim=${hoje}`,
    ).catch(() => null),
    // Uso dos limites do plano (avisos de proximidade e de upgrade, no Base).
    eu.plano === "pro"
      ? Promise.resolve(null)
      : carregarDaSessao<Uso>("/assinatura/uso").catch(() => null),
    // Consumo de insumos também é Pro.
    carregarDaSessao<ResumoInsumos>(
      `/relatorios/insumos?inicio=${dataBrasilia(dias - 1)}&fim=${hoje}`,
    ).catch(() => null),
    // Impacto de descontos na margem também é Pro.
    carregarDaSessao<ResumoDescontos>(
      `/relatorios/descontos?inicio=${dataBrasilia(dias - 1)}&fim=${hoje}`,
    ).catch(() => null),
  ]);

  // Só no Base: avisa quando um limite está perto de acabar e mostra, com o
  // dado real da empresa, o que o Pro entregaria.
  const avisosDoPlano: { chave: string; texto: string; critico: boolean }[] = [];
  if (eu.plano !== "pro") {
    for (const item of uso?.limites ?? []) {
      if (item.limite === null || item.percentual === null || Number(item.percentual) < 80) continue;
      const cheio = item.usado >= item.limite;
      avisosDoPlano.push({
        chave: item.chave,
        critico: cheio,
        texto: cheio
          ? `${item.rotulo}: você chegou ao limite do plano Base (${item.usado} de ${item.limite}). No Pro é ilimitado.`
          : `${item.rotulo}: você já usou ${item.usado} de ${item.limite} do plano Base (${Math.round(Number(item.percentual))}%). No Pro é ilimitado.`,
      });
    }
    if (Number(resumo.descontos) > 0) {
      avisosDoPlano.push({
        chave: "descontos",
        critico: false,
        texto: `Nos últimos ${dias} dias você concedeu ${moeda(resumo.descontos)} em descontos. No plano Pro você vê quanto da sua margem isso consumiu, por produto.`,
      });
    }
  }

  const faturamentoPorDia = new Map(resumo.por_dia.map((dia) => [dia.data, dia]));
  const pontosPorDia = diasDoPeriodo(resumo.inicio, resumo.fim).map((dia) => {
    const dado = faturamentoPorDia.get(dia);
    const valor = Number(dado?.faturamento ?? 0);
    return {
      rotulo: `${dia.slice(8)}/${dia.slice(5, 7)}`,
      valor,
      dica: `${dia.slice(8)}/${dia.slice(5, 7)}: ${moeda(valor)} · ${dado?.quantidade ?? 0} vendas`,
    };
  });

  const cartoes: { titulo: string; valor: string; destaque?: boolean }[] = [
    { titulo: "Faturamento", valor: moeda(resumo.faturamento), destaque: true },
    { titulo: "Vendas fechadas", valor: String(resumo.quantidade_vendas) },
    { titulo: "Ticket médio", valor: resumo.ticket_medio ? moeda(resumo.ticket_medio) : "—" },
  ];
  if (resumo.lucro_bruto !== null) {
    cartoes.push({
      titulo: "Lucro bruto",
      valor: `${moeda(resumo.lucro_bruto)}${
        resumo.margem_percentual ? ` · ${porcentagem(resumo.margem_percentual)}` : ""
      }`,
    });
  }
  cartoes.push(
    { titulo: "Descontos concedidos", valor: moeda(resumo.descontos) },
    { titulo: "Vendas canceladas", valor: String(resumo.cancelamentos) },
  );

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Painel</h1>
          <p className="mt-1 text-sm text-[#5b6b75]">
            Olá, {eu.usuario.nome.split(" ")[0]}. Aqui está o andamento do {eu.empresa.nome}.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {eu.plano === "pro" ? (
            <a
              href={`/relatorios/exportar?dias=${dias}`}
              className="rounded-md border border-[#dbe1e4] bg-white px-3.5 py-1.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
            >
              Exportar vendas (CSV)
            </a>
          ) : null}
          {PERIODOS.map((periodo) => (
            <Link
              key={periodo.dias}
              href={`/?dias=${periodo.dias}`}
              className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
                periodo.dias === dias
                  ? "border-[#0f6d5c] bg-[#0f6d5c] text-white"
                  : "border-[#dbe1e4] bg-white text-[#16222b] hover:border-[#0f6d5c]"
              }`}
            >
              {periodo.texto}
            </Link>
          ))}
        </div>
      </div>

      <section className="mt-8">
        <h2 className="font-medium text-[#16222b]">Agora</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link href="/vendas" className="rounded-lg border border-[#dbe1e4] bg-white p-4 hover:border-[#0f6d5c]">
            <p className="text-sm text-[#5b6b75]">Vendas hoje</p>
            <p className="mt-1 text-xl font-semibold tabular-nums text-[#16222b]">
              {moeda(resumoHoje.faturamento)}
            </p>
            <p className="text-sm text-[#5b6b75]">{resumoHoje.quantidade_vendas} fechadas</p>
          </Link>
          <Link href="/vendas" className="rounded-lg border border-[#dbe1e4] bg-white p-4 hover:border-[#0f6d5c]">
            <p className="text-sm text-[#5b6b75]">Tickets em aberto</p>
            <p className="mt-1 text-xl font-semibold tabular-nums text-[#16222b]">{abertos.length}</p>
            <p className="text-sm text-[#5b6b75]">aguardando fechar</p>
          </Link>
          {eu.permissoes.includes("financeiro.ver") ? (
            <Link href="/caixa" className="rounded-lg border border-[#dbe1e4] bg-white p-4 hover:border-[#0f6d5c]">
              <p className="text-sm text-[#5b6b75]">Caixa</p>
              <p className="mt-1 text-xl font-semibold text-[#16222b]">
                {caixa ? "Aberto" : "Fechado"}
              </p>
              <p className="text-sm text-[#5b6b75]">
                {caixa
                  ? `${caixa.aberto_por_nome ?? "—"} · ${moeda(caixa.resumo.saldo_esperado_dinheiro)} em dinheiro`
                  : "abra pela tela de Vendas"}
              </p>
            </Link>
          ) : null}
          {contas ? (
            <Link href="/contas" className="rounded-lg border border-[#dbe1e4] bg-white p-4 hover:border-[#0f6d5c]">
              <p className="text-sm text-[#5b6b75]">Contas vencidas</p>
              <p className="mt-1 text-xl font-semibold tabular-nums text-[#a33a2a]">
                {moeda(contas.atrasadas_a_pagar)}
              </p>
              <p className="text-sm text-[#5b6b75]">
                a pagar · {moeda(contas.atrasadas_a_receber)} a receber
              </p>
            </Link>
          ) : null}
        </div>
      </section>

      {avisosDoPlano.length > 0 ? (
        <section className="mt-8 space-y-3" aria-label="Avisos do plano">
          {avisosDoPlano.map((aviso) => (
            <div
              key={aviso.chave}
              className={`rounded-lg border px-4 py-3 text-sm ${
                aviso.critico
                  ? "border-[#e9b8ae] bg-[#fbe9e6] text-[#7d2a1b]"
                  : "border-[#ecd9a0] bg-[#fdf3d8] text-[#6b4c00]"
              }`}
            >
              {aviso.texto}
            </div>
          ))}
        </section>
      ) : null}

      {alertas ? (
        <section className="mt-8">
          <h2 className="font-medium text-[#16222b]">Alertas de estoque</h2>
          {alertas.length === 0 ? (
            <p className="mt-3 text-sm text-[#5b6b75]">Nenhum produto abaixo do mínimo nem negativo.</p>
          ) : (
            <ul className="mt-3 divide-y divide-[#dbe1e4] rounded-lg border border-[#dbe1e4] bg-white text-sm">
              {alertas.slice(0, 8).map((alerta) => (
                <li key={alerta.produto_id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      alerta.tipo === "negativo"
                        ? "bg-[#fbe9e6] text-[#a33a2a]"
                        : "bg-[#fdf3d8] text-[#8a6100]"
                    }`}
                  >
                    {alerta.tipo === "negativo" ? "Negativo" : "Baixo"}
                  </span>
                  <Link
                    href={`/produtos/${alerta.produto_id}/estoque`}
                    className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                  >
                    {alerta.nome}
                  </Link>
                  <span className="ml-auto tabular-nums text-[#5b6b75]">
                    {numero(alerta.disponivel, 2)} {alerta.unidade_codigo}
                    {alerta.estoque_minimo ? ` (mínimo ${numero(alerta.estoque_minimo, 2)})` : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {alertas.length > 8 ? (
            <p className="mt-2 text-sm text-[#5b6b75]">
              e mais {alertas.length - 8} — veja em{" "}
              <Link href="/estoque" className="text-[#0f6d5c] hover:underline">
                Estoque
              </Link>
              .
            </p>
          ) : null}
        </section>
      ) : null}

      <h2 className="mt-10 font-medium text-[#16222b]">
        Últimos {dias} dias · {dataBr(resumo.inicio)} a {dataBr(resumo.fim)}
      </h2>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cartoes.map((cartao) => (
          <div key={cartao.titulo} className="rounded-lg border border-[#dbe1e4] bg-white p-4">
            <p className="text-sm text-[#5b6b75]">{cartao.titulo}</p>
            <p
              className={`mt-1 font-semibold tabular-nums ${
                cartao.destaque ? "text-2xl text-[#0f6d5c]" : "text-xl text-[#16222b]"
              }`}
            >
              {cartao.valor}
            </p>
          </div>
        ))}
      </div>

      <section className="mt-10">
        <h2 className="font-medium text-[#16222b]">Faturamento por dia</h2>
        {resumo.quantidade_vendas === 0 ? (
          <p className="mt-3 text-sm text-[#5b6b75]">Nenhuma venda fechada neste período.</p>
        ) : (
          <div className="mt-3 rounded-lg border border-[#dbe1e4] bg-white p-4">
            <GraficoColunas pontos={pontosPorDia} />
          </div>
        )}
      </section>

      {clientes ? (
        <section className="mt-10">
          <h2 className="font-medium text-[#16222b]">Clientes no período</h2>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Compraram", String(clientes.clientes_que_compraram)],
              ["Novos", String(clientes.novos)],
              ["Recorrentes", String(clientes.recorrentes)],
              [
                "Compras por cliente",
                clientes.compras_por_cliente ? numero(clientes.compras_por_cliente, 1) : "—",
              ],
              [
                "Ticket médio (identificados)",
                clientes.ticket_medio ? moeda(clientes.ticket_medio) : "—",
              ],
              [
                "Vendas sem cliente",
                `${clientes.vendas_sem_cliente} · ${moeda(clientes.valor_sem_cliente)}`,
              ],
            ].map(([titulo, valor]) => (
              <div key={titulo} className="rounded-lg border border-[#dbe1e4] bg-white p-4">
                <p className="text-sm text-[#5b6b75]">{titulo}</p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-[#16222b]">{valor}</p>
              </div>
            ))}
          </div>
          {clientes.clientes_que_compraram > 0 ? (
            <div className="mt-4 rounded-lg border border-[#dbe1e4] bg-white p-4">
              <GraficoRosca
                centro={`${clientes.clientes_que_compraram} clientes`}
                fatias={[
                  { rotulo: "Novos", valor: clientes.novos, texto: String(clientes.novos) },
                  {
                    rotulo: "Recorrentes",
                    valor: clientes.recorrentes,
                    texto: String(clientes.recorrentes),
                  },
                ]}
                legendaCom="porcentagem"
              />
            </div>
          ) : null}
          {clientes.melhores.length > 0 ? (
            <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                  <tr>
                    <th className="px-4 py-3 font-medium">Melhores clientes</th>
                    <th className="px-4 py-3 text-right font-medium">Compras</th>
                    <th className="px-4 py-3 text-right font-medium">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#dbe1e4]">
                  {clientes.melhores.map((cliente) => (
                    <tr key={cliente.cliente_id}>
                      <td className="px-4 py-3">
                        <Link
                          href={`/clientes/${cliente.cliente_id}`}
                          className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                        >
                          {cliente.nome}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#5b6b75]">
                        {cliente.compras}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                        {moeda(cliente.valor)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      ) : null}

      {descontos ? (
        <section className="mt-10">
          <h2 className="font-medium text-[#16222b]">Impacto dos descontos</h2>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {(
              [
                [
                  "Descontos concedidos",
                  `${moeda(descontos.descontos)}${
                    descontos.percentual_de_desconto
                      ? ` · ${porcentagem(descontos.percentual_de_desconto)} da tabela`
                      : ""
                  }`,
                ],
                [
                  "Vendas com desconto",
                  `${descontos.vendas_com_desconto} (${descontos.itens_com_desconto} itens)`,
                ],
                descontos.lucro_sem_desconto !== null
                  ? [
                      "Lucro: sem desconto → com",
                      `${moeda(descontos.lucro_sem_desconto)} → ${moeda(descontos.lucro_com_desconto ?? 0)}`,
                    ]
                  : null,
                descontos.lucro_cedido_percentual
                  ? [
                      "Lucro cedido em desconto",
                      porcentagem(descontos.lucro_cedido_percentual),
                    ]
                  : null,
              ] as ([string, string] | null)[]
            )
              .filter((item): item is [string, string] => item !== null)
              .map(([titulo, valor]) => (
                <div key={titulo} className="rounded-lg border border-[#dbe1e4] bg-white p-4">
                  <p className="text-sm text-[#5b6b75]">{titulo}</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums text-[#16222b]">{valor}</p>
                </div>
              ))}
          </div>
          {descontos.produtos.length > 0 ? (
            <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                  <tr>
                    <th className="px-4 py-3 font-medium">Produtos com mais desconto</th>
                    <th className="px-4 py-3 text-right font-medium">Desconto</th>
                    <th className="px-4 py-3 text-right font-medium">% da tabela</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#dbe1e4]">
                  {descontos.produtos.map((item) => (
                    <tr key={item.produto_id}>
                      <td className="px-4 py-3 font-medium text-[#16222b]">{item.nome}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                        {moeda(item.desconto)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#5b6b75]">
                        {porcentagem(item.percentual)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      ) : null}

      {insumos && insumos.insumos.length > 0 ? (
        <section className="mt-10">
          <h2 className="font-medium text-[#16222b]">Consumo e perdas de insumos</h2>
          <p className="mt-1 text-sm text-[#5b6b75]">
            Consumido nas montagens (já com a perda percentual da composição) e baixado por
            ajuste de contagem para baixo, que indica perda ou divergência.
            {insumos.custo_total !== null
              ? ` Custo total no período: ${moeda(insumos.custo_total)}.`
              : ""}
          </p>
          <div className="mt-3 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Insumo</th>
                  <th className="px-4 py-3 text-right font-medium">Montagens</th>
                  <th className="px-4 py-3 text-right font-medium">Baixa por ajuste</th>
                  {insumos.custo_total !== null ? (
                    <th className="px-4 py-3 text-right font-medium">Custo</th>
                  ) : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {insumos.insumos.slice(0, 10).map((item) => (
                  <tr key={item.produto_id}>
                    <td className="px-4 py-3 font-medium text-[#16222b]">{item.nome}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                      {numero(item.consumido_em_montagens, 3)} {item.unidade_codigo}
                    </td>
                    <td
                      className={`px-4 py-3 text-right tabular-nums ${
                        Number(item.baixado_por_ajuste) > 0 ? "text-[#a33a2a]" : "text-[#5b6b75]"
                      }`}
                    >
                      {numero(item.baixado_por_ajuste, 3)} {item.unidade_codigo}
                    </td>
                    {item.custo_total !== null ? (
                      <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                        {moeda(item.custo_total)}
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="font-medium text-[#16222b]">Mais vendidos (por receita)</h2>
          {resumo.mais_vendidos.length === 0 ? (
            <p className="mt-3 text-sm text-[#5b6b75]">Sem vendas no período.</p>
          ) : (
            <div className="mt-3 rounded-lg border border-[#dbe1e4] bg-white p-4">
              <GraficoBarras
                barras={resumo.mais_vendidos.map((item) => ({
                  rotulo: item.nome,
                  valor: Number(item.receita),
                  texto: moeda(item.receita),
                  detalhe: `${numero(item.quantidade, 2)} ${item.unidade_codigo} vendidos`,
                }))}
              />
            </div>
          )}
        </section>

        <section>
          <h2 className="font-medium text-[#16222b]">Recebido por forma de pagamento</h2>
          {resumo.por_forma_pagamento.length === 0 ? (
            <p className="mt-3 text-sm text-[#5b6b75]">Sem recebimentos no período.</p>
          ) : (
            <div className="mt-3 rounded-lg border border-[#dbe1e4] bg-white p-4">
              <GraficoRosca
                centro={moeda(resumo.por_forma_pagamento.reduce((t, f) => t + Number(f.valor), 0))}
                legendaCom="porcentagem"
                fatias={resumo.por_forma_pagamento.map((item) => ({
                  rotulo: ROTULOS_FORMA[item.forma] ?? item.forma,
                  valor: Number(item.valor),
                  texto: moeda(item.valor),
                }))}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
