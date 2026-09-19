"use client";

import { useMemo, useState, type ReactNode } from "react";

/** Campo de busca com dropdown filtrado, que limpa e fecha ao escolher —
 * pensado pra adicionar itens a uma lista (carrinho), não pra um formulário. */
export function SeletorBusca<T>({
  itens,
  chave,
  correspondeAoTermo,
  aoEscolher,
  renderItem,
  placeholder,
}: {
  itens: T[];
  chave: (item: T) => string;
  correspondeAoTermo: (item: T, termo: string) => boolean;
  aoEscolher: (item: T) => void;
  renderItem: (item: T) => ReactNode;
  placeholder?: string;
}) {
  const [filtro, setFiltro] = useState("");
  const [aberto, setAberto] = useState(false);

  const filtrados = useMemo(() => {
    const termo = filtro.trim().toLowerCase();
    const lista = termo ? itens.filter((item) => correspondeAoTermo(item, termo)) : itens;
    return lista.slice(0, 20);
  }, [filtro, itens, correspondeAoTermo]);

  function escolher(item: T) {
    aoEscolher(item);
    setFiltro("");
    setAberto(false);
  }

  return (
    <div className="relative">
      <input
        type="text"
        autoComplete="off"
        value={filtro}
        placeholder={placeholder}
        onFocus={() => setAberto(true)}
        onChange={(evento) => {
          setFiltro(evento.target.value);
          setAberto(true);
        }}
        onBlur={() => setTimeout(() => setAberto(false), 150)}
        className="w-full rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none transition-colors placeholder:text-[#9aa7af] focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
      />
      {aberto ? (
        <ul className="absolute top-full z-10 mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-[#dbe1e4] bg-white shadow-lg">
          {filtrados.length > 0 ? (
            filtrados.map((item) => (
              <li key={chave(item)}>
                <button
                  type="button"
                  onMouseDown={(evento) => evento.preventDefault()}
                  onClick={() => escolher(item)}
                  className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-base text-[#16222b] hover:bg-[#f7f8f8]"
                >
                  {renderItem(item)}
                </button>
              </li>
            ))
          ) : (
            <li className="px-3 py-2 text-sm text-[#5b6b75]">Nada encontrado.</li>
          )}
        </ul>
      ) : null}
    </div>
  );
}
