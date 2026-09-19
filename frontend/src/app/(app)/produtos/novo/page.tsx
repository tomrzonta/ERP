import Link from "next/link";
import { redirect } from "next/navigation";

import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { criarProduto } from "@/modules/produtos/actions";
import { FormularioProduto } from "@/modules/produtos/components/formulario-produto";
import type { Categoria, TipoProduto, Unidade } from "@/modules/produtos/types";

export const metadata = { title: "Novo produto · ERP" };

const ORIGEM = {
  insumos: {
    titulo: "Novo insumo",
    descricao: "Matéria-prima usada em kits e montagens, como filamento ou terra adubada.",
    voltar: { href: "/produtos/insumos", texto: "Voltar para insumos" },
    tipoInicial: "simples" as TipoProduto,
    vendavelInicial: false,
    insumoInicial: true,
  },
  kits: {
    titulo: "Novo kit",
    descricao:
      "Um kit tem saldo próprio: a montagem dá baixa nos componentes e credita esse saldo.",
    voltar: { href: "/produtos/kits", texto: "Voltar para kits" },
    tipoInicial: "kit" as TipoProduto,
    vendavelInicial: true,
    insumoInicial: false,
  },
  produtos: {
    titulo: "Novo produto",
    descricao:
      "A unidade de estoque define como o saldo é contado. Filamento em gramas, bolo em unidades, tecido em metros.",
    voltar: { href: "/produtos", texto: "Voltar para produtos" },
    tipoInicial: "simples" as TipoProduto,
    vendavelInicial: true,
    insumoInicial: false,
  },
} as const;

export default async function NovoProdutoPage({
  searchParams,
}: {
  searchParams: Promise<{ de?: string }>;
}) {
  const { de } = await searchParams;
  const eu = await obterEu();
  if (!eu.permissoes.includes("produtos.editar")) {
    redirect("/produtos");
  }

  const contexto = de === "insumos" || de === "kits" ? ORIGEM[de] : ORIGEM.produtos;

  const [unidades, categorias] = await Promise.all([
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Categoria[]>("/categorias"),
  ]);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href={contexto.voltar.href} className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        {contexto.voltar.texto}
      </Link>
      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[#16222b]">
        {contexto.titulo}
      </h1>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">{contexto.descricao}</p>

      <div className="mt-8">
        <FormularioProduto
          acao={criarProduto}
          unidades={unidades}
          categorias={categorias}
          podeVerCusto={eu.permissoes.includes("produtos.ver_custo")}
          textoBotao="Criar produto"
          tipoInicial={contexto.tipoInicial}
          vendavelInicial={contexto.vendavelInicial}
          insumoInicial={contexto.insumoInicial}
        />
      </div>
    </div>
  );
}
