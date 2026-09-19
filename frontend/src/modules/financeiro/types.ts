/** A API envia valores decimais como texto, para não perder precisão. */

export type StatusCaixa = "aberto" | "fechado";
export type TipoLancamento = "entrada" | "saida";
export type OrigemLancamento = "venda" | "manual";
import type { FormaPagamento } from "@/lib/formas-pagamento";

export type { FormaPagamento };

export type Lancamento = {
  id: string;
  tipo: TipoLancamento;
  origem: OrigemLancamento;
  forma_pagamento: FormaPagamento;
  valor: string;
  descricao: string | null;
  venda_id: string | null;
  ocorrido_em: string;
};

export type ResumoCaixa = {
  total_entradas: string;
  total_saidas: string;
  saldo_esperado_dinheiro: string;
  diferenca: string | null;
};

export type Caixa = {
  id: string;
  status: StatusCaixa;
  valor_inicial: string;
  valor_contado: string | null;
  observacao: string | null;
  aberto_por_usuario_id: string;
  aberto_por_nome: string | null;
  fechado_por_usuario_id: string | null;
  fechado_por_nome: string | null;
  aberto_em: string;
  fechado_em: string | null;
  resumo: ResumoCaixa;
  lancamentos: Lancamento[];
};

export type TipoConta = "pagar" | "receber";
export type StatusConta = "aberta" | "paga" | "cancelada";

export type Conta = {
  id: string;
  tipo: TipoConta;
  status: StatusConta;
  descricao: string;
  contraparte: string | null;
  valor: string;
  vencimento: string; // AAAA-MM-DD
  pago_em: string | null;
  forma_pagamento: FormaPagamento | null;
  vencida: boolean;
};

export type DiaProjetado = {
  data: string; // AAAA-MM-DD
  a_receber: string;
  a_pagar: string;
  saldo_acumulado: string;
};

export type FluxoProjetado = {
  atrasadas_a_receber: string;
  atrasadas_a_pagar: string;
  dias: DiaProjetado[];
};
