"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Caixa, Conta, FormaPagamento, TipoConta, TipoLancamento } from "./types";

async function comSessaoConta(
  acao: () => Promise<Conta>,
): Promise<{ ok: true; conta: Conta } | { ok: false; erro: string }> {
  try {
    const conta = await acao();
    revalidatePath("/contas");
    return { ok: true, conta };
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    return { ok: false, erro: mensagemDoErro(erro) };
  }
}

export async function criarConta(payload: {
  tipo: TipoConta;
  descricao: string;
  contraparte?: string;
  valor: string;
  vencimento: string;
}) {
  return comSessaoConta(() =>
    chamarComSessao<Conta>("/contas", {
      metodo: "POST",
      corpo: { ...payload, contraparte: payload.contraparte || null },
    }),
  );
}

export async function darBaixaConta(contaId: string, formaPagamento: FormaPagamento | null) {
  return comSessaoConta(() =>
    chamarComSessao<Conta>(`/contas/${contaId}/baixa`, {
      metodo: "POST",
      corpo: { forma_pagamento: formaPagamento },
    }),
  );
}

export async function cancelarConta(contaId: string) {
  return comSessaoConta(() =>
    chamarComSessao<Conta>(`/contas/${contaId}/cancelar`, { metodo: "POST" }),
  );
}

async function comSessao(
  acao: () => Promise<Caixa>,
): Promise<{ ok: true; caixa: Caixa } | { ok: false; erro: string }> {
  try {
    const caixa = await acao();
    revalidatePath("/caixa");
    revalidatePath("/caixa/historico");
    revalidatePath("/vendas");
    return { ok: true, caixa };
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    return { ok: false, erro: mensagemDoErro(erro) };
  }
}

export async function abrirCaixa(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const valorInicial = String(dados.get("valor_inicial") ?? "0").trim() || "0";
  const observacao = String(dados.get("observacao") ?? "").trim() || null;

  const resultado = await comSessao(() =>
    chamarComSessao<Caixa>("/caixa/abrir", {
      metodo: "POST",
      corpo: { valor_inicial: valorInicial, observacao },
    }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }
  return { erro: "" };
}

export async function fecharCaixa(
  caixaId: string,
  valorContado: string,
  observacao?: string,
): Promise<{ ok: true; caixa: Caixa } | { ok: false; erro: string }> {
  return comSessao(() =>
    chamarComSessao<Caixa>(`/caixa/${caixaId}/fechar`, {
      metodo: "POST",
      corpo: { valor_contado: valorContado, observacao: observacao || null },
    }),
  );
}

export async function lancarManual(
  caixaId: string,
  payload: {
    tipo: TipoLancamento;
    valor: string;
    forma_pagamento: FormaPagamento;
    descricao?: string;
  },
): Promise<{ ok: true; caixa: Caixa } | { ok: false; erro: string }> {
  return comSessao(() =>
    chamarComSessao<Caixa>(`/caixa/${caixaId}/lancamentos`, { metodo: "POST", corpo: payload }),
  );
}

/** Envia uma entrada/saída de caixa feita offline — chamado pelo motor de
 * sincronização, uma por vez. */
export async function sincronizarLancamentoOffline(payload: {
  id: string;
  tipo: TipoLancamento;
  valor: string;
  forma_pagamento: FormaPagamento;
  descricao: string | null;
  ocorrido_em: string;
}): Promise<{ ok: true } | { ok: false; erro: string }> {
  try {
    await chamarComSessao("/caixa/lancamentos/sincronizar", { metodo: "POST", corpo: payload });
    revalidatePath("/caixa");
    return { ok: true };
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    return { ok: false, erro: mensagemDoErro(erro) };
  }
}
