"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import type { EstadoFormulario } from "@/modules/auth/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioAjuste({
  acao,
  unidadeBase,
  saldoAtual,
}: {
  acao: Acao;
  unidadeBase: string;
  saldoAtual: string;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}

      <CampoNumero
        nome="quantidade_contada"
        formato="quantidade"
        unidade={unidadeBase}
        rotulo={`Quantidade contada (${unidadeBase})`}
        required
        valorInicial={saldoAtual}
        dica="O saldo vira exatamente esse número; a diferença entra no histórico como ajuste."
      />

      <Campo
        nome="origem"
        rotulo="Origem"
        placeholder="Contagem mensal, balanço..."
        maxLength={60}
      />

      <div>
        <BotaoEnviar carregando="Ajustando...">Registrar ajuste</BotaoEnviar>
      </div>
    </form>
  );
}
