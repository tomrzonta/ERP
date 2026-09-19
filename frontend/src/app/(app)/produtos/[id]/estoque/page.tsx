import Link from "next/link";

import { numero } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { montar } from "@/modules/composicao/actions";
import { FormularioMontagem } from "@/modules/composicao/components/formulario-montagem";
import { registrarAjuste, registrarEntrada } from "@/modules/estoque/actions";
import { FormularioAjuste } from "@/modules/estoque/components/formulario-ajuste";
import { FormularioEntrada } from "@/modules/estoque/components/formulario-entrada";
import type { Movimento, Saldo, TipoMovimento } from "@/modules/estoque/types";
import type { Produto, Unidade, UnidadeAlternativa } from "@/modules/produtos/types";

const ROTULOS_TIPO: Record<TipoMovimento, string> = {
  entrada: "Entrada",
  saida: "Saída",
  ajuste: "Ajuste",
  montagem: "Montagem",
  reserva: "Reserva",
  liberacao: "Liberação",
};

export default async function EstoqueDoProdutoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const eu = await obterEu();
  const [produto, saldo, alternativas, unidades, movimentos] = await Promise.all([
    carregarDaSessao<Produto>(`/produtos/${id}`),
    carregarDaSessao<Saldo>(`/estoque/produtos/${id}/saldo`),
    carregarDaSessao<UnidadeAlternativa[]>(`/produtos/${id}/unidades`),
    carregarDaSessao<Unidade[]>("/unidades"),
    carregarDaSessao<Movimento[]>(`/estoque/movimentos?produto_id=${id}`),
  ]);

  const casas = unidades.find((unidade) => unidade.codigo === produto.unidade_codigo)
    ?.casas_exibidas ?? 2;
  const podeMovimentar = eu.permissoes.includes("estoque.movimentar");
  const podeAjustar = eu.permissoes.includes("estoque.ajustar");

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href={`/produtos/${id}`} className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para {produto.nome}
      </Link>
      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[#16222b]">
        Estoque de {produto.nome}
      </h1>

      {!produto.controla_estoque ? (
        <p className="mt-8 rounded-md border border-[#a8341f]/25 bg-[#a8341f]/5 px-3 py-2 text-sm text-[#a8341f]">
          Este produto não controla estoque. Ative &quot;Controla estoque&quot; nos dados do
          produto para movimentar.
        </p>
      ) : (
        <>
          <dl className="mt-8 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-3">
            <div className="bg-white px-4 py-5">
              <dt className="text-sm text-[#5b6b75]">Físico</dt>
              <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
                {numero(saldo.fisico, casas)} {produto.unidade_codigo}
              </dd>
            </div>
            <div className="bg-white px-4 py-5">
              <dt className="text-sm text-[#5b6b75]">Reservado</dt>
              <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
                {numero(saldo.reservado, casas)} {produto.unidade_codigo}
              </dd>
            </div>
            <div className="bg-white px-4 py-5">
              <dt className="text-sm text-[#5b6b75]">Disponível</dt>
              <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
                {numero(saldo.disponivel, casas)} {produto.unidade_codigo}
              </dd>
            </div>
          </dl>

          {podeMovimentar && produto.tipo === "kit" ? (
            <section className="mt-10">
              <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Montar</h2>
              <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
                Dá baixa exata nos componentes (veja a receita nos dados do produto) e credita
                o saldo deste produto, com o custo calculado a partir do que foi consumido.
              </p>
              <div className="mt-5 max-w-xl">
                <FormularioMontagem acao={montar.bind(null, id)} unidadeBase={produto.unidade_codigo} />
              </div>
            </section>
          ) : null}

          {podeMovimentar ? (
            <section className="mt-12 border-t border-[#dbe1e4] pt-8">
              <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
                Registrar entrada
              </h2>
              <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
                {produto.tipo === "kit"
                  ? "Para unidades compradas prontas, fora da montagem."
                  : "Compras e reposições. O custo médio é recalculado automaticamente."}
              </p>
              <div className="mt-5 max-w-xl">
                <FormularioEntrada
                  acao={registrarEntrada.bind(null, id)}
                  unidadeBase={produto.unidade_codigo}
                  unidadesAlternativas={alternativas}
                />
              </div>
            </section>
          ) : null}

          {podeAjustar ? (
            <section className="mt-12 border-t border-[#dbe1e4] pt-8">
              <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
                Ajustar por contagem
              </h2>
              <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
                Use depois de contar o estoque físico. O sistema calcula a diferença sozinho.
              </p>
              <div className="mt-5 max-w-xl">
                <FormularioAjuste
                  acao={registrarAjuste.bind(null, id)}
                  unidadeBase={produto.unidade_codigo}
                  saldoAtual={saldo.fisico}
                />
              </div>
            </section>
          ) : null}
        </>
      )}

      <section className="mt-12 border-t border-[#dbe1e4] pt-8">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
          Movimentações recentes
        </h2>

        {movimentos.length === 0 ? (
          <p className="mt-6 text-sm text-[#5b6b75]">Nenhuma movimentação ainda.</p>
        ) : (
          <div className="mt-6 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Quando</th>
                  <th className="px-4 py-3 font-medium">Tipo</th>
                  <th className="px-4 py-3 text-right font-medium">Quantidade</th>
                  <th className="px-4 py-3 font-medium">Origem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {movimentos.map((movimento) => (
                  <tr key={movimento.id}>
                    <td className="px-4 py-3 text-[#5b6b75]">
                      {new Date(movimento.ocorrido_em).toLocaleString("pt-BR")}
                    </td>
                    <td className="px-4 py-3 text-[#16222b]">{ROTULOS_TIPO[movimento.tipo]}</td>
                    <td
                      className={`px-4 py-3 text-right tabular-nums ${
                        Number(movimento.quantidade) < 0 ? "text-[#a8341f]" : "text-[#16222b]"
                      }`}
                    >
                      {numero(movimento.quantidade, casas)} {produto.unidade_codigo}
                    </td>
                    <td className="px-4 py-3 text-[#5b6b75]">{movimento.origem ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
