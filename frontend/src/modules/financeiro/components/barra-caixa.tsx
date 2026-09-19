"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Modal } from "@/components/ui/modal";
import type { Caixa } from "../types";
import { FormularioAbrirCaixa } from "./formulario-abrir-caixa";

/** Estado do caixa no topo da tela de Vendas: mostra quem abriu e desde
 * quando, ou o botão pra abrir (em modal, com o valor inicial). */
export function BarraCaixa({ caixa, podeOperar }: { caixa: Caixa | null; podeOperar: boolean }) {
  const router = useRouter();
  const [aberto, setAberto] = useState(false);

  if (caixa) {
    return (
      <Link
        href="/caixa"
        className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
      >
        <span className="mr-2 inline-block size-2 rounded-full bg-[#0f6d5c]" aria-hidden="true" />
        Caixa aberto
        <span className="text-[#5b6b75]">
          {" "}
          · {caixa.aberto_por_nome ?? "—"} às{" "}
          {new Date(caixa.aberto_em).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </Link>
    );
  }

  if (!podeOperar) {
    return <span className="text-sm text-[#5b6b75]">Caixa fechado</span>;
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="rounded-md border border-[#0f6d5c] bg-white px-4 py-2 text-sm font-medium text-[#0f6d5c] transition-colors hover:bg-[#0f6d5c] hover:text-white"
      >
        Abrir caixa
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo="Abrir caixa">
        <p className="mt-2 text-sm text-[#5b6b75]">
          Fica registrado no histórico que foi você quem abriu.
        </p>
        <div className="mt-5">
          <FormularioAbrirCaixa
            aoConcluir={() => {
              setAberto(false);
              router.refresh();
            }}
          />
        </div>
      </Modal>
    </>
  );
}
