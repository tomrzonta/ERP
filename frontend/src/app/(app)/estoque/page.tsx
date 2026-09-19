import Link from "next/link";

import { numero } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { BotaoEstoque } from "@/modules/estoque/components/botao-estoque";
import type { SaldoComProduto } from "@/modules/estoque/types";
import { BotaoEditarProduto } from "@/modules/produtos/components/botao-editar-produto";
import type { Categoria, Produto, Unidade } from "@/modules/produtos/types";

export const metadata = { title: "Estoque · ERP" };

export default async function EstoquePage({
  searchParams,
}: {
  searchParams: Promise<{ termo?: string }>;
}) {
  const { termo } = await searchParams;
  const eu = await obterEu();
  const caminho = termo
    ? `/estoque/saldos?termo=${encodeURIComponent(termo)}`
    : "/estoque/saldos";
  const [saldos, unidades, produtos, categorias] = await Promise.all([
    carregarDaSessao<SaldoComProduto[]>(caminho),
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Produto[]>("/produtos?limite=200"),
    carregarDaSessao<Categoria[]>("/categorias"),
  ]);
  const casasPorUnidade = new Map(unidades.map((unidade) => [unidade.codigo, unidade.casas_exibidas]));
  const produtosPorId = new Map(produtos.map((produto) => [produto.id, produto]));

  const podeEditar = eu.permissoes.includes("produtos.editar");
  const podeVerCusto = eu.permissoes.includes("produtos.ver_custo");
  const podeMovimentar = eu.permissoes.includes("estoque.movimentar");
  const podeAjustar = eu.permissoes.includes("estoque.ajustar");
  const temAcoes = podeEditar || podeMovimentar || podeAjustar;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Estoque</h1>

      <form action="/estoque" className="mt-6 flex gap-3">
        <input
          name="termo"
          defaultValue={termo ?? ""}
          placeholder="Buscar por nome ou SKU"
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

      {saldos.length === 0 ? (
        <p className="mt-10 text-sm text-[#5b6b75]">
          {termo
            ? "Nenhum produto encontrado para essa busca."
            : "Nenhum produto com controle de estoque ainda."}
        </p>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
              <tr>
                <th className="px-4 py-3 font-medium">Produto</th>
                <th className="px-4 py-3 font-medium">SKU</th>
                <th className="px-4 py-3 text-right font-medium">Físico</th>
                <th className="px-4 py-3 text-right font-medium">Reservado</th>
                <th className="px-4 py-3 text-right font-medium">Disponível</th>
                {temAcoes ? <th className="px-4 py-3" /> : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#dbe1e4]">
              {saldos.map((saldo) => {
                const casas = casasPorUnidade.get(saldo.unidade_codigo) ?? 2;
                const produto = produtosPorId.get(saldo.produto_id);
                return (
                  <tr key={saldo.produto_id} className="transition-colors hover:bg-[#f7f8f8]">
                    <td className="px-4 py-3">
                      <Link
                        href={`/produtos/${saldo.produto_id}/estoque`}
                        className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                      >
                        {saldo.nome}
                      </Link>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-[#5b6b75]">{saldo.sku}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                      {numero(saldo.fisico, casas)} {saldo.unidade_codigo}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-[#5b6b75]">
                      {numero(saldo.reservado, casas)} {saldo.unidade_codigo}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                      {numero(saldo.disponivel, casas)} {saldo.unidade_codigo}
                    </td>
                    {temAcoes ? (
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <BotaoEstoque
                            produtoId={saldo.produto_id}
                            nome={saldo.nome}
                            unidadeCodigo={saldo.unidade_codigo}
                            fisico={saldo.fisico}
                            casas={casas}
                            custoMedio={produto?.custo_medio ?? null}
                            podeMovimentar={podeMovimentar}
                            podeAjustar={podeAjustar}
                          />
                          {podeEditar && produto ? (
                            <BotaoEditarProduto
                              produto={produto}
                              unidades={unidades}
                              categorias={categorias}
                              podeVerCusto={podeVerCusto}
                            />
                          ) : null}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
