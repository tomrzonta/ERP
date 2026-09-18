import type { SelectHTMLAttributes } from "react";

/** Campo de escolha com rótulo. */
export function Selecao({
  nome,
  rotulo,
  opcoes,
  vazio,
  ...props
}: {
  nome: string;
  rotulo: string;
  opcoes: { valor: string; texto: string }[];
  vazio?: string;
} & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={nome} className="text-sm font-medium text-[#16222b]">
        {rotulo}
      </label>
      <select
        id={nome}
        name={nome}
        className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none transition-colors focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        {...props}
      >
        {vazio ? <option value="">{vazio}</option> : null}
        {opcoes.map((opcao) => (
          <option key={opcao.valor} value={opcao.valor}>
            {opcao.texto}
          </option>
        ))}
      </select>
    </div>
  );
}
