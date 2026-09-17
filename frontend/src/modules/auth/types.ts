export type Tokens = { access_token: string; refresh_token: string };

export type EmpresaDisponivel = { id: string; nome: string; papel: string };

export type RespostaLogin = {
  tokens: Tokens;
  empresa_ativa_id: string | null;
  empresas: EmpresaDisponivel[];
};

export type Eu = {
  usuario: { id: string; nome: string; email: string };
  empresa: { id: string; nome: string; slug: string };
  papel: string;
  permissoes: string[];
  plano: string;
};

/** Estado devolvido pelas Server Actions dos formulários. */
export type EstadoFormulario = { erro: string } | undefined;
