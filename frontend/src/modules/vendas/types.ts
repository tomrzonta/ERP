/** A API envia valores decimais como texto, para não perder precisão. */

export type CanalVenda = "pdv" | "vitrine" | "marketplace";
import type { FormaPagamento } from "@/lib/formas-pagamento";

export type { FormaPagamento };
export type StatusVenda = "aberto" | "fechado" | "cancelado";

export type ItemVenda = {
  id: string;
  produto_id: string;
  quantidade: string;
  preco_tabela: string;
  desconto: string;
  preco_final: string;
  custo_unitario: string | null;
};

export type PagamentoVenda = {
  id: string;
  forma: FormaPagamento;
  valor: string;
};

export type Venda = {
  id: string;
  numero: string;
  cliente_id: string | null;
  vendedor_usuario_id: string;
  canal: CanalVenda;
  status: StatusVenda;
  subtotal: string;
  desconto_total: string;
  total: string;
  ocorrido_em: string;
  fechado_em: string | null;
  cancelado_em: string | null;
  itens: ItemVenda[];
  pagamentos: PagamentoVenda[];
};
