"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { anonimizarCliente, exportarDadosDoCliente } from "../actions";
import type { Cliente } from "../types";

export function AcoesLgpd({ cliente }: { cliente: Cliente }) {
  const router = useRouter();
  const [confirmandoAnonimizacao, setConfirmandoAnonimizacao] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  async function exportar() {
    setErro("");
    const resultado = await exportarDadosDoCliente(cliente.id);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    const conteudo = JSON.stringify(resultado.dados, null, 2);
    const blob = new Blob([conteudo], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cliente-${cliente.nome.toLowerCase().replace(/\s+/g, "-")}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function anonimizar() {
    setEnviando(true);
    setErro("");
    const resultado = await anonimizarCliente(cliente.id);
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    setConfirmandoAnonimizacao(false);
    router.refresh();
  }

  if (cliente.anonimizado_em) {
    return (
      <p className="text-sm text-[#5b6b75]">
        Dados pessoais anonimizados em{" "}
        {new Date(cliente.anonimizado_em).toLocaleString("pt-BR")}.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-4 text-sm">
        <button type="button" onClick={exportar} className="text-[#0f6d5c] hover:underline">
          Exportar dados (LGPD)
        </button>
        {!confirmandoAnonimizacao ? (
          <button
            type="button"
            onClick={() => setConfirmandoAnonimizacao(true)}
            className="text-[#a8341f] hover:underline"
          >
            Anonimizar dados pessoais
          </button>
        ) : null}
      </div>
      {confirmandoAnonimizacao ? (
        <div className="flex items-center gap-3 rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm">
          <span className="text-[#a8341f]">
            Apaga nome, telefone, e-mail, CPF e endereço. Não pode ser desfeito. Continuar?
          </span>
          <button
            type="button"
            disabled={enviando}
            onClick={anonimizar}
            className="font-medium text-[#a8341f] hover:underline disabled:opacity-60"
          >
            {enviando ? "Anonimizando..." : "Confirmar"}
          </button>
          <button
            type="button"
            onClick={() => setConfirmandoAnonimizacao(false)}
            className="text-[#5b6b75] hover:text-[#16222b]"
          >
            Voltar
          </button>
        </div>
      ) : null}
      {erro ? <Aviso>{erro}</Aviso> : null}
    </div>
  );
}
