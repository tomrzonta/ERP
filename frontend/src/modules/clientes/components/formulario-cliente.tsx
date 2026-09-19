"use client";

import { useActionState, useEffect, useRef } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { Marcador } from "@/components/ui/marcador";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Cliente } from "../types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioCliente({
  acao,
  cliente,
  textoBotao,
  aoSalvar,
}: {
  acao: Acao;
  cliente?: Cliente;
  textoBotao: string;
  /** Só faz sentido editando dentro de um modal: chamado a cada salvamento
   * bem-sucedido, com `true` se o botão clicado foi "Salvar e sair". */
  aoSalvar?: (sair: boolean) => void;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);
  const salvo = estado?.erro === "";

  const sairAoSalvarRef = useRef(false);
  useEffect(() => {
    if (estado?.erro === "") {
      aoSalvar?.(sairAoSalvarRef.current);
      sairAoSalvarRef.current = false;
    }
    // Só reage à mudança do resultado da ação — os refs não precisam disparar de novo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estado]);

  return (
    <form action={enviar} className="flex max-w-xl flex-col gap-5">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      {salvo ? (
        <p className="rounded-md border border-[#0f6d5c]/25 bg-[#0f6d5c]/5 px-3 py-2 text-sm text-[#0f6d5c]">
          Alterações salvas.
        </p>
      ) : null}

      <Campo nome="nome" rotulo="Nome" required defaultValue={cliente?.nome} maxLength={120} />

      <div className="grid gap-5 sm:grid-cols-2">
        <Campo
          nome="telefone"
          rotulo="Telefone"
          defaultValue={cliente?.telefone ?? ""}
          maxLength={20}
        />
        <Campo
          nome="email"
          rotulo="E-mail"
          tipo="email"
          defaultValue={cliente?.email ?? ""}
          maxLength={255}
        />
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <Campo
          nome="cpf"
          rotulo="CPF"
          defaultValue={cliente?.cpf ?? ""}
          maxLength={14}
          dica="Só necessário se o cliente pedir CPF na nota."
        />
        <Campo
          nome="data_nascimento"
          rotulo="Data de nascimento"
          tipo="date"
          defaultValue={cliente?.data_nascimento ?? ""}
        />
      </div>

      <Campo
        nome="endereco"
        rotulo="Endereço"
        defaultValue={cliente?.endereco ?? ""}
        maxLength={500}
      />

      <fieldset className="flex flex-col gap-3 border-t border-[#dbe1e4] pt-5">
        <legend className="sr-only">Preferências</legend>
        <Marcador
          nome="consentimento_marketing"
          rotulo="Aceita receber contato de marketing"
          dica="Promoções e novidades, por e-mail ou telefone."
          defaultChecked={cliente?.consentimento_marketing ?? false}
        />
      </fieldset>

      <div className="flex flex-wrap gap-3">
        {aoSalvar ? (
          <>
            <BotaoEnviar
              carregando="Salvando..."
              onClick={() => {
                sairAoSalvarRef.current = true;
              }}
            >
              Salvar e sair
            </BotaoEnviar>
            <BotaoEnviar
              carregando="Salvando..."
              variante="secundario"
              onClick={() => {
                sairAoSalvarRef.current = false;
              }}
            >
              {textoBotao}
            </BotaoEnviar>
          </>
        ) : (
          <BotaoEnviar carregando="Salvando...">{textoBotao}</BotaoEnviar>
        )}
      </div>
    </form>
  );
}
