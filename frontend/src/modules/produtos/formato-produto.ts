import type { Produto } from "./types";

/** Reconstrói o FormData que `atualizarProduto` espera, a partir de um produto
 * já carregado — usado pelo "Desfazer", pra restaurar os valores de antes da edição. */
export function produtoParaFormData(produto: Produto): FormData {
  const dados = new FormData();
  dados.set("nome", produto.nome);
  dados.set("sku", produto.sku);
  dados.set("unidade_codigo", produto.unidade_codigo);
  dados.set("categoria_id", produto.categoria_id ?? "");
  dados.set("preco_venda", produto.preco_venda);
  if (produto.custo_medio !== null) {
    dados.set("custo_medio", produto.custo_medio);
  }
  dados.set("vendavel", produto.vendavel ? "true" : "false");
  dados.set("insumo", produto.insumo ? "true" : "false");
  dados.set("controla_estoque", produto.controla_estoque ? "true" : "false");
  dados.set("estoque_minimo", produto.estoque_minimo ?? "");
  dados.set("codigo_barras", produto.codigo_barras ?? "");
  dados.set("descricao", produto.descricao ?? "");
  dados.set("publicado_na_vitrine", produto.publicado_na_vitrine ? "true" : "false");
  return dados;
}
