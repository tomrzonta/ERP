import Link from "next/link";

import { moeda, numero } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { adicionarUnidade, atualizarProduto } from "@/modules/produtos/actions";
import { FormularioProduto } from "@/modules/produtos/components/formulario-produto";
import { FormularioUnidade } from "@/modules/produtos/components/formulario-unidade";
import type { Categoria, Produto, Unidade, UnidadeAlternativa } from "@/modules/produtos/types";

export default async function ProdutoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const eu = await obterEu();
  const [produto, unidades, categorias, alternativas] = await Promise.all([
    carregarDaSessao<Produto>(`/produtos/${id}`),
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Categoria[]>("/categorias"),
    carregarDaSessao<UnidadeAlternativa[]>(`/produtos/${id}/unidades`),
  ]);

  const podeEditar = eu.permissoes.includes("produtos.editar");
  const podeVerCusto = eu.permissoes.includes("produtos.ver_custo");

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <Link href="/produtos" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para produtos
      </Link>

      <div className="mt-4 flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">{produto.nome}</h1>
        <p className="text-sm tabular-nums text-[#5b6b75]">
          {produto.sku} · {produto.unidade_codigo}
        </p>
      </div>

      {podeVerCusto ? (
        <dl className="mt-8 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-3">
          <div className="bg-white px-4 py-5">
            <dt className="text-sm text-[#5b6b75]">Preço</dt>
            <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
              {moeda(produto.preco_venda)}
            </dd>
          </div>
          <div className="bg-white px-4 py-5">
            <dt className="text-sm text-[#5b6b75]">Custo médio</dt>
            <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
              {moeda(produto.custo_medio ?? "0")}
            </dd>
          </div>
          <div className="bg-white px-4 py-5">
            <dt className="text-sm text-[#5b6b75]">Margem</dt>
            <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
              {produto.margem_percentual ? `${numero(produto.margem_percentual, 1)}%` : "—"}
            </dd>
          </div>
        </dl>
      ) : null}

      {produto.status === "congelado" ? (
        <p className="mt-8 rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm text-[#a8341f]">
          Este produto está congelado pelo limite do plano. Você pode vender o que está em
          estoque, mas não editar nem repor.
        </p>
      ) : null}

      {podeEditar ? (
        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Dados</h2>
          <div className="mt-5">
            <FormularioProduto
              acao={atualizarProduto.bind(null, produto.id)}
              unidades={unidades}
              categorias={categorias}
              produto={produto}
              podeVerCusto={podeVerCusto}
              textoBotao="Salvar alterações"
            />
          </div>
        </section>
      ) : null}

      <section className="mt-12 border-t border-[#dbe1e4] pt-8">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
          Embalagens e frações
        </h2>
        <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
          Formas de comprar e vender este produto sem mudar a unidade do estoque. O saldo
          continua em {produto.unidade_codigo}.
        </p>

        {alternativas.length > 0 ? (
          <ul className="mt-6 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
            {alternativas.map((unidade) => (
              <li
                key={unidade.id}
                className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
              >
                <span className="font-medium text-[#16222b]">{unidade.nome}</span>
                <span className="tabular-nums text-[#5b6b75]">
                  {numero(unidade.fator, 4)} {produto.unidade_codigo}
                  {unidade.usa_na_compra ? " · compra" : ""}
                  {unidade.usa_na_venda ? " · venda" : ""}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-6 text-sm text-[#5b6b75]">
            Nenhuma ainda. Um bolo vendido em fatias, por exemplo, tem uma unidade
            &quot;Fatia&quot; valendo 0,125.
          </p>
        )}

        {podeEditar && produto.status !== "congelado" ? (
          <div className="mt-8 max-w-xl">
            <FormularioUnidade
              acao={adicionarUnidade.bind(null, produto.id)}
              unidadeBase={produto.unidade_codigo}
            />
          </div>
        ) : null}
      </section>
    </div>
  );
}
