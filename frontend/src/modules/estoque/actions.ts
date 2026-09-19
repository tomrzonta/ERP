"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Movimento } from "./types";

function texto(dados: FormData, campo: string): string {
  return String(dados.get(campo) ?? "").trim();
}

function opcional(dados: FormData, campo: string): string | null {
  return texto(dados, campo) || null;
}

async function comSessao<T>(
  acao: () => Promise<T>,
): Promise<{ ok: true; dados: T } | { ok: false; erro: string }> {
  try {
    return { ok: true, dados: await acao() };
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    return { ok: false, erro: mensagemDoErro(erro) };
  }
}

export async function registrarEntrada(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const quantidade = texto(dados, "quantidade");
  const custoUnitario = texto(dados, "custo_unitario");
  if (!quantidade || !custoUnitario) {
    return { erro: "Informe a quantidade e o custo da entrada." };
  }

  const corpo = {
    quantidade,
    custo_unitario: custoUnitario,
    unidade_id: opcional(dados, "unidade_id"),
    origem: opcional(dados, "origem"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Movimento>(`/estoque/produtos/${produtoId}/entradas`, {
      metodo: "POST",
      corpo,
    }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoId}/estoque`);
  revalidatePath("/estoque");
  return { erro: "" };
}

export async function registrarAjuste(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const quantidadeContada = texto(dados, "quantidade_contada");
  if (!quantidadeContada) {
    return { erro: "Informe a quantidade contada." };
  }

  const corpo = {
    quantidade_contada: quantidadeContada,
    origem: opcional(dados, "origem"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Movimento | null>(`/estoque/produtos/${produtoId}/ajustes`, {
      metodo: "POST",
      corpo,
    }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoId}/estoque`);
  revalidatePath("/estoque");
  return { erro: "" };
}
