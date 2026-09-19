import { moeda } from "@/lib/formato";
import { adicionarCustoAdicional, removerCustoAdicional } from "../actions";
import type { CustoAdicional } from "../types";
import { FormularioCustoAdicional } from "./formulario-custo-adicional";

export function SecaoCustosAdicionais({
  produtoId,
  custos,
  podeEditar,
}: {
  produtoId: string;
  custos: CustoAdicional[];
  podeEditar: boolean;
}) {
  return (
    <section className="mt-12 border-t border-[#dbe1e4] pt-8">
      <h2 className="text-lg font-semibold tracking-tight text-[#16222b]">Custos adicionais</h2>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Embalagem, energia, mão de obra — some ao custo médio na hora de calcular a margem.
      </p>

      {custos.length > 0 ? (
        <ul className="mt-6 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
          {custos.map((custo) => (
            <li
              key={custo.id}
              className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
            >
              <span className="font-medium text-[#16222b]">{custo.nome}</span>
              <div className="flex items-center gap-4">
                <span className="tabular-nums text-[#5b6b75]">{moeda(custo.valor)}</span>
                {podeEditar ? (
                  <form action={removerCustoAdicional.bind(null, produtoId, custo.id)}>
                    <button
                      type="submit"
                      className="text-xs text-[#a8341f] hover:underline"
                      aria-label={`Remover ${custo.nome}`}
                    >
                      Remover
                    </button>
                  </form>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-6 text-sm text-[#5b6b75]">Nenhum custo adicional ainda.</p>
      )}

      {podeEditar ? (
        <div className="mt-8 max-w-xl">
          <FormularioCustoAdicional acao={adicionarCustoAdicional.bind(null, produtoId)} />
        </div>
      ) : null}
    </section>
  );
}
