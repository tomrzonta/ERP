/**
 * Gráficos em SVG puro (sem biblioteca): renderizam no servidor, sem JS no
 * navegador. Cada elemento tem <title>, que vira dica ao passar o mouse, e
 * todo gráfico vem com legenda/rótulos em texto, pra não depender só de cor.
 */

export const CORES = ["#0f6d5c", "#3f6fb5", "#d9a441", "#8b5fbf", "#c4573f", "#7a8a94"];

const compacto = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});

const completo = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export type PontoColuna = { rotulo: string; valor: number; dica?: string };

/** Colunas verticais (ex. faturamento por dia). */
export function GraficoColunas({ pontos, altura = 220 }: { pontos: PontoColuna[]; altura?: number }) {
  const largura = 720;
  const margemEsq = 58;
  const margemBaixo = 26;
  const margemTopo = 10;
  const areaW = largura - margemEsq - 8;
  const areaH = altura - margemBaixo - margemTopo;
  const maximo = Math.max(1, ...pontos.map((p) => p.valor));
  const passo = areaW / Math.max(pontos.length, 1);
  const larguraColuna = Math.max(2, passo * 0.7);
  // No máximo ~8 rótulos no eixo x, sempre incluindo o primeiro.
  const cadaQuantos = Math.max(1, Math.ceil(pontos.length / 8));

  return (
    <svg
      viewBox={`0 0 ${largura} ${altura}`}
      role="img"
      aria-label="Gráfico de colunas"
      className="w-full"
    >
      {[0, 0.5, 1].map((fracao) => {
        const y = margemTopo + areaH - areaH * fracao;
        return (
          <g key={fracao}>
            <line x1={margemEsq} x2={largura - 8} y1={y} y2={y} stroke="#e6ebed" />
            <text x={margemEsq - 6} y={y + 4} textAnchor="end" fontSize="11" fill="#5b6b75">
              {compacto.format(maximo * fracao)}
            </text>
          </g>
        );
      })}
      {pontos.map((ponto, indice) => {
        const alturaColuna = (ponto.valor / maximo) * areaH;
        const x = margemEsq + indice * passo + (passo - larguraColuna) / 2;
        return (
          <g key={indice}>
            <rect
              x={x}
              y={margemTopo + areaH - alturaColuna}
              width={larguraColuna}
              height={ponto.valor > 0 ? Math.max(alturaColuna, 1) : 0}
              rx={2}
              fill={CORES[0]}
            >
              <title>{ponto.dica ?? `${ponto.rotulo}: ${completo.format(ponto.valor)}`}</title>
            </rect>
            {indice % cadaQuantos === 0 ? (
              <text
                x={x + larguraColuna / 2}
                y={altura - 8}
                textAnchor="middle"
                fontSize="11"
                fill="#5b6b75"
              >
                {ponto.rotulo}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

export type Fatia = { rotulo: string; valor: number; texto: string };

/** Rosca com o total no centro e legenda ao lado. */
export function GraficoRosca({
  fatias,
  centro,
  legendaCom,
}: {
  fatias: Fatia[];
  centro: string;
  /** Mostra também a porcentagem de cada fatia na legenda. */
  legendaCom?: "porcentagem";
}) {
  const total = fatias.reduce((soma, f) => soma + f.valor, 0);
  let acumulado = 0;

  return (
    <div className="flex flex-wrap items-center gap-6">
      <svg viewBox="0 0 42 42" role="img" aria-label="Gráfico de rosca" className="size-40 shrink-0">
        <circle cx="21" cy="21" r="15.9155" fill="none" stroke="#f0f3f4" strokeWidth="6" />
        {total > 0
          ? fatias.map((fatia, indice) => {
              const percentual = (fatia.valor / total) * 100;
              const deslocamento = 25 - acumulado; // começa no topo
              acumulado += percentual;
              return (
                <circle
                  key={fatia.rotulo}
                  cx="21"
                  cy="21"
                  r="15.9155"
                  fill="none"
                  stroke={CORES[indice % CORES.length]}
                  strokeWidth="6"
                  strokeDasharray={`${percentual} ${100 - percentual}`}
                  strokeDashoffset={deslocamento}
                >
                  <title>{`${fatia.rotulo}: ${fatia.texto} (${percentual.toFixed(1).replace(".", ",")}%)`}</title>
                </circle>
              );
            })
          : null}
        <text x="21" y="22.5" textAnchor="middle" fontSize="4.6" fontWeight="600" fill="#16222b">
          {centro}
        </text>
      </svg>
      <ul className="min-w-40 flex-1 space-y-2 text-sm">
        {fatias.map((fatia, indice) => (
          <li key={fatia.rotulo} className="flex items-center gap-2">
            <span
              className="size-3 shrink-0 rounded-sm"
              style={{ background: CORES[indice % CORES.length] }}
              aria-hidden="true"
            />
            <span className="text-[#16222b]">{fatia.rotulo}</span>
            <span className="ml-auto tabular-nums text-[#5b6b75]">
              {fatia.texto}
              {legendaCom === "porcentagem" && total > 0
                ? ` · ${((fatia.valor / total) * 100).toFixed(1).replace(".", ",")}%`
                : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export type Barra = { rotulo: string; valor: number; texto: string; detalhe?: string };

/** Barras horizontais com rótulo e valor (ex. mais vendidos). */
export function GraficoBarras({ barras }: { barras: Barra[] }) {
  const maximo = Math.max(1, ...barras.map((b) => b.valor));
  return (
    <ul className="space-y-3">
      {barras.map((barra) => (
        <li key={barra.rotulo}>
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className="truncate font-medium text-[#16222b]">{barra.rotulo}</span>
            <span className="shrink-0 tabular-nums text-[#16222b]">{barra.texto}</span>
          </div>
          <div className="mt-1 h-2.5 rounded bg-[#f0f3f4]">
            <div
              className="h-2.5 rounded"
              style={{ width: `${(barra.valor / maximo) * 100}%`, background: CORES[0] }}
            />
          </div>
          {barra.detalhe ? <p className="mt-0.5 text-xs text-[#5b6b75]">{barra.detalhe}</p> : null}
        </li>
      ))}
    </ul>
  );
}
