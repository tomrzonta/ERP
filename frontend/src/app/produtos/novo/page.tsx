import Link from "next/link";
import { redirect } from "next/navigation";

import { Cabecalho } from "@/components/cabecalho";
import { carregarDaSessao } from "@/lib/server/sessao";
import type { Eu } from "@/modules/auth/types";
import { criarProduto } from "@/modules/produtos/actions";
import { FormularioProduto } from "@/modules/produtos/components/formulario-produto";
import type { Categoria, Unidade } from "@/modules/produtos/types";

export const metadata = { title: "Novo produto · ERP" };

export default async function NovoProdutoPage() {
  const eu = await carregarDaSessao<Eu>("/auth/eu");
  if (!eu.permissoes.includes("produtos.editar")) {
    redirect("/produtos");
  }

  const [unidades, categorias] = await Promise.all([
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Categoria[]>("/categorias"),
  ]);

  return (
    <>
      <Cabecalho eu={eu} />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <Link href="/produtos" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
          Voltar para produtos
        </Link>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[#16222b]">
          Novo produto
        </h1>
        <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
          A unidade de estoque define como o saldo é contado. Filamento em gramas, bolo em
          unidades, tecido em metros.
        </p>

        <div className="mt-8">
          <FormularioProduto
            acao={criarProduto}
            unidades={unidades}
            categorias={categorias}
            podeVerCusto={eu.permissoes.includes("produtos.ver_custo")}
            textoBotao="Criar produto"
          />
        </div>
      </main>
    </>
  );
}
