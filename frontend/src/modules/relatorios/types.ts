/** A API envia valores decimais como texto, para não perder precisão. */

import type { FormaPagamento } from "@/lib/formas-pagamento";

export type { FormaPagamento };

export type DiaVendas = {
  data: string; // AAAA-MM-DD
  quantidade: number;
  faturamento: string;
};

export type ProdutoVendido = {
  produto_id: string;
  nome: string;
  quantidade: string;
  unidade_codigo: string;
  receita: string;
};

export type ResumoClientes = {
  inicio: string;
  fim: string;
  clientes_que_compraram: number;
  novos: number;
  recorrentes: number;
  compras_de_clientes: number;
  valor_de_clientes: string;
  ticket_medio: string | null;
  compras_por_cliente: string | null;
  vendas_sem_cliente: number;
  valor_sem_cliente: string;
  melhores: { cliente_id: string; nome: string; compras: number; valor: string }[];
};

export type ResumoDescontos = {
  inicio: string;
  fim: string;
  receita_de_tabela: string;
  descontos: string;
  receita_final: string;
  percentual_de_desconto: string | null;
  itens_com_desconto: number;
  vendas_com_desconto: number;
  lucro_sem_desconto: string | null;
  lucro_com_desconto: string | null;
  lucro_cedido_percentual: string | null;
  produtos: { produto_id: string; nome: string; desconto: string; percentual: string }[];
};

export type ResumoInsumos = {
  inicio: string;
  fim: string;
  custo_total: string | null;
  custo_dos_ajustes: string | null;
  insumos: {
    produto_id: string;
    nome: string;
    unidade_codigo: string;
    consumido_em_montagens: string;
    baixado_por_ajuste: string;
    custo_das_montagens: string | null;
    custo_dos_ajustes: string | null;
    custo_total: string | null;
  }[];
};

export type Resumo = {
  inicio: string;
  fim: string;
  quantidade_vendas: number;
  faturamento: string;
  ticket_medio: string | null;
  descontos: string;
  cancelamentos: number;
  lucro_bruto: string | null;
  margem_percentual: string | null;
  por_dia: DiaVendas[];
  mais_vendidos: ProdutoVendido[];
  por_forma_pagamento: { forma: FormaPagamento; valor: string }[];
};
