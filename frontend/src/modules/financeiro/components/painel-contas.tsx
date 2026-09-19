"use client";

import { FORMAS_SELECIONAVEIS, ROTULOS_FORMA } from "@/lib/formas-pagamento";
import { InputNumero } from "@/components/ui/campo-numero";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { moeda } from "@/lib/formato";
import { cancelarConta, criarConta, darBaixaConta } from "../actions";
import type { Conta, FormaPagamento, StatusConta, TipoConta } from "../types";

type Filtro = "abertas" | "pagar" | "receber" | "encerradas";

const FILTROS: { valor: Filtro; texto: string }[] = [
  { valor: "abertas", texto: "Em aberto" },
  { valor: "pagar", texto: "A pagar" },
  { valor: "receber", texto: "A receber" },
  { valor: "encerradas", texto: "Pagas e canceladas" },
];

const ROTULOS_STATUS: Record<StatusConta, string> = {
  aberta: "Em aberto",
  paga: "Paga",
  cancelada: "Cancelada",
};

function dataBr(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

function passaNoFiltro(conta: Conta, filtro: Filtro): boolean {
  if (filtro === "encerradas") return conta.status !== "aberta";
  if (conta.status !== "aberta") return false;
  return filtro === "abertas" || conta.tipo === filtro;
}

export function PainelContas({ contas, podeOperar }: { contas: Conta[]; podeOperar: boolean }) {
  const router = useRouter();
  const [filtro, setFiltro] = useState<Filtro>("abertas");
  const [erro, setErro] = useState("");
  const [ocupada, setOcupada] = useState<string | null>(null);
  const [baixaEm, setBaixaEm] = useState<string | null>(null);
  const [formaBaixa, setFormaBaixa] = useState<FormaPagamento | "">("");

  const [tipo, setTipo] = useState<TipoConta>("pagar");
  const [descricao, setDescricao] = useState("");
  const [contraparte, setContraparte] = useState("");
  const [valor, setValor] = useState("");
  const [vencimento, setVencimento] = useState("");
  const [salvando, setSalvando] = useState(false);

  const visiveis = contas.filter((conta) => passaNoFiltro(conta, filtro));

  async function salvar() {
    setErro("");
    if (!descricao.trim() || !valor || Number(valor) <= 0 || !vencimento) {
      setErro("Informe descrição, valor maior que zero e vencimento.");
      return;
    }
    setSalvando(true);
    const resultado = await criarConta({ tipo, descricao, contraparte, valor, vencimento });
    setSalvando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    setDescricao("");
    setContraparte("");
    setValor("");
    router.refresh();
  }

  async function executar(
    id: string,
    acao: () => Promise<{ ok: true } | { ok: false; erro: string }>,
  ) {
    setErro("");
    setOcupada(id);
    const resultado = await acao();
    setOcupada(null);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    setBaixaEm(null);
    router.refresh();
  }

  return (
    <div className="mt-8 space-y-8">
      {podeOperar ? (
        <section className="rounded-lg border border-[#dbe1e4] bg-white p-5">
          <h2 className="font-medium text-[#16222b]">Nova conta</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <label className="flex flex-col gap-1.5 text-sm font-medium text-[#16222b]">
              Tipo
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value as TipoConta)}
                className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 font-normal"
              >
                <option value="pagar">A pagar</option>
                <option value="receber">A receber</option>
              </select>
            </label>
            <label className="flex flex-col gap-1.5 text-sm font-medium text-[#16222b] lg:col-span-2">
              Descrição
              <input
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                maxLength={255}
                className="rounded-md border border-[#dbe1e4] px-3 py-2.5 font-normal"
              />
            </label>
            <label className="flex flex-col gap-1.5 text-sm font-medium text-[#16222b]">
              Valor (R$)
              <InputNumero formato="dinheiro"
                valor={valor}
                aoMudar={(valorNovo) => setValor(valorNovo)}
                classe="rounded-md border border-[#dbe1e4] px-3 py-2.5 font-normal"
              />
            </label>
            <label className="flex flex-col gap-1.5 text-sm font-medium text-[#16222b]">
              Vencimento
              <input
                type="date"
                value={vencimento}
                onChange={(e) => setVencimento(e.target.value)}
                className="rounded-md border border-[#dbe1e4] px-3 py-2.5 font-normal"
              />
            </label>
            <label className="flex flex-col gap-1.5 text-sm font-medium text-[#16222b] sm:col-span-2 lg:col-span-3">
              {tipo === "pagar" ? "Fornecedor (opcional)" : "Cliente ou devedor (opcional)"}
              <input
                value={contraparte}
                onChange={(e) => setContraparte(e.target.value)}
                maxLength={120}
                className="rounded-md border border-[#dbe1e4] px-3 py-2.5 font-normal"
              />
            </label>
            <div className="flex items-end lg:col-span-2">
              <button
                type="button"
                onClick={salvar}
                disabled={salvando}
                className="rounded-md bg-[#0f6d5c] px-4 py-2.5 font-medium text-white hover:bg-[#0b564a] disabled:opacity-70"
              >
                {salvando ? "Salvando..." : "Adicionar conta"}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {erro ? <Aviso>{erro}</Aviso> : null}

      <section>
        <div className="flex flex-wrap gap-2">
          {FILTROS.map((item) => (
            <button
              key={item.valor}
              type="button"
              onClick={() => setFiltro(item.valor)}
              className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
                filtro === item.valor
                  ? "border-[#0f6d5c] bg-[#0f6d5c] text-white"
                  : "border-[#dbe1e4] bg-white text-[#16222b] hover:border-[#0f6d5c]"
              }`}
            >
              {item.texto}
            </button>
          ))}
        </div>

        {visiveis.length === 0 ? (
          <p className="mt-6 text-sm text-[#5b6b75]">Nenhuma conta nesta lista.</p>
        ) : (
          <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Vencimento</th>
                  <th className="px-4 py-3 font-medium">Descrição</th>
                  <th className="px-4 py-3 font-medium">Tipo</th>
                  <th className="px-4 py-3 text-right font-medium">Valor</th>
                  <th className="px-4 py-3 font-medium">Situação</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {visiveis.map((conta) => (
                  <tr key={conta.id}>
                    <td className="px-4 py-3 tabular-nums">{dataBr(conta.vencimento)}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-[#16222b]">{conta.descricao}</div>
                      {conta.contraparte ? (
                        <div className="text-[#5b6b75]">{conta.contraparte}</div>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-[#5b6b75]">
                      {conta.tipo === "pagar" ? "A pagar" : "A receber"}
                    </td>
                    <td
                      className={`px-4 py-3 text-right tabular-nums ${
                        conta.tipo === "pagar" ? "text-[#a33a2a]" : "text-[#0f6d5c]"
                      }`}
                    >
                      {moeda(conta.valor)}
                    </td>
                    <td className="px-4 py-3">
                      {conta.vencida ? (
                        <span className="font-medium text-[#a33a2a]">Vencida</span>
                      ) : (
                        ROTULOS_STATUS[conta.status]
                      )}
                      {conta.pago_em ? (
                        <div className="text-[#5b6b75]">
                          em {dataBr(conta.pago_em)}
                          {conta.forma_pagamento ? ` · ${ROTULOS_FORMA[conta.forma_pagamento]}` : ""}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {podeOperar && conta.status === "aberta" ? (
                        baixaEm === conta.id ? (
                          <div className="flex flex-wrap items-center justify-end gap-2">
                            <select
                              value={formaBaixa}
                              onChange={(e) => setFormaBaixa(e.target.value as FormaPagamento | "")}
                              className="rounded-md border border-[#dbe1e4] bg-white px-2 py-1.5"
                              aria-label="Forma de pagamento"
                            >
                              <option value="">Forma (opcional)</option>
                              {FORMAS_SELECIONAVEIS.map((forma) => (
                                <option key={forma} value={forma}>
                                  {ROTULOS_FORMA[forma]}
                                </option>
                              ))}
                            </select>
                            <button
                              type="button"
                              disabled={ocupada === conta.id}
                              onClick={() =>
                                executar(conta.id, () =>
                                  darBaixaConta(conta.id, formaBaixa === "" ? null : formaBaixa),
                                )
                              }
                              className="rounded-md bg-[#0f6d5c] px-3 py-1.5 font-medium text-white disabled:opacity-70"
                            >
                              Confirmar
                            </button>
                            <button
                              type="button"
                              onClick={() => setBaixaEm(null)}
                              className="text-[#5b6b75] hover:text-[#16222b]"
                            >
                              Voltar
                            </button>
                          </div>
                        ) : (
                          <div className="flex justify-end gap-3">
                            <button
                              type="button"
                              onClick={() => {
                                setBaixaEm(conta.id);
                                setFormaBaixa("");
                              }}
                              className="font-medium text-[#0f6d5c] hover:underline"
                            >
                              {conta.tipo === "pagar" ? "Marcar como paga" : "Marcar como recebida"}
                            </button>
                            <button
                              type="button"
                              disabled={ocupada === conta.id}
                              onClick={() => executar(conta.id, () => cancelarConta(conta.id))}
                              className="text-[#5b6b75] hover:text-[#a33a2a]"
                            >
                              Cancelar
                            </button>
                          </div>
                        )
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
