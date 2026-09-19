export type OrigemCliente = "balcao" | "vitrine" | "marketplace";

export type Cliente = {
  id: string;
  nome: string;
  telefone: string | null;
  email: string | null;
  cpf: string | null;
  data_nascimento: string | null;
  endereco: string | null;
  consentimento_marketing: boolean;
  origem: OrigemCliente;
  anonimizado_em: string | null;
};

export type MetricasCliente = {
  quantidade_compras: number;
  valor_total: string;
  ticket_medio: string | null;
  primeira_compra: string | null;
  ultima_compra: string | null;
};
