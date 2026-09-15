/**
 * Cliente HTTP único para falar com a API.
 * Todo módulo usa apiFetch em vez de chamar fetch diretamente, assim
 * autenticação, erros e URL base ficam em um só lugar.
 */
import { env } from "@/lib/env";

/** Espelha o formato de erro do backend: { erro, mensagem } */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  headers?: Record<string, string>;
};

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;

  let response: Response;
  try {
    response = await fetch(`${env.apiUrl}${path}`, {
      ...rest,
      headers: { "Content-Type": "application/json", ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "sem_conexao", "Não foi possível conectar à API.");
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      data?.erro ?? "erro",
      data?.mensagem ?? "Erro inesperado.",
    );
  }

  return data as T;
}
