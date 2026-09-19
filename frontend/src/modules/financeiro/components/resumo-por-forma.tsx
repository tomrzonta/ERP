import { moeda } from "@/lib/formato";
import { FORMAS_SELECIONAVEIS, ROTULOS_FORMA, type FormaPagamento } from "@/lib/formas-pagamento";
import type { Lancamento } from "../types";

/** Saldo do caixa por forma de pagamento (entradas − saídas), pra conferir
 * gaveta, maquininha (crédito/débito) e Pix separadamente. */
export function ResumoPorForma({ lancamentos }: { lancamentos: Lancamento[] }) {
  const totais = new Map<FormaPagamento, number>();
  for (const lancamento of lancamentos) {
    const sinal = lancamento.tipo === "entrada" ? 1 : -1;
    totais.set(
      lancamento.forma_pagamento,
      (totais.get(lancamento.forma_pagamento) ?? 0) + sinal * Number(lancamento.valor),
    );
  }
  // As formas atuais sempre aparecem; a antiga só se houver movimento.
  const formas: FormaPagamento[] = [
    ...FORMAS_SELECIONAVEIS,
    ...(totais.has("cartao") ? (["cartao"] as const) : []),
  ];

  return (
    <dl className="mt-6 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-4">
      {formas.map((forma) => (
        <div key={forma} className="bg-white px-4 py-4">
          <dt className="text-sm text-[#5b6b75]">{ROTULOS_FORMA[forma]}</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(totais.get(forma) ?? 0)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
