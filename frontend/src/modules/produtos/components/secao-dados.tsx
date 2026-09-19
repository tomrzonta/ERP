import { BotaoEditarProduto } from "./botao-editar-produto";
import type { Categoria, Produto, Unidade } from "../types";

function Fato({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div>
      <dt className="text-sm text-[#5b6b75]">{rotulo}</dt>
      <dd className="mt-0.5 text-base text-[#16222b]">{valor}</dd>
    </div>
  );
}

export function SecaoDados({
  unidades,
  categorias,
  produto,
  podeEditar,
  podeVerCusto,
}: {
  unidades: Unidade[];
  categorias: Categoria[];
  produto: Produto;
  podeEditar: boolean;
  podeVerCusto: boolean;
}) {
  const categoria = categorias.find((c) => c.id === produto.categoria_id);

  const caracteristicas = [
    produto.vendavel && "Vendável",
    produto.insumo && "Usado como insumo",
    produto.controla_estoque && "Controla estoque",
    produto.publicado_na_vitrine && "Publicado na vitrine",
  ].filter(Boolean) as string[];

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Dados</h2>
        {podeEditar ? (
          <BotaoEditarProduto
            produto={produto}
            unidades={unidades}
            categorias={categorias}
            podeVerCusto={podeVerCusto}
          />
        ) : null}
      </div>

      <dl className="mt-5 grid gap-5 sm:grid-cols-2">
        <Fato rotulo="SKU" valor={produto.sku} />
        <Fato rotulo="Unidade de estoque" valor={produto.unidade_codigo} />
        <Fato rotulo="Categoria" valor={categoria?.nome ?? "Sem categoria"} />
        <Fato
          rotulo="Estoque mínimo"
          valor={produto.estoque_minimo ? `${produto.estoque_minimo} ${produto.unidade_codigo}` : "—"}
        />
        <Fato rotulo="Código de barras" valor={produto.codigo_barras ?? "—"} />
      </dl>

      {produto.descricao ? (
        <p className="mt-5 max-w-prose text-base text-[#16222b]">{produto.descricao}</p>
      ) : null}

      {caracteristicas.length > 0 ? (
        <div className="mt-5 flex flex-wrap gap-2">
          {caracteristicas.map((item) => (
            <span
              key={item}
              className="rounded-full bg-[#f7f8f8] px-3 py-1 text-sm text-[#5b6b75]"
            >
              {item}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
