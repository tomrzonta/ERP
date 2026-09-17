/** A API envia valores decimais como texto, para não perder precisão. */

export type Unidade = {
  codigo: string;
  nome: string;
  grandeza: string;
  casas_exibidas: number;
};

export type Categoria = {
  id: string;
  nome: string;
  categoria_pai_id: string | null;
};

export type Produto = {
  id: string;
  sku: string;
  nome: string;
  tipo: "simples" | "composto";
  status: "ativo" | "inativo" | "congelado";
  unidade_codigo: string;
  categoria_id: string | null;
  vendavel: boolean;
  insumo: boolean;
  controla_estoque: boolean;
  preco_venda: string;
  codigo_barras: string | null;
  descricao: string | null;
  publicado_na_vitrine: boolean;
  custo_medio: string | null;
  margem_percentual: string | null;
};

export type UnidadeAlternativa = {
  id: string;
  nome: string;
  fator: string;
  usa_na_compra: boolean;
  usa_na_venda: boolean;
};
