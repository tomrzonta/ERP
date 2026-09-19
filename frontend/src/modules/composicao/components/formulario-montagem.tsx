"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import type { EstadoFormulario } from "@/modules/auth/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioMontagem({ acao, unidadeBase }: { acao: Acao; unidadeBase: string }) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <CampoNumero
        nome="quantidade"
        formato="quantidade"
        unidade={unidadeBase}
        positivo
        rotulo={`Quantidade a montar (${unidadeBase})`}
        required
        dica="Dá baixa exata nos componentes (com a perda, se houver) e credita esta quantidade."
      />
      <Campo nome="origem" rotulo="Origem" placeholder="Produção do dia..." maxLength={60} />
      <div>
        <BotaoEnviar carregando="Montando...">Montar</BotaoEnviar>
      </div>
    </form>
  );
}
