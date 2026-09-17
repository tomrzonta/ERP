"use client";

import type { ReactNode } from "react";
import { useFormStatus } from "react-dom";

/** Botão de envio que se desabilita e avisa enquanto a ação roda. */
export function BotaoEnviar({
  children,
  carregando,
}: {
  children: ReactNode;
  carregando: string;
}) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-md bg-[#0f6d5c] px-4 py-2.5 font-medium text-white transition-colors hover:bg-[#0b564a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f6d5c] disabled:opacity-70"
    >
      {pending ? carregando : children}
    </button>
  );
}
