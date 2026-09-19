import { ROTULOS_FORMA } from "@/lib/formas-pagamento";
import Link from "next/link";

import { moeda } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { ResumoPorForma } from "@/modules/financeiro/components/resumo-por-forma";
import type { Caixa } from "@/modules/financeiro/types";

const ROTULOS_ORIGEM: Record<string, string> = {
  venda: "Venda",
  manual: "Manual",
};

export default async function CaixaDetalhePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const caixa = await carregarDaSessao<Caixa>(`/caixa/${id}`);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/caixa/historico" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para o histórico
      </Link>

      <div className="mt-4 flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
          Caixa de {new Date(caixa.aberto_em).toLocaleDateString("pt-BR")}
        </h1>
        <p className="text-sm text-[#5b6b75]">
          {caixa.status === "aberto" ? "Aberto" : "Fechado"}
        </p>
      </div>

      <p className="mt-3 text-sm text-[#5b6b75]">
        Aberto por {caixa.aberto_por_nome ?? "—"} em {new Date(caixa.aberto_em).toLocaleString("pt-BR")}
        {caixa.fechado_em
          ? ` · fechado por ${caixa.fechado_por_nome ?? "—"} em ${new Date(caixa.fechado_em).toLocaleString("pt-BR")}`
          : ""}
      </p>

      <dl className="mt-8 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-3">
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Valor inicial</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.valor_inicial)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Esperado em dinheiro</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.resumo.saldo_esperado_dinheiro)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Contado / Diferença</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {caixa.valor_contado !== null ? moeda(caixa.valor_contado) : "—"}
            {caixa.resumo.diferenca !== null ? (
              <span className="ml-2 text-sm text-[#5b6b75]">
                ({moeda(caixa.resumo.diferenca)})
              </span>
            ) : null}
          </dd>
        </div>
      </dl>

      {caixa.observacao ? (
        <p className="mt-4 text-sm text-[#5b6b75]">Observação: {caixa.observacao}</p>
      ) : null}

      <ResumoPorForma lancamentos={caixa.lancamentos} />

      <section className="mt-10">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Lançamentos</h2>
        {caixa.lancamentos.length > 0 ? (
          <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Hora</th>
                  <th className="px-4 py-3 font-medium">Origem</th>
                  <th className="px-4 py-3 font-medium">Forma</th>
                  <th className="px-4 py-3 font-medium">Descrição</th>
                  <th className="px-4 py-3 text-right font-medium">Valor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {caixa.lancamentos.map((lancamento) => (
                  <tr key={lancamento.id}>
                    <td className="px-4 py-3 tabular-nums text-[#5b6b75]">
                      {new Date(lancamento.ocorrido_em).toLocaleTimeString("pt-BR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-4 py-3 text-[#5b6b75]">
                      {ROTULOS_ORIGEM[lancamento.origem] ?? lancamento.origem}
                    </td>
                    <td className="px-4 py-3 text-[#5b6b75]">
                      {ROTULOS_FORMA[lancamento.forma_pagamento]}
                    </td>
                    <td className="px-4 py-3 text-[#5b6b75]">{lancamento.descricao ?? "—"}</td>
                    <td
                      className={`px-4 py-3 text-right tabular-nums ${
                        lancamento.tipo === "entrada" ? "text-[#0f6d5c]" : "text-[#a8341f]"
                      }`}
                    >
                      {lancamento.tipo === "entrada" ? "+" : "-"} {moeda(lancamento.valor)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[#5b6b75]">Nenhum lançamento neste caixa.</p>
        )}
      </section>
    </div>
  );
}
