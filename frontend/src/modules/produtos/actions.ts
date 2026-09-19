"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { CustoAdicional, Produto, UnidadeAlternativa } from "./types";

function texto(dados: FormData, campo: string): string {
  return String(dados.get(campo) ?? "").trim();
}

function opcional(dados: FormData, campo: string): string | null {
  return texto(dados, campo) || null;
}

/** Caixa marcada envia "true" depois do hidden "false": vale o último. */
function booleano(dados: FormData, campo: string): boolean {
  const valores = dados.getAll(campo);
  return valores[valores.length - 1] === "true";
}

/** Zero (ou vazio) = sem estoque mínimo, ou seja, sem alerta de estoque baixo. */
function estoqueMinimo(dados: FormData): string | null {
  const valor = opcional(dados, "estoque_minimo");
  return valor !== null && Number(valor) > 0 ? valor : null;
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

export async function criarProduto(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const corpo = {
    nome: texto(dados, "nome"),
    unidade_codigo: texto(dados, "unidade_codigo"),
    tipo: texto(dados, "tipo") || "simples",
    sku: opcional(dados, "sku"),
    categoria_id: opcional(dados, "categoria_id"),
    preco_venda: texto(dados, "preco_venda") || "0",
    custo: texto(dados, "custo") || "0",
    vendavel: booleano(dados, "vendavel"),
    insumo: booleano(dados, "insumo"),
    controla_estoque: booleano(dados, "controla_estoque"),
    estoque_minimo: estoqueMinimo(dados),
    codigo_barras: opcional(dados, "codigo_barras"),
    descricao: opcional(dados, "descricao"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Produto>("/produtos", { metodo: "POST", corpo }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath("/produtos");
  redirect(`/produtos/${resultado.dados.id}`);
}

export async function atualizarProduto(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  // custo_medio só existe no formulário para quem tem produtos.ver_custo — se
  // não veio no envio, não é pra mexer nele (nunca zera por omissão).
  const custoMedio = opcional(dados, "custo_medio");

  const corpo = {
    nome: texto(dados, "nome"),
    sku: texto(dados, "sku"),
    unidade_codigo: texto(dados, "unidade_codigo"),
    categoria_id: opcional(dados, "categoria_id"),
    preco_venda: texto(dados, "preco_venda") || "0",
    ...(custoMedio !== null ? { custo_medio: custoMedio } : {}),
    vendavel: booleano(dados, "vendavel"),
    insumo: booleano(dados, "insumo"),
    controla_estoque: booleano(dados, "controla_estoque"),
    estoque_minimo: estoqueMinimo(dados),
    codigo_barras: opcional(dados, "codigo_barras"),
    descricao: opcional(dados, "descricao"),
    publicado_na_vitrine: booleano(dados, "publicado_na_vitrine"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Produto>(`/produtos/${produtoId}`, { metodo: "PATCH", corpo }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath("/produtos");
  revalidatePath(`/produtos/${produtoId}`);
  return { erro: "" };
}

export async function adicionarUnidade(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const corpo = {
    nome: texto(dados, "nome"),
    fator: texto(dados, "fator"),
    usa_na_compra: booleano(dados, "usa_na_compra"),
    usa_na_venda: booleano(dados, "usa_na_venda"),
  };

  if (!corpo.nome || !corpo.fator) {
    return { erro: "Informe o nome e o fator da unidade." };
  }

  const resultado = await comSessao(() =>
    chamarComSessao<UnidadeAlternativa>(`/produtos/${produtoId}/unidades`, {
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

export async function adicionarCustoAdicional(
  produtoId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const nome = texto(dados, "nome");
  const valor = texto(dados, "valor");
  if (!nome || !valor) {
    return { erro: "Informe o nome e o valor do custo adicional." };
  }

  const resultado = await comSessao(() =>
    chamarComSessao<CustoAdicional>(`/produtos/${produtoId}/custos-adicionais`, {
      metodo: "POST",
      corpo: { nome, valor },
    }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath(`/produtos/${produtoId}`);
  return { erro: "" };
}

export async function removerCustoAdicional(produtoId: string, custoId: string): Promise<void> {
  const resultado = await comSessao(() =>
    chamarComSessao(`/produtos/${produtoId}/custos-adicionais/${custoId}`, { metodo: "DELETE" }),
  );
  if (resultado.ok) {
    revalidatePath(`/produtos/${produtoId}`);
  }
}

export async function criarCategoria(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const nome = texto(dados, "nome");
  if (!nome) {
    return { erro: "Informe o nome da categoria." };
  }

  const resultado = await comSessao(() =>
    chamarComSessao("/categorias", { metodo: "POST", corpo: { nome } }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath("/produtos");
  return { erro: "" };
}
