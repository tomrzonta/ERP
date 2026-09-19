"use client";

import type { MouseEventHandler, ReactNode } from "react";
import { useFormStatus } from "react-dom";

/** Botão de envio que se desabilita e avisa enquanto a ação roda. */
export function BotaoEnviar({
  children,
  carregando,
  onClick,
  variante = "primario",
}: {
  children: ReactNode;
  carregando: string;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  variante?: "primario" | "secundario";
}) {
  const { pending } = useFormStatus();
  const classes =
    variante === "primario"
      ? "rounded-md bg-[#0f6d5c] px-4 py-2.5 font-medium text-white transition-colors hover:bg-[#0b564a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f6d5c] disabled:opacity-70"
      : "rounded-md border border-[#dbe1e4] bg-white px-4 py-2.5 font-medium text-[#16222b] transition-colors hover:border-[#0f6d5c] disabled:opacity-70";

  return (
    <button type="submit" disabled={pending} onClick={onClick} className={classes}>
      {pending ? carregando : children}
    </button>
  );
}
