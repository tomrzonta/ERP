import Link from "next/link";

import { moeda, porcentagem } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import type { Produto } from "@/modules/produtos/types";

export const metadata = { title: "Produtos · ERP" };

export default async function ProdutosPage({
  searchParams,
}: {
  searchParams: Promise<{ termo?: string }>;
}) {
  const { termo } = await searchParams;
  const eu = await obterEu();
  const caminho = termo ? `/produtos?termo=${encodeURIComponent(termo)}` : "/produtos";
  const produtos = await carregarDaSessao<Produto[]>(caminho);

  const podeEditar = eu.permissoes.includes("produtos.editar");
  const podeVerCusto = eu.permissoes.includes("produtos.ver_custo");

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Produtos</h1>
        {podeEditar ? (
          <Link
            href="/produtos/novo"
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            Novo produto
          </Link>
        ) : null}
      </div>

      <form action="/produtos" className="mt-6 flex gap-3">
        <input
          name="termo"
          defaultValue={termo ?? ""}
          placeholder="Buscar por nome, SKU ou código de barras"
          aria-label="Buscar produtos"
          className="w-full max-w-sm rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-[#16222b] outline-none focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        />
        <button
          type="submit"
          className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
        >
          Buscar
        </button>
      </form>

      {produtos.length === 0 ? (
        <p className="mt-10 text-sm text-[#5b6b75]">
          {termo
            ? "Nenhum produto encontrado para essa busca."
            : "Você ainda não cadastrou produtos. Comece pelo que você vende mais."}
        </p>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
              <tr>
                <th className="px-4 py-3 font-medium">Produto</th>
                <th className="px-4 py-3 font-medium">SKU</th>
                <th className="px-4 py-3 font-medium">Un.</th>
                <th className="px-4 py-3 text-right font-medium">Preço</th>
                {podeVerCusto ? (
                  <th className="px-4 py-3 text-right font-medium">Margem</th>
                ) : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#dbe1e4]">
              {produtos.map((produto) => (
                <tr key={produto.id} className="transition-colors hover:bg-[#f7f8f8]">
                  <td className="px-4 py-3">
                    <Link
                      href={`/produtos/${produto.id}`}
                      className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                    >
                      {produto.nome}
                    </Link>
                    {produto.insumo ? (
                      <span className="ml-2 text-xs text-[#5b6b75]">
                        {produto.vendavel ? "insumo e venda" : "insumo"}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 tabular-nums text-[#5b6b75]">{produto.sku}</td>
                  <td className="px-4 py-3 text-[#5b6b75]">{produto.unidade_codigo}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                    {moeda(produto.preco_venda)}
                  </td>
                  {podeVerCusto ? (
                    <td className="px-4 py-3 text-right tabular-nums text-[#5b6b75]">
                      {produto.margem_percentual ? porcentagem(produto.margem_percentual) : "—"}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
