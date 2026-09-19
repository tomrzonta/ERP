"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import { chamarComSessao, limparSessao } from "@/lib/server/sessao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Cliente } from "./types";

export type CompraExportada = { numero: string; ocorrido_em: string; total: string };
export type ExportacaoCliente = {
  id: string;
  nome: string;
  telefone: string | null;
  email: string | null;
  cpf: string | null;
  data_nascimento: string | null;
  endereco: string | null;
  consentimento_marketing: boolean;
  consentimento_em: string | null;
  origem: string;
  compras: CompraExportada[];
};

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

export async function criarCliente(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const corpo = {
    nome: texto(dados, "nome"),
    telefone: opcional(dados, "telefone"),
    email: opcional(dados, "email"),
    cpf: opcional(dados, "cpf"),
    data_nascimento: opcional(dados, "data_nascimento"),
    endereco: opcional(dados, "endereco"),
    consentimento_marketing: booleano(dados, "consentimento_marketing"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Cliente>("/clientes", { metodo: "POST", corpo }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath("/clientes");
  redirect("/clientes");
}

export async function atualizarCliente(
  clienteId: string,
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const corpo = {
    nome: texto(dados, "nome"),
    telefone: opcional(dados, "telefone"),
    email: opcional(dados, "email"),
    cpf: opcional(dados, "cpf"),
    data_nascimento: opcional(dados, "data_nascimento"),
    endereco: opcional(dados, "endereco"),
    consentimento_marketing: booleano(dados, "consentimento_marketing"),
  };

  const resultado = await comSessao(() =>
    chamarComSessao<Cliente>(`/clientes/${clienteId}`, { metodo: "PATCH", corpo }),
  );
  if (!resultado.ok) {
    return { erro: resultado.erro };
  }

  revalidatePath("/clientes");
  revalidatePath(`/clientes/${clienteId}`);
  return { erro: "" };
}

export async function mesclarClientes(
  clienteId: string,
  duplicadoId: string,
): Promise<{ ok: true; dados: Cliente } | { ok: false; erro: string }> {
  const resultado = await comSessao(() =>
    chamarComSessao<Cliente>(`/clientes/${clienteId}/mesclar`, {
      metodo: "POST",
      corpo: { duplicado_id: duplicadoId },
    }),
  );
  if (resultado.ok) {
    revalidatePath("/clientes");
    revalidatePath(`/clientes/${clienteId}`);
  }
  return resultado;
}

export async function anonimizarCliente(
  clienteId: string,
): Promise<{ ok: true; dados: Cliente } | { ok: false; erro: string }> {
  const resultado = await comSessao(() =>
    chamarComSessao<Cliente>(`/clientes/${clienteId}/anonimizar`, { metodo: "POST" }),
  );
  if (resultado.ok) {
    revalidatePath("/clientes");
    revalidatePath(`/clientes/${clienteId}`);
  }
  return resultado;
}

export async function exportarDadosDoCliente(
  clienteId: string,
): Promise<{ ok: true; dados: ExportacaoCliente } | { ok: false; erro: string }> {
  return comSessao(() =>
    chamarComSessao<ExportacaoCliente>(`/clientes/${clienteId}/exportar`),
  );
}
