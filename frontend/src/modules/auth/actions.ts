"use server";

import { redirect } from "next/navigation";

import { chamarApi, mensagemDoErro, SessaoExpirada } from "@/lib/server/api";
import {
  chamarComSessao,
  gravarAcesso,
  gravarSessao,
  limparSessao,
  tokenDeAcesso,
} from "@/lib/server/sessao";
import type { EstadoFormulario, RespostaLogin } from "./types";

const MINIMO_SENHA = 8;

function texto(dados: FormData, campo: string): string {
  return String(dados.get(campo) ?? "").trim();
}

export async function entrar(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const email = texto(dados, "email");
  const senha = String(dados.get("senha") ?? "");

  if (!email || !senha) {
    return { erro: "Informe seu e-mail e sua senha." };
  }

  let resposta: RespostaLogin;
  try {
    resposta = await chamarApi<RespostaLogin>("/auth/login", {
      metodo: "POST",
      corpo: { email, senha },
    });
  } catch (erro) {
    return { erro: mensagemDoErro(erro) };
  }

  await gravarSessao(resposta.tokens);
  redirect(resposta.empresa_ativa_id ? "/" : "/escolher-empresa");
}

export async function criarConta(
  _anterior: EstadoFormulario,
  dados: FormData,
): Promise<EstadoFormulario> {
  const nome = texto(dados, "nome");
  const email = texto(dados, "email");
  const senha = String(dados.get("senha") ?? "");
  const nomeEmpresa = texto(dados, "nome_empresa");

  if (!nome || !email || !senha || !nomeEmpresa) {
    return { erro: "Preencha todos os campos para criar a conta." };
  }
  if (senha.length < MINIMO_SENHA) {
    return { erro: `A senha precisa de pelo menos ${MINIMO_SENHA} caracteres.` };
  }

  let resposta: RespostaLogin;
  try {
    resposta = await chamarApi<RespostaLogin>("/auth/cadastro", {
      metodo: "POST",
      corpo: { nome, email, senha, nome_empresa: nomeEmpresa },
    });
  } catch (erro) {
    return { erro: mensagemDoErro(erro) };
  }

  await gravarSessao(resposta.tokens);
  redirect("/");
}

export async function escolherEmpresa(dados: FormData): Promise<void> {
  const empresaId = texto(dados, "empresa_id");
  if (!empresaId) {
    return;
  }

  try {
    const { access_token } = await chamarComSessao<{ access_token: string }>(
      "/auth/empresa-ativa",
      { metodo: "POST", corpo: { empresa_id: empresaId } },
    );
    await gravarAcesso(access_token);
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      await limparSessao();
      redirect("/entrar");
    }
    throw erro;
  }

  redirect("/");
}

export async function sair(): Promise<void> {
  const token = await tokenDeAcesso();
  if (token) {
    // Encerra a sessão no servidor; se já estiver encerrada, segue em frente
    await chamarApi("/auth/sair", { metodo: "POST", token }).catch(() => undefined);
  }
  await limparSessao();
  redirect("/entrar");
}
