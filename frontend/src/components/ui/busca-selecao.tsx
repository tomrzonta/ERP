"use client";

import { useId, useMemo, useState } from "react";

/** Campo de escolha com busca: digita e filtra, em vez de rolar uma lista gigante. */
export function BuscaSelecao({
  nome,
  rotulo,
  opcoes,
  placeholder,
  dica,
}: {
  nome: string;
  rotulo: string;
  opcoes: { valor: string; texto: string }[];
  placeholder?: string;
  dica?: string;
}) {
  const id = useId();
  const [filtro, setFiltro] = useState("");
  const [selecionado, setSelecionado] = useState<{ valor: string; texto: string } | null>(null);
  const [aberto, setAberto] = useState(false);

  const filtrados = useMemo(() => {
    const termo = filtro.trim().toLowerCase();
    const lista = termo
      ? opcoes.filter((opcao) => opcao.texto.toLowerCase().includes(termo))
      : opcoes;
    return lista.slice(0, 20);
  }, [filtro, opcoes]);

  function escolher(opcao: { valor: string; texto: string }) {
    setSelecionado(opcao);
    setFiltro(opcao.texto);
    setAberto(false);
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-[#16222b]">
        {rotulo}
      </label>
      <div className="relative">
        <input type="hidden" name={nome} value={selecionado?.valor ?? ""} />
        <input
          id={id}
          type="text"
          autoComplete="off"
          value={filtro}
          placeholder={placeholder}
          onFocus={() => setAberto(true)}
          onChange={(evento) => {
            setFiltro(evento.target.value);
            setSelecionado(null);
            setAberto(true);
          }}
          onBlur={() => {
            // atraso curto: permite o clique na opção registrar antes do fechamento
            setTimeout(() => setAberto(false), 150);
          }}
          className="w-full rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none transition-colors placeholder:text-[#9aa7af] focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        />
        {aberto ? (
          <ul className="absolute top-full z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-[#dbe1e4] bg-white shadow-lg">
            {filtrados.length > 0 ? (
              filtrados.map((opcao) => (
                <li key={opcao.valor}>
                  <button
                    type="button"
                    onMouseDown={(evento) => evento.preventDefault()}
                    onClick={() => escolher(opcao)}
                    className="block w-full px-3 py-2 text-left text-base text-[#16222b] hover:bg-[#f7f8f8]"
                  >
                    {opcao.texto}
                  </button>
                </li>
              ))
            ) : (
              <li className="px-3 py-2 text-sm text-[#5b6b75]">Nada encontrado.</li>
            )}
          </ul>
        ) : null}
      </div>
      {dica ? <p className="text-xs text-[#5b6b75]">{dica}</p> : null}
    </div>
  );
}
