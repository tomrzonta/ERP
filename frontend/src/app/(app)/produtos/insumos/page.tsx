import Link from "next/link";

import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { AbasLista } from "@/modules/produtos/components/abas-lista";
import { TabelaProdutos } from "@/modules/produtos/components/tabela-produtos";
import type { Categoria, Produto, Unidade } from "@/modules/produtos/types";

export const metadata = { title: "Insumos · ERP" };

export default async function InsumosPage({
  searchParams,
}: {
  searchParams: Promise<{ termo?: string }>;
}) {
  const { termo } = await searchParams;
  const eu = await obterEu();
  const parametros = new URLSearchParams({ apenas_insumos: "true" });
  if (termo) parametros.set("termo", termo);
  const [produtos, unidades, categorias] = await Promise.all([
    carregarDaSessao<Produto[]>(`/produtos?${parametros}`),
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Categoria[]>("/categorias"),
  ]);

  const podeEditar = eu.permissoes.includes("produtos.editar");
  const podeVerCusto = eu.permissoes.includes("produtos.ver_custo");

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Insumos</h1>
        {podeEditar ? (
          <Link
            href="/produtos/novo?de=insumos"
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            Novo insumo
          </Link>
        ) : null}
      </div>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Matéria-prima e insumos usados em kits e montagens. Um item marcado como vendável e
        insumo ao mesmo tempo (como um vaso vendido solto e usado num kit) aparece aqui e em{" "}
        <Link href="/produtos" className="text-[#0f6d5c] hover:underline">
          Produtos
        </Link>{" "}
        — sem precisar cadastrar duas vezes.
      </p>

      <AbasLista ativa="insumos" />

      <form action="/produtos/insumos" className="mt-6 flex gap-3">
        <input
          name="termo"
          defaultValue={termo ?? ""}
          placeholder="Buscar por nome, SKU ou código de barras"
          aria-label="Buscar insumos"
          className="w-full max-w-sm rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-[#16222b] outline-none focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        />
        <button
          type="submit"
          className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
        >
          Buscar
        </button>
      </form>

      <TabelaProdutos
        produtos={produtos}
        unidades={unidades}
        categorias={categorias}
        podeEditar={podeEditar}
        podeVerCusto={podeVerCusto}
        podeMovimentarEstoque={eu.permissoes.includes("estoque.movimentar")}
        podeAjustarEstoque={eu.permissoes.includes("estoque.ajustar")}
        mensagemVazia={
          termo
            ? "Nenhum insumo encontrado para essa busca."
            : "Nenhum insumo ainda. Cadastre um produto e marque \"Usado como insumo\"."
        }
      />
    </div>
  );
}
