import { cache } from "react";

import { carregarDaSessao } from "@/lib/server/sessao";
import type { Eu } from "./types";

/**
 * Dados do usuário logado.
 *
 * O cache do React evita repetir a chamada: layout e página pedem o mesmo
 * "eu" e a API é consultada uma vez por requisição.
 */
export const obterEu = cache(() => carregarDaSessao<Eu>("/auth/eu"));
