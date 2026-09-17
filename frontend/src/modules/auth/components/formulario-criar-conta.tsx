"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { criarConta } from "../actions";
import type { EstadoFormulario } from "../types";

export function FormularioCriarConta() {
  const [estado, acao] = useActionState<EstadoFormulario, FormData>(criarConta, undefined);

  return (
    <form action={acao} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <Campo nome="nome" rotulo="Seu nome" autoComplete="name" required />
      <Campo
        nome="nome_empresa"
        rotulo="Nome do negócio"
        autoComplete="organization"
        required
        placeholder="Ateliê da Maria"
      />
      <Campo nome="email" rotulo="E-mail" tipo="email" autoComplete="email" required />
      <Campo
        nome="senha"
        rotulo="Senha"
        tipo="password"
        autoComplete="new-password"
        required
        minLength={8}
        dica="No mínimo 8 caracteres."
      />
      <BotaoEnviar carregando="Criando conta...">Criar conta</BotaoEnviar>
    </form>
  );
}
