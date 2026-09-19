"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Componente } from "./types";

function texto(dados: FormData, campo: string): string {
  return String(dados.get(campo) ?? "").trim();
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

export async function adicionarComponente(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const componenteId = texto(dados, "componente_id");
  const quantidade = texto(dados, "quantidade");
  if (!componenteId || !quantidade) {
    return { erro: "Escolha o componente e a quantidade." };
  }

  const corpo = {
    componente_id: componenteId,
    quantidade,
    perda_percentual: texto(dados, "perda_percentual") || "0",
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Componente>(`/produtos/${produtoId}/componentes`, {
      metodo: "POST",
      corpo,
    }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoId}`);
  return { erro: "" };
}

export async function criarInsumoEAdicionar(
  produtoCompostoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const nome = texto(dados, "nome");
  const unidadeCodigo = texto(dados, "unidade_codigo");
  const quantidade = texto(dados, "quantidade");
  if (!nome || !unidadeCodigo || !quantidade) {
    return { erro: "Informe o nome, a unidade e a quantidade." };
  }

  const resultado = await comSessao(async () => {
    const insumo = await chamarComSessao<{ id: string }>("/produtos", {
      metodo: "POST",
      corpo: {
        nome,
        unidade_codigo: unidadeCodigo,
        tipo: "simples",
        vendavel: false,
        insumo: true,
        custo: texto(dados, "custo") || "0",
      },
    });
    return chamarComSessao<Componente>(`/produtos/${produtoCompostoId}/componentes`, {
      metodo: "POST",
      corpo: { componente_id: insumo.id, quantidade, perda_percentual: "0" },
    });
  });
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoCompostoId}`);
  return { erro: "" };
}

export async function removerComponente(produtoId: string, componenteId: string): Promise<void> {
  const resultado = await comSessao(() =>
    chamarComSessao(`/produtos/${produtoId}/componentes/${componenteId}`, { metodo: "DELETE" }),
  );
  if (resultado.ok) {
    revalidatePath(`/produtos/${produtoId}`);
  }
}

export async function montar(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const quantidade = texto(dados, "quantidade");
  if (!quantidade) {
    return { erro: "Informe a quantidade a montar." };
  }

  const corpo = {
    quantidade,
    origem: texto(dados, "origem") || null,
  };

  const resultado = await comSessao(() =>
    chamarComSessao(`/produtos/${produtoId}/montagens`, { metodo: "POST", corpo }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoId}/estoque`);
  revalidatePath("/estoque");
  return { erro: "" };
}
