import Link from "next/link";

import { moeda, porcentagem } from "@/lib/formato";
import { BotaoEstoque } from "@/modules/estoque/components/botao-estoque";
import { BotaoEditarProduto } from "./botao-editar-produto";
import type { Categoria, Produto, Unidade } from "../types";

export function TabelaProdutos({
  produtos,
  unidades,
  categorias,
  podeEditar,
  podeVerCusto,
  podeMovimentarEstoque = false,
  podeAjustarEstoque = false,
  mensagemVazia,
}: {
  produtos: Produto[];
  unidades: Unidade[];
  categorias: Categoria[];
  podeEditar: boolean;
  podeVerCusto: boolean;
  podeMovimentarEstoque?: boolean;
  podeAjustarEstoque?: boolean;
  mensagemVazia: string;
}) {
  const temEstoque = podeMovimentarEstoque || podeAjustarEstoque;
  const temAcoes = podeEditar || temEstoque;
  const casasPorUnidade = new Map(unidades.map((u) => [u.codigo, u.casas_exibidas]));

  if (produtos.length === 0) {
    return <p className="mt-10 text-sm text-[#5b6b75]">{mensagemVazia}</p>;
  }

  return (
    <div className="mt-8 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
      <table className="w-full text-sm">
        <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
          <tr>
            <th className="px-4 py-3 font-medium">Produto</th>
            <th className="px-4 py-3 font-medium">SKU</th>
            <th className="px-4 py-3 font-medium">Un.</th>
            <th className="px-4 py-3 text-right font-medium">Preço</th>
            {podeVerCusto ? <th className="px-4 py-3 text-right font-medium">Margem</th> : null}
            {temAcoes ? <th className="px-4 py-3" /> : null}
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
                {produto.tipo === "kit" ? (
                  <span className="ml-2 rounded-full bg-[#0f6d5c]/10 px-2 py-0.5 text-xs font-medium text-[#0f6d5c]">
                    kit
                  </span>
                ) : null}
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
              {temAcoes ? (
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    {temEstoque && produto.controla_estoque && produto.tipo !== "kit" ? (
                      <BotaoEstoque
                        produtoId={produto.id}
                        nome={produto.nome}
                        unidadeCodigo={produto.unidade_codigo}
                        casas={casasPorUnidade.get(produto.unidade_codigo) ?? 2}
                        custoMedio={produto.custo_medio}
                        podeMovimentar={podeMovimentarEstoque}
                        podeAjustar={podeAjustarEstoque}
                      />
                    ) : null}
                    {podeEditar ? (
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
          ))}
        </tbody>
      </table>
    </div>
  );
}
