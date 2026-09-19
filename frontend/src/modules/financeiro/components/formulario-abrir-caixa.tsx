"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import type { EstadoFormulario } from "@/modules/auth/types";
import { abrirCaixa } from "../actions";

export function FormularioAbrirCaixa({ aoConcluir }: { aoConcluir?: () => void }) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(async (anterior, dados) => {
    const resultado = await abrirCaixa(anterior, dados);
    if (resultado && !resultado.erro) aoConcluir?.();
    return resultado;
  }, undefined);

  return (
    <form action={enviar} className="flex max-w-sm flex-col gap-5">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}

      <CampoNumero
        nome="valor_inicial"
        formato="dinheiro"
        rotulo="Valor inicial"
        valorInicial="0"
        dica="O que já está na gaveta antes de começar a vender."
      />
      <Campo nome="observacao" rotulo="Observação (opcional)" maxLength={500} />

      <BotaoEnviar carregando="Abrindo...">Abrir caixa</BotaoEnviar>
    </form>
  );
}
