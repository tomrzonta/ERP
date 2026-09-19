import { moeda } from "@/lib/formato";
import { ErroApi } from "@/lib/server/api";
import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { PainelContas } from "@/modules/financeiro/components/painel-contas";
import type { Conta, FluxoProjetado } from "@/modules/financeiro/types";

export const metadata = { title: "Contas a pagar e receber · ERP" };

const DIAS_PROJETADOS = 30;

function dataCurta(iso: string): string {
  const [, mes, dia] = iso.split("-");
  return `${dia}/${mes}`;
}

export default async function ContasPage() {
  const eu = await obterEu();

  let contas: Conta[];
  let fluxo: FluxoProjetado;
  try {
    contas = await carregarDaSessao<Conta[]>("/contas?limite=200");
    fluxo = await carregarDaSessao<FluxoProjetado>(
      `/contas/fluxo-projetado?dias=${DIAS_PROJETADOS}`,
    );
  } catch (erro) {
    if (erro instanceof ErroApi && erro.codigo === "recurso_do_plano") {
      return (
        <div className="mx-auto max-w-3xl px-6 py-10">
          <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
            Contas a pagar e receber
          </h1>
          <p className="mt-6 rounded-lg border border-[#dbe1e4] bg-white p-5 text-[#5b6b75]">
            Este recurso faz parte do plano Pro. Com ele você cadastra contas com vencimento e
            acompanha o fluxo de caixa projetado.
          </p>
        </div>
      );
    }
    throw erro;
  }

  // Só dias com movimento, pra tabela não virar uma lista de 30 linhas vazias.
  const diasComMovimento = fluxo.dias.filter(
    (dia) => Number(dia.a_receber) !== 0 || Number(dia.a_pagar) !== 0,
  );
  const saldoFinal = fluxo.dias.at(-1)?.saldo_acumulado ?? "0";

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
        Contas a pagar e receber
      </h1>

      <section className="mt-8">
        <h2 className="font-medium text-[#16222b]">
          Fluxo projetado · próximos {DIAS_PROJETADOS} dias
        </h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-[#dbe1e4] bg-white p-4">
            <p className="text-sm text-[#5b6b75]">Vencidas a receber</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-[#0f6d5c]">
              {moeda(fluxo.atrasadas_a_receber)}
            </p>
          </div>
          <div className="rounded-lg border border-[#dbe1e4] bg-white p-4">
            <p className="text-sm text-[#5b6b75]">Vencidas a pagar</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-[#a33a2a]">
              {moeda(fluxo.atrasadas_a_pagar)}
            </p>
          </div>
          <div className="rounded-lg border border-[#dbe1e4] bg-white p-4">
            <p className="text-sm text-[#5b6b75]">Resultado líquido no período</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-[#16222b]">
              {moeda(saldoFinal)}
            </p>
          </div>
        </div>

        {diasComMovimento.length === 0 ? (
          <p className="mt-4 text-sm text-[#5b6b75]">Nenhuma conta vence neste período.</p>
        ) : (
          <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-4 py-3 font-medium">Dia</th>
                  <th className="px-4 py-3 text-right font-medium">A receber</th>
                  <th className="px-4 py-3 text-right font-medium">A pagar</th>
                  <th className="px-4 py-3 text-right font-medium">Acumulado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dbe1e4]">
                {diasComMovimento.map((dia) => (
                  <tr key={dia.data}>
                    <td className="px-4 py-3 tabular-nums">{dataCurta(dia.data)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{moeda(dia.a_receber)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{moeda(dia.a_pagar)}</td>
                    <td
                      className={`px-4 py-3 text-right font-medium tabular-nums ${
                        Number(dia.saldo_acumulado) < 0 ? "text-[#a33a2a]" : "text-[#16222b]"
                      }`}
                    >
                      {moeda(dia.saldo_acumulado)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <PainelContas contas={contas} podeOperar={eu.permissoes.includes("financeiro.operar")} />
    </div>
  );
}
