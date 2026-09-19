import type { Cliente } from "./types";

/** Reconstrói o FormData que `atualizarCliente` espera, a partir de um cliente
 * já carregado — usado pelo "Desfazer", pra restaurar os valores de antes da edição. */
export function clienteParaFormData(cliente: Cliente): FormData {
  const dados = new FormData();
  dados.set("nome", cliente.nome);
  dados.set("telefone", cliente.telefone ?? "");
  dados.set("email", cliente.email ?? "");
  dados.set("cpf", cliente.cpf ?? "");
  dados.set("data_nascimento", cliente.data_nascimento ?? "");
  dados.set("endereco", cliente.endereco ?? "");
  dados.set("consentimento_marketing", cliente.consentimento_marketing ? "true" : "false");
  return dados;
}
