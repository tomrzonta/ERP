"use client";

import { FORMAS_SELECIONAVEIS, ROTULOS_FORMA } from "@/lib/formas-pagamento";
import { InputNumero } from "@/components/ui/campo-numero";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { moeda } from "@/lib/formato";
import { fecharCaixa, lancarManual } from "../actions";
import { ResumoPorForma } from "./resumo-por-forma";
import type { Caixa, FormaPagamento, TipoLancamento } from "../types";

const ROTULOS_ORIGEM: Record<string, string> = {
  venda: "Venda",
  manual: "Manual",
};

export function PainelCaixaAberto({ caixa }: { caixa: Caixa }) {
  const router = useRouter();

  const [tipo, setTipo] = useState<TipoLancamento>("entrada");
  const [valor, setValor] = useState("");
  const [forma, setForma] = useState<FormaPagamento>("dinheiro");
  const [descricao, setDescricao] = useState("");
  const [enviandoLancamento, setEnviandoLancamento] = useState(false);
  const [erroLancamento, setErroLancamento] = useState("");

  const [fechando, setFechando] = useState(false);
  const [valorContado, setValorContado] = useState("");
  const [enviandoFechamento, setEnviandoFechamento] = useState(false);
  const [erroFechamento, setErroFechamento] = useState("");

  async function registrarLancamento() {
    setErroLancamento("");
    if (!valor || Number(valor) <= 0) {
      setErroLancamento("Informe um valor maior que zero.");
      return;
    }
    setEnviandoLancamento(true);
    const resultado = await lancarManual(caixa.id, {
      tipo,
      valor,
      forma_pagamento: forma,
      descricao: descricao || undefined,
    });
    setEnviandoLancamento(false);
    if (!resultado.ok) {
      setErroLancamento(resultado.erro);
      return;
    }
    setValor("");
    setDescricao("");
    router.refresh();
  }

  const diferencaEstimada =
    valorContado !== ""
      ? Math.round((Number(valorContado) - Number(caixa.resumo.saldo_esperado_dinheiro)) * 100) /
        100
      : null;

  async function confirmarFechamento() {
    setErroFechamento("");
    if (valorContado === "" || Number(valorContado) < 0) {
      setErroFechamento("Informe quanto foi contado na gaveta.");
      return;
    }
    setEnviandoFechamento(true);
    const resultado = await fecharCaixa(caixa.id, valorContado);
    setEnviandoFechamento(false);
    if (!resultado.ok) {
      setErroFechamento(resultado.erro);
      return;
    }
    router.refresh();
  }

  return (
    <div className="flex flex-col gap-8">
      <dl className="grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-4">
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Valor inicial</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.valor_inicial)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Entradas</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.resumo.total_entradas)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Saídas</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.resumo.total_saidas)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Esperado em dinheiro</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(caixa.resumo.saldo_esperado_dinheiro)}
          </dd>
        </div>
      </dl>

      <ResumoPorForma lancamentos={caixa.lancamentos} />

      <section>
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
                    <td className="px-4 py-3 text-[#5b6b75]">{ROTULOS_FORMA[lancamento.forma_pagamento]}</td>
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
          <p className="mt-3 text-sm text-[#5b6b75]">Nenhum lançamento ainda.</p>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
          Lançar entrada ou saída
        </h2>
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoLancamento)}
            className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          >
            <option value="entrada">Entrada</option>
            <option value="saida">Saída</option>
          </select>
          <select
            value={forma}
            onChange={(e) => setForma(e.target.value as FormaPagamento)}
            className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          >
            {FORMAS_SELECIONAVEIS.map((f) => (
              <option key={f} value={f}>
                {ROTULOS_FORMA[f]}
              </option>
            ))}
          </select>
          <InputNumero formato="dinheiro"
            valor={valor}
            aoMudar={(valorNovo) => setValor(valorNovo)}
            placeholder="Valor"
            classe="w-32 rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          />
          <input
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Descrição (opcional)"
            className="w-full max-w-xs rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          />
          <button
            type="button"
            disabled={enviandoLancamento}
            onClick={registrarLancamento}
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a] disabled:opacity-60"
          >
            {enviandoLancamento ? "Lançando..." : "Lançar"}
          </button>
        </div>
        {erroLancamento ? (
          <div className="mt-3">
            <Aviso>{erroLancamento}</Aviso>
          </div>
        ) : null}
      </section>

      <section className="border-t border-[#dbe1e4] pt-8">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Fechar caixa</h2>
        {!fechando ? (
          <button
            type="button"
            onClick={() => setFechando(true)}
            className="mt-4 rounded-md border border-[#dbe1e4] bg-white px-4 py-2.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
          >
            Conferir e fechar
          </button>
        ) : (
          <div className="mt-4 flex max-w-sm flex-col gap-3">
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-[#16222b]">Valor contado na gaveta</span>
              <InputNumero formato="dinheiro"
                valor={valorContado}
                aoMudar={(valorNovo) => setValorContado(valorNovo)}
                classe="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none focus:border-[#0f6d5c]"
              />
            </label>
            {diferencaEstimada !== null ? (
              <p
                className={`text-sm ${
                  diferencaEstimada === 0
                    ? "text-[#5b6b75]"
                    : diferencaEstimada > 0
                      ? "text-[#0f6d5c]"
                      : "text-[#a8341f]"
                }`}
              >
                {diferencaEstimada === 0
                  ? "Bate certinho com o esperado."
                  : `Diferença: ${moeda(diferencaEstimada.toFixed(2))} ${diferencaEstimada > 0 ? "a mais" : "a menos"}.`}
              </p>
            ) : null}
            {erroFechamento ? <Aviso>{erroFechamento}</Aviso> : null}
            <div className="flex gap-3">
              <button
                type="button"
                disabled={enviandoFechamento}
                onClick={confirmarFechamento}
                className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a] disabled:opacity-60"
              >
                {enviandoFechamento ? "Fechando..." : "Confirmar fechamento"}
              </button>
              <button
                type="button"
                onClick={() => setFechando(false)}
                className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
