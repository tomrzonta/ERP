"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { entrar } from "../actions";
import type { EstadoFormulario } from "../types";

export function FormularioEntrar() {
  const [estado, acao] = useActionState<EstadoFormulario, FormData>(entrar, undefined);

  return (
    <form action={acao} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <Campo
        nome="email"
        rotulo="E-mail"
        tipo="email"
        autoComplete="email"
        required
        placeholder="voce@exemplo.com"
      />
      <Campo nome="senha" rotulo="Senha" tipo="password" autoComplete="current-password" required />
      <BotaoEnviar carregando="Entrando...">Entrar</BotaoEnviar>
    </form>
  );
}
