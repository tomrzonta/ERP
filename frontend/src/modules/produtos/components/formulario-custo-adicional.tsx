"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import type { EstadoFormulario } from "@/modules/auth/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioCustoAdicional({ acao }: { acao: Acao }) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo
          nome="nome"
          rotulo="Nome"
          required
          maxLength={60}
          placeholder="Embalagem, energia..."
        />
        <CampoNumero
          nome="valor"
          formato="custo"
          positivo
          rotulo="Valor por unidade"
          required
        />
      </div>
      <div>
        <BotaoEnviar carregando="Adicionando...">Adicionar custo</BotaoEnviar>
      </div>
    </form>
  );
}
