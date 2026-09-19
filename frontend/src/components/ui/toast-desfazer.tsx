"use client";

import { useEffect } from "react";

/** Aviso flutuante com opção de desfazer, some sozinho depois de `duracaoMs`. */
export function ToastDesfazer({
  mensagem,
  aoDesfazer,
  aoEncerrar,
  duracaoMs = 8000,
}: {
  mensagem: string;
  aoDesfazer: () => void;
  aoEncerrar: () => void;
  duracaoMs?: number;
}) {
  useEffect(() => {
    const id = setTimeout(aoEncerrar, duracaoMs);
    return () => clearTimeout(id);
  }, [aoEncerrar, duracaoMs]);

  return (
    <div className="fixed inset-x-0 bottom-6 z-50 flex justify-center px-4">
      <div className="flex items-center gap-4 rounded-lg bg-[#16222b] px-4 py-3 text-sm text-white shadow-lg">
        <span>{mensagem}</span>
        <button
          type="button"
          onClick={() => {
            aoDesfazer();
            aoEncerrar();
          }}
          className="font-medium text-[#7fd6c2] hover:underline"
        >
          Desfazer
        </button>
      </div>
    </div>
  );
}
