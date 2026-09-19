/** A API envia valores decimais como texto, para não perder precisão. */

export type TipoMovimento = "entrada" | "saida" | "ajuste" | "montagem" | "reserva" | "liberacao";

export type Movimento = {
  id: string;
  produto_id: string;
  tipo: TipoMovimento;
  quantidade: string;
  custo_unitario: string | null;
  origem: string | null;
  ocorrido_em: string;
  registrado_em: string;
};

export type Saldo = {
  produto_id: string;
  fisico: string;
  reservado: string;
  disponivel: string;
};

export type SaldoComProduto = {
  produto_id: string;
  nome: string;
  sku: string;
  unidade_codigo: string;
  fisico: string;
  reservado: string;
  disponivel: string;
};

export type AlertaEstoque = {
  produto_id: string;
  nome: string;
  sku: string;
  unidade_codigo: string;
  tipo: "negativo" | "baixo";
  fisico: string;
  disponivel: string;
  estoque_minimo: string | null;
};
