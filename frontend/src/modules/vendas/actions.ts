"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { FormaPagamento, StatusVenda, Venda } from "./types";

export type ClienteNovoPayload = {
  nome: string;
  telefone?: string;
};

export type ItemVendaPayload = {
  produto_id: string;
  quantidade: string;
  desconto_percentual: string;
};

export type PagamentoPayload = {
  forma: FormaPagamento;
  valor: string;
};

type Resultado = { ok: true; venda: Venda } | { ok: false; erro: string };

async function comSessao(acao: () => Promise<Venda>): Promise<Resultado> {
  try {
    const venda = await acao();
    revalidatePath("/vendas");
    return { ok: true, venda };
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    return { ok: false, erro: mensagemDoErro(erro) };
  }
}

/** Chamadas direto pelo painel de vendas — não são formulários nativos, o
 * carrinho e a seleção do ticket são estado local do cliente. */

export async function abrirVenda(payload: {
  cliente_id?: string | null;
  cliente_novo?: ClienteNovoPayload | null;
}): Promise<Resultado> {
  return comSessao(() => chamarComSessao<Venda>("/vendas", { metodo: "POST", corpo: payload }));
}

export async function adicionarItem(vendaId: string, item: ItemVendaPayload): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>(`/vendas/${vendaId}/itens`, { metodo: "POST", corpo: item }),
  );
}

export async function removerItem(vendaId: string, itemId: string): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>(`/vendas/${vendaId}/itens/${itemId}`, { metodo: "DELETE" }),
  );
}

export async function atualizarClienteDaVenda(
  vendaId: string,
  payload: { cliente_id?: string | null; cliente_novo?: ClienteNovoPayload | null },
): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>(`/vendas/${vendaId}/cliente`, { metodo: "PATCH", corpo: payload }),
  );
}

export async function fecharVenda(
  vendaId: string,
  pagamentos: PagamentoPayload[],
): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>(`/vendas/${vendaId}/fechar`, {
      metodo: "POST",
      corpo: { pagamentos },
    }),
  );
}

export async function cancelarVenda(vendaId: string): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>(`/vendas/${vendaId}/cancelar`, { metodo: "POST" }),
  );
}

export async function listarVendas(status?: StatusVenda): Promise<Venda[]> {
  const parametros = new URLSearchParams({ limite: "100" });
  if (status) parametros.set("status", status);
  return chamarComSessao<Venda[]>(`/vendas?${parametros}`);
}

/** Busca um ticket específico — usado quando se chega em `/vendas` com um
 * ticket que pode não estar entre os mais recentes já carregados. */
export async function obterVenda(vendaId: string): Promise<Venda | null> {
  try {
    return await chamarComSessao<Venda>(`/vendas/${vendaId}`);
  } catch {
    return null;
  }
}

export type ItemVendaOfflinePayload = {
  produto_id: string;
  quantidade: string;
  preco_tabela: string;
  desconto_percentual: string;
};

/** Envia uma venda feita offline, já completa — chamado pelo motor de
 * sincronização ao reconectar, um item da fila local por vez. */
export async function sincronizarVendaOffline(payload: {
  id: string;
  cliente_id?: string | null;
  cliente_novo?: ClienteNovoPayload | null;
  itens: ItemVendaOfflinePayload[];
  pagamentos: PagamentoPayload[];
  ocorrido_em: string;
}): Promise<Resultado> {
  return comSessao(() =>
    chamarComSessao<Venda>("/vendas/sincronizar", { metodo: "POST", corpo: payload }),
  );
}
