"use client";

import { ROTULOS_FORMA } from "@/lib/formas-pagamento";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { moeda, numero } from "@/lib/formato";
import type { Cliente } from "@/modules/clientes/types";
import type { Produto } from "@/modules/produtos/types";
import { adicionarItem, cancelarVenda, removerItem } from "../actions";
import type { Venda } from "../types";
import { AtribuirCliente } from "./atribuir-cliente";
import { FormularioFechamento } from "./formulario-fechamento";
import type { ItemSelecionado } from "./modal-selecionar-produtos";
import { ModalSelecionarProdutos } from "./modal-selecionar-produtos";
import { SeloStatus } from "./selo-status";

export function DetalheVenda({
  venda,
  produtos,
  clientes,
  aoAtualizar,
  podeCancelarFechada = false,
}: {
  venda: Venda;
  produtos: Produto[];
  clientes: Cliente[];
  aoAtualizar: (venda: Venda) => void;
  /** Cancelar uma venda já fechada estorna estoque de verdade — mais
   * sensível que descartar um ticket em aberto, exige `vendas.cancelar`. */
  podeCancelarFechada?: boolean;
}) {
  const [modalAberto, setModalAberto] = useState(false);
  const [confirmandoCancelamento, setConfirmandoCancelamento] = useState(false);
  const [erro, setErro] = useState("");

  const produtosPorId = new Map(produtos.map((p) => [p.id, p]));
  const aberta = venda.status === "aberto";

  async function aoRemoverItem(itemId: string) {
    setErro("");
    const resultado = await removerItem(venda.id, itemId);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoAtualizar(resultado.venda);
  }

  async function aoAdicionarProdutos(itens: ItemSelecionado[]) {
    for (const item of itens) {
      const resultado = await adicionarItem(venda.id, {
        produto_id: item.produtoId,
        quantidade: item.quantidade,
        desconto_percentual: item.descontoPercentual,
      });
      if (!resultado.ok) return resultado;
      aoAtualizar(resultado.venda);
    }
    return { ok: true as const };
  }

  async function confirmarCancelamento() {
    setErro("");
    const resultado = await cancelarVenda(venda.id);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoAtualizar(resultado.venda);
    setConfirmandoCancelamento(false);
  }

  return (
    <div className="flex flex-col gap-6 rounded-lg border border-[#dbe1e4] bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#16222b]">Venda {venda.numero}</h2>
          <p className="mt-1 text-sm tabular-nums text-[#5b6b75]">
            Aberta em {new Date(venda.ocorrido_em).toLocaleString("pt-BR")}
          </p>
          {venda.fechado_em ? (
            <p className="text-sm tabular-nums text-[#5b6b75]">
              Fechada em {new Date(venda.fechado_em).toLocaleString("pt-BR")}
            </p>
          ) : null}
          {venda.cancelado_em ? (
            <p className="text-sm tabular-nums text-[#5b6b75]">
              Cancelada em {new Date(venda.cancelado_em).toLocaleString("pt-BR")}
            </p>
          ) : null}
        </div>
        <SeloStatus status={venda.status} />
      </div>

      <AtribuirCliente venda={venda} clientes={clientes} aoAtualizar={aoAtualizar} />

      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[#16222b]">Itens</h3>
          {aberta ? (
            <button
              type="button"
              onClick={() => setModalAberto(true)}
              className="text-sm text-[#0f6d5c] hover:underline"
            >
              + Adicionar produto
            </button>
          ) : null}
        </div>

        {venda.itens.length > 0 ? (
          <div className="mt-3 overflow-x-auto rounded-lg border border-[#dbe1e4]">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-3 py-2 font-medium">Produto</th>
                  <th className="px-3 py-2 text-right font-medium">Qtd.</th>
                  <th className="px-3 py-2 text-right font-medium">Total</th>
                  {aberta ? <th className="px-3 py-2" /> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {venda.itens.map((item) => (
                  <tr key={item.id}>
                    <td className="px-3 py-2 font-medium text-[#16222b]">
                      {produtosPorId.get(item.produto_id)?.nome ?? "Produto removido"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-[#5b6b75]">
                      {numero(item.quantidade, 4)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-[#16222b]">
                      {moeda((Number(item.preco_final) * Number(item.quantidade)).toFixed(2))}
                    </td>
                    {aberta ? (
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => aoRemoverItem(item.id)}
                          className="text-sm text-[#a8341f] hover:underline"
                        >
                          Remover
                        </button>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[#5b6b75]">Nenhum item ainda.</p>
        )}
      </div>

      <dl className="flex flex-col gap-1 border-t border-[#dbe1e4] pt-4 text-sm">
        <div className="flex justify-between">
          <dt className="text-[#5b6b75]">Subtotal</dt>
          <dd className="tabular-nums text-[#16222b]">{moeda(venda.subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-[#5b6b75]">Desconto</dt>
          <dd className="tabular-nums text-[#16222b]">{moeda(venda.desconto_total)}</dd>
        </div>
        <div className="flex justify-between text-base font-medium">
          <dt className="text-[#16222b]">Total</dt>
          <dd className="tabular-nums text-[#16222b]">{moeda(venda.total)}</dd>
        </div>
      </dl>

      {venda.status === "fechado" ? (
        <div>
          <h3 className="text-sm font-semibold text-[#16222b]">Pagamento</h3>
          <ul className="mt-3 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4]">
            {venda.pagamentos.map((pagamento) => (
              <li key={pagamento.id} className="flex justify-between px-3 py-2 text-sm">
                <span className="text-[#16222b]">
                  {ROTULOS_FORMA[pagamento.forma] ?? pagamento.forma}
                </span>
                <span className="tabular-nums text-[#5b6b75]">{moeda(pagamento.valor)}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {erro ? <Aviso>{erro}</Aviso> : null}

      {aberta ? (
        <>
          <FormularioFechamento venda={venda} aoFechar={aoAtualizar} />

          {!confirmandoCancelamento ? (
            <button
              type="button"
              onClick={() => setConfirmandoCancelamento(true)}
              className="self-start text-sm text-[#5b6b75] hover:text-[#a8341f]"
            >
              Cancelar venda
            </button>
          ) : (
            <div className="flex items-center gap-3 rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm">
              <span className="text-[#a8341f]">Cancelar este ticket e liberar as reservas?</span>
              <button
                type="button"
                onClick={confirmarCancelamento}
                className="font-medium text-[#a8341f] hover:underline"
              >
                Confirmar
              </button>
              <button
                type="button"
                onClick={() => setConfirmandoCancelamento(false)}
                className="text-[#5b6b75] hover:text-[#16222b]"
              >
                Voltar
              </button>
            </div>
          )}
        </>
      ) : null}

      {venda.status === "fechado" && podeCancelarFechada ? (
        <>
          {!confirmandoCancelamento ? (
            <button
              type="button"
              onClick={() => setConfirmandoCancelamento(true)}
              className="self-start text-sm text-[#5b6b75] hover:text-[#a8341f]"
            >
              Cancelar venda (estorna estoque)
            </button>
          ) : (
            <div className="flex items-center gap-3 rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm">
              <span className="text-[#a8341f]">
                Estorna o estoque de cada item e marca a venda como cancelada. Os pagamentos já
                registrados não são desfeitos automaticamente. Continuar?
              </span>
              <button
                type="button"
                onClick={confirmarCancelamento}
                className="font-medium text-[#a8341f] hover:underline"
              >
                Confirmar
              </button>
              <button
                type="button"
                onClick={() => setConfirmandoCancelamento(false)}
                className="text-[#5b6b75] hover:text-[#16222b]"
              >
                Voltar
              </button>
            </div>
          )}
        </>
      ) : null}

      <ModalSelecionarProdutos
        aberto={modalAberto}
        aoFechar={() => setModalAberto(false)}
        produtos={produtos}
        titulo="Adicionar produtos"
        textoConfirmar="Adicionar ao ticket"
        aoConfirmar={aoAdicionarProdutos}
      />
    </div>
  );
}
