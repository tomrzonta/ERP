"use client";

import { FORMAS_SELECIONAVEIS, ROTULOS_FORMA } from "@/lib/formas-pagamento";
import { InputNumero } from "@/components/ui/campo-numero";
import { useRef, useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { moeda } from "@/lib/formato";
import { fecharVenda } from "../actions";
import type { FormaPagamento, Venda } from "../types";

type LinhaPagamento = {
  chave: string;
  forma: FormaPagamento;
  valor: string;
};

export function FormularioFechamento({
  venda,
  aoFechar,
}: {
  venda: Venda;
  aoFechar: (venda: Venda) => void;
}) {
  const total = Number(venda.total);
  const proximoId = useRef(1);
  const [pagamentos, setPagamentos] = useState<LinhaPagamento[]>(() => [
    { chave: "p0", forma: "dinheiro", valor: total > 0 ? total.toFixed(2) : "" },
  ]);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  const somaPagamentos = pagamentos.reduce((soma, p) => soma + Number(p.valor || "0"), 0);
  const diferenca = Math.round((total - somaPagamentos) * 100) / 100;

  function atualizar(chave: string, campo: "forma" | "valor", valor: string) {
    setPagamentos((atual) => atual.map((p) => (p.chave === chave ? { ...p, [campo]: valor } : p)));
  }

  function adicionar() {
    const chave = `p${proximoId.current++}`;
    setPagamentos((atual) => [
      ...atual,
      { chave, forma: "dinheiro", valor: Math.max(total - somaPagamentos, 0).toFixed(2) },
    ]);
  }

  function remover(chave: string) {
    setPagamentos((atual) => atual.filter((p) => p.chave !== chave));
  }

  async function confirmar() {
    if (diferenca !== 0) {
      setErro("A soma dos pagamentos precisa bater com o total da venda.");
      return;
    }
    setErro("");
    setEnviando(true);
    const resultado = await fecharVenda(
      venda.id,
      pagamentos
        .filter((p) => Number(p.valor || "0") > 0)
        .map((p) => ({ forma: p.forma, valor: p.valor })),
    );
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoFechar(resultado.venda);
  }

  return (
    <div className="flex flex-col gap-3 rounded-md border border-[#dbe1e4] bg-white p-4">
      {pagamentos.map((pagamento) => (
        <div key={pagamento.chave} className="flex items-center gap-2">
          <select
            value={pagamento.forma}
            onChange={(evento) => atualizar(pagamento.chave, "forma", evento.target.value)}
            className="rounded-md border border-[#dbe1e4] bg-white px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          >
            {FORMAS_SELECIONAVEIS.map((forma) => (
              <option key={forma} value={forma}>
                {ROTULOS_FORMA[forma]}
              </option>
            ))}
          </select>
          <InputNumero formato="dinheiro"
            valor={pagamento.valor}
            aoMudar={(valorNovo) => atualizar(pagamento.chave, "valor", valorNovo)}
            classe="w-28 rounded-md border border-[#dbe1e4] px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          />
          {pagamentos.length > 1 ? (
            <button
              type="button"
              onClick={() => remover(pagamento.chave)}
              className="text-sm text-[#a8341f] hover:underline"
            >
              Remover
            </button>
          ) : null}
        </div>
      ))}
      <button
        type="button"
        onClick={adicionar}
        className="self-start text-sm text-[#0f6d5c] hover:underline"
      >
        + Dividir em outra forma de pagamento
      </button>

      <dl className="flex flex-col gap-1 border-t border-[#dbe1e4] pt-3 text-sm">
        <div className="flex justify-between">
          <dt className="text-[#5b6b75]">Total</dt>
          <dd className="font-medium tabular-nums text-[#16222b]">{moeda(total.toFixed(2))}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-[#5b6b75]">Pagamentos informados</dt>
          <dd className="tabular-nums text-[#16222b]">{moeda(somaPagamentos.toFixed(2))}</dd>
        </div>
        {diferenca !== 0 ? (
          <div className="flex justify-between text-[#a8341f]">
            <dt>Diferença</dt>
            <dd className="tabular-nums">{moeda(diferenca.toFixed(2))}</dd>
          </div>
        ) : null}
      </dl>

      {erro ? <Aviso>{erro}</Aviso> : null}

      <button
        type="button"
        disabled={enviando}
        onClick={confirmar}
        className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a] disabled:opacity-60"
      >
        {enviando ? "Fechando..." : "Fechar venda"}
      </button>
    </div>
  );
}
