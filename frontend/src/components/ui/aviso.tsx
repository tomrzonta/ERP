import type { ReactNode } from "react";

/** Mensagem de erro de um formulário ou de uma ação. */
export function Aviso({ children }: { children: ReactNode }) {
  return (
    <p
      role="alert"
      className="rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm text-[#a8341f]"
    >
      {children}
    </p>
  );
}
