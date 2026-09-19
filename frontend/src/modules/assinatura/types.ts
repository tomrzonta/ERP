export type UsoDoLimite = {
  chave: string;
  rotulo: string;
  usado: number;
  /** Nulo = ilimitado no plano atual. */
  limite: number | null;
  percentual: string | null;
};

export type Uso = { plano: string; limites: UsoDoLimite[] };
