"use client";

import { useEffect } from "react";

import { salvarCatalogoOffline, type ProdutoOffline } from "@/lib/client/banco-local";

/** Grava o catálogo (produto + preço + saldo) já carregado pelo servidor no
 * IndexedDB, pra consulta com o app offline. Não renderiza nada — só
 * sincroniza como efeito colateral de uma página que já buscou esses dados. */
export function SincronizarCatalogo({ produtos }: { produtos: ProdutoOffline[] }) {
  useEffect(() => {
    salvarCatalogoOffline(produtos).catch(() => {});
    // Só precisa gravar uma vez por carregamento da página, com os dados
    // que o servidor já trouxe — não a cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
