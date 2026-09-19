import Link from "next/link";

import { carregarDaSessao } from "@/lib/server/sessao";
import { PainelCaixaAberto } from "@/modules/financeiro/components/painel-caixa-aberto";
import type { Caixa } from "@/modules/financeiro/types";

export const metadata = { title: "Caixa do dia · ERP" };

export default async function CaixaPage() {
  const caixa = await carregarDaSessao<Caixa | null>("/caixa/aberto");

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Caixa do dia</h1>
        <Link href="/caixa/historico" className="text-sm text-[#0f6d5c] hover:underline">
          Ver histórico de caixas
        </Link>
      </div>

      {caixa ? (
        <div className="mt-8">
          <PainelCaixaAberto caixa={caixa} />
        </div>
      ) : (
        <div className="mt-8 max-w-prose text-sm text-[#5b6b75]">
          <p>
            Nenhum caixa aberto agora. O caixa é aberto pela tela de{" "}
            <Link href="/vendas" className="text-[#0f6d5c] hover:underline">
              Vendas
            </Link>
            , no botão do topo. Abrir não é obrigatório pra vender — mas, enquanto aberto, toda
            venda fechada vira lançamento automático aqui.
          </p>
        </div>
      )}
    </div>
  );
}
