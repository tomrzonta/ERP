"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import { Marcador } from "@/components/ui/marcador";
import type { EstadoFormulario } from "@/modules/auth/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioUnidade({
  acao,
  unidadeBase,
}: {
  acao: Acao;
  unidadeBase: string;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo nome="nome" rotulo="Nome" placeholder="Fatia, rolo, caixa" required maxLength={30} />
        <CampoNumero
          nome="fator"
          formato="quantidade"
          positivo
          rotulo={`Quanto vale em ${unidadeBase}`}
          required
          dica="Fatia de bolo: 0,125. Rolo de filamento: 1000."
        />
      </div>
      <div className="flex flex-col gap-3">
        <Marcador nome="usa_na_compra" rotulo="Usar nas compras" defaultChecked />
        <Marcador nome="usa_na_venda" rotulo="Usar nas vendas" defaultChecked />
      </div>
      <div>
        <BotaoEnviar carregando="Adicionando...">Adicionar unidade</BotaoEnviar>
      </div>
    </form>
  );
}
