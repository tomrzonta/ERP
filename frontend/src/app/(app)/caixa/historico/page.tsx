import Link from "next/link";

import { moeda } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import type { Caixa } from "@/modules/financeiro/types";

export const metadata = { title: "Histórico de caixas · ERP" };

const ROTULOS_STATUS: Record<string, string> = {
  aberto: "Aberto",
  fechado: "Fechado",
};

export default async function HistoricoCaixasPage() {
  const caixas = await carregarDaSessao<Caixa[]>("/caixa?limite=100");

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/caixa" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para o caixa do dia
      </Link>
      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[#16222b]">
        Histórico de caixas
      </h1>

      {caixas.length === 0 ? (
        <p className="mt-10 text-sm text-[#5b6b75]">Nenhum caixa foi aberto ainda.</p>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
              <tr>
                <th className="px-4 py-3 font-medium">Aberto em</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Aberto por</th>
                <th className="px-4 py-3 font-medium">Fechado por</th>
                <th className="px-4 py-3 text-right font-medium">Valor inicial</th>
                <th className="px-4 py-3 text-right font-medium">Entradas</th>
                <th className="px-4 py-3 text-right font-medium">Saídas</th>
                <th className="px-4 py-3 text-right font-medium">Diferença</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#dbe1e4]">
              {caixas.map((caixa) => (
                <tr key={caixa.id} className="transition-colors hover:bg-[#f7f8f8]">
                  <td className="px-4 py-3">
                    <Link
                      href={`/caixa/${caixa.id}`}
                      className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                    >
                      {new Date(caixa.aberto_em).toLocaleString("pt-BR")}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[#5b6b75]">
                    {ROTULOS_STATUS[caixa.status] ?? caixa.status}
                  </td>
                  <td className="px-4 py-3 text-[#16222b]">{caixa.aberto_por_nome ?? "—"}</td>
                  <td className="px-4 py-3 text-[#16222b]">
                    {caixa.status === "fechado" ? (caixa.fechado_por_nome ?? "—") : "—"}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                    {moeda(caixa.valor_inicial)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                    {moeda(caixa.resumo.total_entradas)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                    {moeda(caixa.resumo.total_saidas)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                    {caixa.resumo.diferenca !== null ? moeda(caixa.resumo.diferenca) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
