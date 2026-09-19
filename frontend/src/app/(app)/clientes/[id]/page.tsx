import Link from "next/link";

import { moeda } from "@/lib/formato";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { AcoesLgpd } from "@/modules/clientes/components/acoes-lgpd";
import { BotaoEditarCliente } from "@/modules/clientes/components/botao-editar-cliente";
import { MesclarCliente } from "@/modules/clientes/components/mesclar-cliente";
import type { Cliente, MetricasCliente } from "@/modules/clientes/types";
import type { Venda } from "@/modules/vendas/types";

export default async function ClientePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const eu = await obterEu();
  const podeEditar = eu.permissoes.includes("clientes.editar");

  const [cliente, metricas, compras, clientes] = await Promise.all([
    carregarDaSessao<Cliente>(`/clientes/${id}`),
    carregarDaSessao<MetricasCliente>(`/clientes/${id}/metricas`),
    carregarDaSessao<Venda[]>(`/vendas?cliente_id=${id}&status=fechado&limite=100`),
    podeEditar
      ? carregarDaSessao<Cliente[]>("/clientes?limite=200")
      : Promise.resolve<Cliente[]>([]),
  ]);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/clientes" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para clientes
      </Link>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">{cliente.nome}</h1>
          <p className="mt-1 text-sm text-[#5b6b75]">
            {cliente.telefone ?? "Sem telefone"}
            {cliente.email ? ` · ${cliente.email}` : ""}
          </p>
        </div>
        {podeEditar && !cliente.anonimizado_em ? <BotaoEditarCliente cliente={cliente} /> : null}
      </div>

      <dl className="mt-8 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-4">
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Compras</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {metricas.quantidade_compras}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Valor total</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {moeda(metricas.valor_total)}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Ticket médio</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {metricas.ticket_medio ? moeda(metricas.ticket_medio) : "—"}
          </dd>
        </div>
        <div className="bg-white px-4 py-5">
          <dt className="text-sm text-[#5b6b75]">Última compra</dt>
          <dd className="mt-1 text-lg font-medium tabular-nums text-[#16222b]">
            {metricas.ultima_compra
              ? new Date(metricas.ultima_compra).toLocaleDateString("pt-BR")
              : "—"}
          </dd>
        </div>
      </dl>

      <section className="mt-10">
        <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
          Histórico de compras
        </h2>
        {compras.length > 0 ? (
          <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Número</th>
                  <th className="px-4 py-3 font-medium">Data</th>
                  <th className="px-4 py-3 text-right font-medium">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {compras.map((venda) => (
                  <tr key={venda.id}>
                    <td className="px-4 py-3">
                      <Link
                        href={`/vendas?ticket=${venda.id}`}
                        className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                      >
                        {venda.numero}
                      </Link>
                    </td>
                    <td className="px-4 py-3 tabular-nums text-[#5b6b75]">
                      {new Date(venda.ocorrido_em).toLocaleString("pt-BR")}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                      {moeda(venda.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[#5b6b75]">Nenhuma compra fechada ainda.</p>
        )}
      </section>

      {podeEditar ? (
        <section className="mt-10 flex flex-col gap-6 border-t border-[#dbe1e4] pt-8">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
              Cadastro duplicado
            </h2>
            <div className="mt-3">
              <MesclarCliente cliente={cliente} clientes={clientes} />
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">
              Dados pessoais (LGPD)
            </h2>
            <div className="mt-3">
              <AcoesLgpd cliente={cliente} />
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
