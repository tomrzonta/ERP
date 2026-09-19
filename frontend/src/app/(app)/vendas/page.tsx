import { SincronizarCatalogo } from "@/components/pwa/sincronizar-catalogo";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import type { Cliente } from "@/modules/clientes/types";
import { BarraCaixa } from "@/modules/financeiro/components/barra-caixa";
import type { Caixa } from "@/modules/financeiro/types";
import type { SaldoComProduto } from "@/modules/estoque/types";
import type { Produto } from "@/modules/produtos/types";
import { PainelVendas } from "@/modules/vendas/components/painel-vendas";
import type { Venda } from "@/modules/vendas/types";

export const metadata = { title: "Vendas · ERP" };

export default async function VendasPage({
  searchParams,
}: {
  searchParams: Promise<{ ticket?: string }>;
}) {
  const { ticket } = await searchParams;
  const eu = await obterEu();
  const podeVerCaixa = eu.permissoes.includes("financeiro.ver");
  const [vendas, produtos, clientes, saldos, caixa] = await Promise.all([
    carregarDaSessao<Venda[]>("/vendas?limite=100"),
    carregarDaSessao<Produto[]>("/produtos?apenas_vendaveis=true&limite=200"),
    carregarDaSessao<Cliente[]>("/clientes?limite=200"),
    carregarDaSessao<SaldoComProduto[]>("/estoque/saldos?limite=200"),
    podeVerCaixa ? carregarDaSessao<Caixa | null>("/caixa/aberto") : Promise.resolve(null),
  ]);
  const saldosPorProduto = new Map(saldos.map((saldo) => [saldo.produto_id, saldo]));
  const catalogoOffline = produtos.map((produto) => {
    const saldo = saldosPorProduto.get(produto.id);
    return {
      id: produto.id,
      sku: produto.sku,
      nome: produto.nome,
      unidade_codigo: produto.unidade_codigo,
      preco_venda: produto.preco_venda,
      controla_estoque: produto.controla_estoque,
      fisico: saldo?.fisico ?? null,
      reservado: saldo?.reservado ?? null,
      disponivel: saldo?.disponivel ?? null,
    };
  });

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Vendas</h1>
        {podeVerCaixa ? (
          <BarraCaixa caixa={caixa} podeOperar={eu.permissoes.includes("financeiro.operar")} />
        ) : null}
      </div>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Cada venda é um ticket: fica aberto enquanto você adiciona itens, e só vira histórico de
        verdade quando fechado (pago) ou cancelado.
      </p>

      <SincronizarCatalogo produtos={catalogoOffline} />

      <div className="mt-8">
        <PainelVendas
          vendasIniciais={vendas}
          produtos={produtos}
          clientes={clientes}
          podeRegistrar={eu.permissoes.includes("vendas.registrar")}
          podeCancelarFechada={eu.permissoes.includes("vendas.cancelar")}
          ticketInicial={ticket}
        />
      </div>
    </div>
  );
}
