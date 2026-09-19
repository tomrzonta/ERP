import Link from "next/link";

type Aba = "vendaveis" | "insumos" | "kits";

const ABAS: { chave: Aba; titulo: string; href: string }[] = [
  { chave: "vendaveis", titulo: "Produtos", href: "/produtos" },
  { chave: "insumos", titulo: "Insumos", href: "/produtos/insumos" },
  { chave: "kits", titulo: "Kits", href: "/produtos/kits" },
];

/** Navegação entre as três telas de cadastro. Um item pode aparecer em mais de uma. */
export function AbasLista({ ativa }: { ativa: Aba }) {
  return (
    <nav aria-label="Tipo de item" className="mt-6 flex gap-1 border-b border-[#dbe1e4]">
      {ABAS.map((aba) => {
        const ehAtiva = aba.chave === ativa;
        return (
          <Link
            key={aba.chave}
            href={aba.href}
            aria-current={ehAtiva ? "page" : undefined}
            className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
              ehAtiva
                ? "border-[#0f6d5c] font-medium text-[#0f6d5c]"
                : "border-transparent text-[#5b6b75] hover:text-[#16222b]"
            }`}
          >
            {aba.titulo}
          </Link>
        );
      })}
    </nav>
  );
}
