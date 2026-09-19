"use client";

import { useEffect, useMemo, useState } from "react";

import { moeda } from "@/lib/formato";
import type { Cliente } from "@/modules/clientes/types";
import type { Produto } from "@/modules/produtos/types";
import { abrirVenda, adicionarItem, obterVenda } from "../actions";
import type { StatusVenda, Venda } from "../types";
import { DetalheVenda } from "./detalhe-venda";
import type { ItemSelecionado } from "./modal-selecionar-produtos";
import { ModalSelecionarProdutos } from "./modal-selecionar-produtos";
import { SeloStatus } from "./selo-status";

type Filtro = "todos" | StatusVenda;

const ABAS: { valor: Filtro; texto: string }[] = [
  { valor: "todos", texto: "Todos" },
  { valor: "aberto", texto: "Abertos" },
  { valor: "fechado", texto: "Fechados" },
  { valor: "cancelado", texto: "Cancelados" },
];

export function PainelVendas({
  vendasIniciais,
  produtos,
  clientes,
  podeRegistrar,
  podeCancelarFechada,
  ticketInicial,
}: {
  vendasIniciais: Venda[];
  produtos: Produto[];
  clientes: Cliente[];
  podeRegistrar: boolean;
  podeCancelarFechada: boolean;
  /** Ticket pra abrir já selecionado (ex.: vindo do histórico do cliente) —
   * pode não estar entre os mais recentes já carregados. */
  ticketInicial?: string;
}) {
  const [vendas, setVendas] = useState<Venda[]>(vendasIniciais);
  const [filtro, setFiltro] = useState<Filtro>(ticketInicial ? "todos" : "aberto");
  const [selecionadaId, setSelecionadaId] = useState<string | null>(
    ticketInicial ?? vendasIniciais[0]?.id ?? null,
  );
  const [modalAberto, setModalAberto] = useState(false);

  useEffect(() => {
    if (!ticketInicial) return;
    if (vendasIniciais.some((v) => v.id === ticketInicial)) return;
    obterVenda(ticketInicial).then((venda) => {
      if (venda) setVendas((atual) => [venda, ...atual]);
    });
    // Só precisa buscar uma vez, ao chegar com um ticket que não veio na carga inicial.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nomesPorCliente = new Map(clientes.map((c) => [c.id, c.nome]));

  function atualizarVenda(venda: Venda) {
    setVendas((atual) => {
      const existe = atual.some((v) => v.id === venda.id);
      if (existe) return atual.map((v) => (v.id === venda.id ? venda : v));
      return [venda, ...atual];
    });
    setSelecionadaId(venda.id);
  }

  const contagens = useMemo(() => {
    return {
      todos: vendas.length,
      aberto: vendas.filter((v) => v.status === "aberto").length,
      fechado: vendas.filter((v) => v.status === "fechado").length,
      cancelado: vendas.filter((v) => v.status === "cancelado").length,
    };
  }, [vendas]);

  const listados = useMemo(() => {
    const filtrados = filtro === "todos" ? vendas : vendas.filter((v) => v.status === filtro);
    return [...filtrados].sort(
      (a, b) => new Date(b.ocorrido_em).getTime() - new Date(a.ocorrido_em).getTime(),
    );
  }, [vendas, filtro]);

  const selecionada = vendas.find((v) => v.id === selecionadaId) ?? null;

  async function aoIniciarVenda(itens: ItemSelecionado[]) {
    const aberta = await abrirVenda({});
    if (!aberta.ok) return aberta;
    atualizarVenda(aberta.venda);

    for (const item of itens) {
      const resultado = await adicionarItem(aberta.venda.id, {
        produto_id: item.produtoId,
        quantidade: item.quantidade,
        desconto_percentual: item.descontoPercentual,
      });
      if (!resultado.ok) return resultado;
      atualizarVenda(resultado.venda);
    }
    return { ok: true as const };
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {ABAS.map((aba) => (
            <button
              key={aba.valor}
              type="button"
              onClick={() => setFiltro(aba.valor)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                filtro === aba.valor
                  ? "bg-[#16222b] text-white"
                  : "bg-[#f7f8f8] text-[#5b6b75] hover:bg-[#dbe1e4]"
              }`}
            >
              {aba.texto}{" "}
              <span className="tabular-nums opacity-70">({contagens[aba.valor]})</span>
            </button>
          ))}
        </div>
        {podeRegistrar ? (
          <button
            type="button"
            onClick={() => setModalAberto(true)}
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            + Iniciar venda
          </button>
        ) : null}
      </div>

      <div className="mt-6 flex flex-col gap-6 lg:flex-row">
        <div className="flex w-full flex-col gap-3 lg:max-w-sm">
          {listados.length === 0 ? (
            <p className="mt-4 text-sm text-[#5b6b75]">Nenhuma venda nesse status.</p>
          ) : (
            listados.map((venda) => (
              <button
                key={venda.id}
                type="button"
                onClick={() => setSelecionadaId(venda.id)}
                className={`rounded-lg border px-4 py-3 text-left transition-colors ${
                  venda.id === selecionadaId
                    ? "border-[#0f6d5c] bg-[#0f6d5c]/5"
                    : "border-[#dbe1e4] bg-white hover:border-[#0f6d5c]/40"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-[#16222b]">{venda.numero}</span>
                  <SeloStatus status={venda.status} />
                </div>
                <div className="mt-1 flex items-center justify-between gap-2 text-sm text-[#5b6b75]">
                  <span>
                    {venda.cliente_id ? (nomesPorCliente.get(venda.cliente_id) ?? "—") : "Balcão"}
                  </span>
                  <span className="tabular-nums font-medium text-[#16222b]">
                    {moeda(venda.total)}
                  </span>
                </div>
                <p className="mt-1 text-xs tabular-nums text-[#5b6b75]">
                  {new Date(venda.ocorrido_em).toLocaleString("pt-BR")}
                </p>
              </button>
            ))
          )}
        </div>

        <div className="flex-1">
          {selecionada ? (
            <DetalheVenda
              venda={selecionada}
              produtos={produtos}
              clientes={clientes}
              aoAtualizar={atualizarVenda}
              podeCancelarFechada={podeCancelarFechada}
            />
          ) : (
            <p className="text-sm text-[#5b6b75]">Selecione uma venda pra ver os detalhes.</p>
          )}
        </div>
      </div>

      <ModalSelecionarProdutos
        aberto={modalAberto}
        aoFechar={() => setModalAberto(false)}
        produtos={produtos}
        titulo="Iniciar venda"
        textoConfirmar="Iniciar ticket"
        aoConfirmar={aoIniciarVenda}
      />
    </div>
  );
}
