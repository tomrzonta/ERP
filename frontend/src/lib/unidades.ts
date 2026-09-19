/** Casas decimais **digitadas** por unidade de medida (0,000 g, 0,000 kg...).
 * Peso e volume usam 3 casas; contagem, nenhuma. Não é o mesmo que
 * `casas_exibidas` do backend, que só arredonda a exibição em listas. */
const CASAS_POR_UNIDADE: Record<string, number> = {
  un: 0,
  g: 3,
  kg: 3,
  ml: 3,
  l: 3,
  cm: 1,
  m: 2,
  m2: 2,
};

/** Quando a unidade ainda não é conhecida (ex. escolhida no mesmo formulário). */
export const CASAS_QUANTIDADE_PADRAO = 3;

export function casasDaUnidade(codigo: string | undefined): number {
  if (!codigo) return CASAS_QUANTIDADE_PADRAO;
  return CASAS_POR_UNIDADE[codigo] ?? CASAS_QUANTIDADE_PADRAO;
}
