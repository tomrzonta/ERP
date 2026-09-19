"use client";

import { useEffect } from "react";

import { salvarSessaoOffline } from "@/lib/client/banco-local";
import type { Eu } from "@/modules/auth/types";

/** Grava quem está logado (nome, empresa, papel, permissões) no IndexedDB,
 * pra página /offline saber quem é o usuário sem depender do servidor. Não
 * renderiza nada. */
export function SincronizarSessao({ eu }: { eu: Eu }) {
  useEffect(() => {
    salvarSessaoOffline({
      usuarioNome: eu.usuario.nome,
      empresaNome: eu.empresa.nome,
      papel: eu.papel,
      permissoes: eu.permissoes,
    }).catch(() => {});
    // Só precisa gravar uma vez por carregamento — não a cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
