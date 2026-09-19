/** Formas de pagamento. `cartao` (genérico) só existe no histórico anterior à
 * separação em crédito e débito: aparece nos relatórios, mas não é oferecido
 * pra novos pagamentos. */
export type FormaPagamento = "dinheiro" | "cartao" | "cartao_credito" | "cartao_debito" | "pix";

export const ROTULOS_FORMA: Record<FormaPagamento, string> = {
  dinheiro: "Dinheiro",
  cartao_credito: "Cartão de crédito",
  cartao_debito: "Cartão de débito",
  pix: "Pix",
  cartao: "Cartão (antes da separação)",
};

/** O que os formulários oferecem, na ordem de exibição. */
export const FORMAS_SELECIONAVEIS: FormaPagamento[] = [
  "dinheiro",
  "cartao_credito",
  "cartao_debito",
  "pix",
];
