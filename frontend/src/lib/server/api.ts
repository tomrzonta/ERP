/**
 * Chamadas à API, feitas SEMPRE do servidor do Next.js.
 * O navegador nunca fala com a API nem enxerga os tokens.
 */
import { env } from "@/lib/env";

/** Espelha o formato de erro do backend: { erro, mensagem } */
export class ErroApi extends Error {
  constructor(
    readonly status: number,
    readonly codigo: string,
    mensagem: string,
  ) {
    super(mensagem);
    this.name = "ErroApi";
  }
}

/** A sessão acabou ou foi revogada: o visitante precisa entrar de novo. */
export class SessaoExpirada extends Error {
  constructor() {
    super("Sessão expirada.");
    this.name = "SessaoExpirada";
  }
}

type Opcoes = {
  metodo?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  corpo?: unknown;
  token?: string | null;
};

export async function chamarApi<T>(caminho: string, opcoes: Opcoes = {}): Promise<T> {
  const resposta = await fetch(`${env.apiUrl}${caminho}`, {
    method: opcoes.metodo ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(opcoes.token ? { Authorization: `Bearer ${opcoes.token}` } : {}),
    },
    body: opcoes.corpo === undefined ? undefined : JSON.stringify(opcoes.corpo),
    cache: "no-store",
  });

  if (resposta.status === 204) {
    return undefined as T;
  }

  const dados = await resposta.json().catch(() => null);

  if (!resposta.ok) {
    throw new ErroApi(
      resposta.status,
      dados?.erro ?? "erro",
      dados?.mensagem ?? "Não foi possível completar a ação. Tente de novo.",
    );
  }

  return dados as T;
}

/** Mensagem pronta para mostrar ao visitante. */
export function mensagemDoErro(erro: unknown): string {
  if (erro instanceof ErroApi) {
    return erro.message;
  }
  return "Não foi possível falar com o servidor. Verifique sua conexão.";
}
