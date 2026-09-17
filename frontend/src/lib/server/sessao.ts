/**
 * Tokens em cookies protegidos (httpOnly): JavaScript da página não os lê,
 * então uma falha de segurança no frontend não expõe a sessão.
 *
 * A renovação do token de acesso acontece no middleware, porque só ele e as
 * Server Actions podem gravar cookies.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { chamarApi, ErroApi, SessaoExpirada } from "@/lib/server/api";

export const COOKIE_ACESSO = "erp_acesso";
export const COOKIE_RENOVACAO = "erp_renovacao";

// O cookie de acesso expira um pouco antes do token, para o middleware renovar
export const SEGUNDOS_ACESSO = 60 * 14;
export const SEGUNDOS_RENOVACAO = 60 * 60 * 24 * 30;

export const OPCOES_COOKIE = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export type Tokens = { access_token: string; refresh_token: string };

export async function gravarSessao(tokens: Tokens) {
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_ACESSO, tokens.access_token, {
    ...OPCOES_COOKIE,
    maxAge: SEGUNDOS_ACESSO,
  });
  cookieStore.set(COOKIE_RENOVACAO, tokens.refresh_token, {
    ...OPCOES_COOKIE,
    maxAge: SEGUNDOS_RENOVACAO,
  });
}

export async function gravarAcesso(accessToken: string) {
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_ACESSO, accessToken, {
    ...OPCOES_COOKIE,
    maxAge: SEGUNDOS_ACESSO,
  });
}

export async function limparSessao() {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_ACESSO);
  cookieStore.delete(COOKIE_RENOVACAO);
}

export async function tokenDeAcesso(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(COOKIE_ACESSO)?.value ?? null;
}

/** Chama a API com o token da sessão. Sem token válido, SessaoExpirada. */
export async function chamarComSessao<T>(
  caminho: string,
  opcoes: { metodo?: "GET" | "POST" | "PATCH" | "DELETE"; corpo?: unknown } = {},
): Promise<T> {
  const token = await tokenDeAcesso();
  if (!token) {
    throw new SessaoExpirada();
  }
  try {
    return await chamarApi<T>(caminho, { ...opcoes, token });
  } catch (erro) {
    if (erro instanceof ErroApi && erro.status === 401) {
      throw new SessaoExpirada();
    }
    throw erro;
  }
}

/** Para páginas: busca dados da sessão ou manda para a tela de entrada. */
export async function carregarDaSessao<T>(caminho: string): Promise<T> {
  try {
    return await chamarComSessao<T>(caminho);
  } catch (erro) {
    if (erro instanceof SessaoExpirada) {
      redirect("/entrar");
    }
    throw erro;
  }
}
