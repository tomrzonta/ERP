import Link from "next/link";

import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { AbasLista } from "@/modules/produtos/components/abas-lista";
import { TabelaProdutos } from "@/modules/produtos/components/tabela-produtos";
import type { Categoria, Produto, Unidade } from "@/modules/produtos/types";

export const metadata = { title: "Kits · ERP" };

export default async function KitsPage({
  searchParams,
}: {
  searchParams: Promise<{ termo?: string }>;
}) {
  const { termo } = await searchParams;
  const eu = await obterEu();
  const parametros = new URLSearchParams({ tipo: "kit" });
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
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Kits</h1>
        {podeEditar ? (
          <Link
            href="/produtos/novo?de=kits"
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            Novo kit
          </Link>
        ) : null}
      </div>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Produtos montados a partir de componentes cadastrados em{" "}
        <Link href="/produtos/insumos" className="text-[#0f6d5c] hover:underline">
          Insumos
        </Link>
        . Kit tem saldo próprio: a montagem dá baixa nos componentes e credita o saldo dele.
      </p>

      <AbasLista ativa="kits" />

      <form action="/produtos/kits" className="mt-6 flex gap-3">
        <input
          name="termo"
          defaultValue={termo ?? ""}
          placeholder="Buscar por nome ou SKU"
          aria-label="Buscar kits"
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
        mensagemVazia={
          termo ? "Nenhum kit encontrado para essa busca." : "Nenhum kit ainda. Crie um produto do tipo Kit."
        }
      />
    </div>
  );
}
