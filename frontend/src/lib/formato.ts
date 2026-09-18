/** Formatação para exibição. A API envia números decimais como texto. */

export function moeda(valor: string | number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    Number(valor),
  );
}

export function numero(valor: string | number, casas = 2): string {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(Number(valor));
}

export function porcentagem(valor: string | number): string {
  return `${numero(valor, 1)}%`;
}
