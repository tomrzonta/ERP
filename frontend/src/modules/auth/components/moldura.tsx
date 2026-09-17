import Link from "next/link";
import type { ReactNode } from "react";

/**
 * Moldura das telas de entrada.
 *
 * Paleta: tinta #16222b · papel #f7f8f8 · linha #dbe1e4 · ação #0f6d5c · alerta #a8341f.
 * O painel da esquerda mostra a composição de um produto real, que é o que o
 * sistema faz de diferente; o formulário fica quieto ao lado.
 */
export function MolduraAuth({
  titulo,
  descricao,
  children,
  rodape,
}: {
  titulo: string;
  descricao: string;
  children: ReactNode;
  rodape: ReactNode;
}) {
  return (
    <main className="grid min-h-screen bg-[#f7f8f8] lg:grid-cols-[1.05fr_1fr]">
      <section className="hidden flex-col justify-between bg-[#16222b] p-10 text-[#e7ecef] lg:flex">
        <Link href="/" className="text-lg font-semibold tracking-tight text-white">
          ERP
        </Link>

        <div className="max-w-sm">
          <p className="text-2xl font-semibold leading-snug tracking-tight text-white">
            Um vaso, uma planta, um preço que fecha a conta.
          </p>
          <dl className="mt-8 space-y-3 border-t border-white/15 pt-6 text-sm">
            {[
              ["Filamento PLA", "85 g"],
              ["Terra adubada", "0,150 kg"],
              ["Suculenta", "1 un"],
              ["Embalagem", "1 un"],
            ].map(([item, quantidade]) => (
              <div key={item} className="flex justify-between gap-6">
                <dt className="text-[#a9bac4]">{item}</dt>
                <dd className="tabular-nums">{quantidade}</dd>
              </div>
            ))}
            <div className="flex justify-between gap-6 border-t border-white/15 pt-3 font-medium text-white">
              <dt>Kit montado</dt>
              <dd className="tabular-nums">R$ 42,00</dd>
            </div>
          </dl>
        </div>

        <p className="text-sm text-[#a9bac4]">
          Estoque, custo e margem de cada parte, sem planilha paralela.
        </p>
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">{titulo}</h1>
          <p className="mt-2 text-sm text-[#5b6b75]">{descricao}</p>
          <div className="mt-8">{children}</div>
          <div className="mt-6 text-sm text-[#5b6b75]">{rodape}</div>
        </div>
      </section>
    </main>
  );
}
