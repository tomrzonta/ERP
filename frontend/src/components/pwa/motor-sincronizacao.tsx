"use client";

import { useEffect, useRef } from "react";

import {
  listarLancamentosPendentes,
  listarVendasPendentes,
  marcarLancamentoPendenteComErro,
  marcarVendaPendenteComErro,
  removerLancamentoPendente,
  removerVendaPendente,
  type LancamentoPendente,
  type VendaPendente,
} from "@/lib/client/banco-local";
import { sincronizarLancamentoOffline } from "@/modules/financeiro/actions";
import { sincronizarVendaOffline } from "@/modules/vendas/actions";

export const EVENTO_FILA_ATUALIZADA = "erp:fila-vendas-atualizada";

export function avisarFilaAtualizada() {
  window.dispatchEvent(new Event(EVENTO_FILA_ATUALIZADA));
}

async function sincronizarUma(venda: VendaPendente): Promise<void> {
  const resultado = await sincronizarVendaOffline({
    id: venda.id,
    cliente_id: venda.clienteId,
    cliente_novo: venda.clienteNovo,
    itens: venda.itens.map((item) => ({
      produto_id: item.produtoId,
      quantidade: item.quantidade,
      preco_tabela: item.precoTabela,
      desconto_percentual: item.descontoPercentual,
    })),
    pagamentos: venda.pagamentos,
    ocorrido_em: venda.ocorridoEm,
  });
  if (resultado.ok) {
    await removerVendaPendente(venda.id);
  } else {
    // Chegou no servidor mas foi recusada (regra de negócio) — marca o
    // motivo e segue pras próximas. Se a chamada nem chegasse a completar
    // (sem rede), ela teria lançado e caído no catch de sincronizarFila,
    // sem marcar nada — só tenta de novo na próxima reconexão.
    await marcarVendaPendenteComErro(venda.id, resultado.erro);
  }
}

async function sincronizarUmLancamento(item: LancamentoPendente): Promise<void> {
  const resultado = await sincronizarLancamentoOffline({
    id: item.id,
    tipo: item.tipo,
    valor: item.valor,
    forma_pagamento: item.formaPagamento,
    descricao: item.descricao,
    ocorrido_em: item.ocorridoEm,
  });
  if (resultado.ok) {
    await removerLancamentoPendente(item.id);
  } else {
    await marcarLancamentoPendenteComErro(item.id, resultado.erro);
  }
}

/** Roda em segundo plano: sempre que a conexão volta, envia a fila local de
 * vendas offline, uma por vez, em ordem. Não renderiza nada. Montado tanto
 * no layout autenticado quanto na página /offline, pra cobrir os dois
 * lugares de onde a reconexão pode acontecer. */
export function MotorSincronizacao() {
  const sincronizando = useRef(false);

  useEffect(() => {
    async function sincronizarFila() {
      if (sincronizando.current || !navigator.onLine) return;
      sincronizando.current = true;
      try {
        const pendentes = await listarVendasPendentes();
        for (const venda of pendentes) {
          if (!navigator.onLine) break;
          await sincronizarUma(venda);
          avisarFilaAtualizada();
        }
        // Vendas primeiro: elas é que geram lançamento automático no caixa;
        // depois as entradas/saídas avulsas, também em ordem.
        const lancamentos = await listarLancamentosPendentes();
        for (const item of lancamentos) {
          if (!navigator.onLine) break;
          await sincronizarUmLancamento(item);
          avisarFilaAtualizada();
        }
      } catch {
        // Falha de rede no meio da fila: só para por aqui. O que já foi
        // enviado saiu da fila; o resto tenta de novo na próxima reconexão.
      } finally {
        sincronizando.current = false;
      }
    }

    sincronizarFila();
    window.addEventListener("online", sincronizarFila);
    return () => window.removeEventListener("online", sincronizarFila);
  }, []);

  return null;
}
