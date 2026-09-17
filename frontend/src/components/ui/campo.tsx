import type { InputHTMLAttributes } from "react";

/** Campo de formulário com rótulo e dica opcional. */
export function Campo({
  nome,
  rotulo,
  tipo = "text",
  dica,
  ...props
}: {
  nome: string;
  rotulo: string;
  tipo?: string;
  dica?: string;
} & InputHTMLAttributes<HTMLInputElement>) {
  const idDica = dica ? `${nome}-dica` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={nome} className="text-sm font-medium text-[#16222b]">
        {rotulo}
      </label>
      <input
        id={nome}
        name={nome}
        type={tipo}
        aria-describedby={idDica}
        className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none transition-colors placeholder:text-[#9aa7af] focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        {...props}
      />
      {dica ? (
        <p id={idDica} className="text-xs text-[#5b6b75]">
          {dica}
        </p>
      ) : null}
    </div>
  );
}
