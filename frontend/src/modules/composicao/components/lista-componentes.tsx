import { numero } from "@/lib/formato";
import { removerComponente } from "@/modules/composicao/actions";
import type { Componente } from "@/modules/composicao/types";

export type ComponenteExibido = Componente & {
  nome: string;
  sku: string;
  unidadeCodigo: string;
};

export function ListaComponentes({
  produtoCompostoId,
  componentes,
  podeEditar,
}: {
  produtoCompostoId: string;
  componentes: ComponenteExibido[];
  podeEditar: boolean;
}) {
  if (componentes.length === 0) {
    return (
      <p className="text-sm text-[#5b6b75]">
        Nenhum componente ainda. Adicione os produtos que entram nesta composição.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
      {componentes.map((componente) => (
        <li
          key={componente.id}
          className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
        >
          <div>
            <span className="font-medium text-[#16222b]">{componente.nome}</span>
            <span className="ml-2 text-xs text-[#5b6b75]">{componente.sku}</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="tabular-nums text-[#5b6b75]">
              {numero(componente.quantidade, 4)} {componente.unidadeCodigo}
              {Number(componente.perda_percentual) > 0
                ? ` · ${numero(componente.perda_percentual, 2)}% de perda`
                : ""}
            </span>
            {podeEditar ? (
              <form action={removerComponente.bind(null, produtoCompostoId, componente.componente_id)}>
                <button
                  type="submit"
                  className="text-xs text-[#a8341f] hover:underline"
                  aria-label={`Remover ${componente.nome} da composição`}
                >
                  Remover
                </button>
              </form>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
