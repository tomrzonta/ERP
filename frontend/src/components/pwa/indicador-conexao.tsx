"use client";

import { useEffect, useState, useSyncExternalStore } from "react";

import {
  listarLancamentosPendentes,
  listarVendasPendentes,
  obterUltimaSincronizacao,
} from "@/lib/client/banco-local";
import { EVENTO_FILA_ATUALIZADA } from "./motor-sincronizacao";

function inscreverConexao(avisar: () => void) {
  window.addEventListener("online", avisar);
  window.addEventListener("offline", avisar);
  return () => {
    window.removeEventListener("online", avisar);
    window.removeEventListener("offline", avisar);
  };
}

function estaOnline() {
  return navigator.onLine;
}

// O servidor não tem como saber a conexão do navegador — assume online até
// o componente montar e o valor real ser lido.
function estaOnlineNoServidor() {
  return true;
}

const CORES_TEXTO_ONLINE = {
  claro: "text-[#5b6b75]",
  escuro: "text-[#a9bac4]",
};

const CORES_TEXTO_OFFLINE = {
  claro: "text-[#8a5a0f]",
  escuro: "text-[#fdf3e0]",
};

const CORES_DETALHE = {
  claro: "text-[#5b6b75]",
  escuro: "text-[#a9bac4]",
};

/** Mostra se o app está online ou offline, a hora do catálogo salvo
 * localmente, e quantas vendas offline ainda aguardam sincronizar.
 * `variante` escolhe as cores conforme o fundo (claro/escuro). O estado
 * inicial assume "online" (o servidor não tem como saber) e se corrige
 * assim que o componente monta no navegador. */
export function IndicadorConexao({ variante = "claro" }: { variante?: "claro" | "escuro" }) {
  const online = useSyncExternalStore(inscreverConexao, estaOnline, estaOnlineNoServidor);
  const [ultimaSincronizacao, setUltimaSincronizacao] = useState<string | null>(null);
  const [pendentes, setPendentes] = useState(0);

  useEffect(() => {
    function atualizar() {
      obterUltimaSincronizacao()
        .then(setUltimaSincronizacao)
        .catch(() => {});
      Promise.all([listarVendasPendentes(), listarLancamentosPendentes()])
        .then(([vendas, lancamentos]) => setPendentes(vendas.length + lancamentos.length))
        .catch(() => {});
    }
    atualizar();
    window.addEventListener(EVENTO_FILA_ATUALIZADA, atualizar);
    return () => window.removeEventListener(EVENTO_FILA_ATUALIZADA, atualizar);
  }, []);

  if (online) {
    return (
      <span className={`inline-flex items-center gap-1.5 text-xs ${CORES_TEXTO_ONLINE[variante]}`}>
        <span className="size-1.5 rounded-full bg-[#3fae6a]" aria-hidden="true" />
        Online
        {pendentes > 0 ? (
          <span className={CORES_DETALHE[variante]}>· sincronizando {pendentes}</span>
        ) : null}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs ${CORES_TEXTO_OFFLINE[variante]}`}
      role="status"
    >
      <span className="size-1.5 rounded-full bg-[#e0a63d]" aria-hidden="true" />
      Offline
      {ultimaSincronizacao ? (
        <span className={CORES_DETALHE[variante]}>
          · catálogo de {new Date(ultimaSincronizacao).toLocaleString("pt-BR")}
        </span>
      ) : null}
      {pendentes > 0 ? (
        <span className={CORES_DETALHE[variante]}>· {pendentes} pendente(s)</span>
      ) : null}
    </span>
  );
}
