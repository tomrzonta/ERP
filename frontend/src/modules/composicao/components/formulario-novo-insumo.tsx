"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import { Selecao } from "@/components/ui/selecao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Unidade } from "@/modules/produtos/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

/** Cadastra um insumo novo e já vincula como componente, numa ação só. */
export function FormularioNovoInsumo({ acao, unidades }: { acao: Acao; unidades: Unidade[] }) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <Campo
        nome="nome"
        rotulo="Nome do insumo"
        required
        maxLength={120}
        placeholder="Ex.: Filamento PLA"
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <Selecao
          nome="unidade_codigo"
          rotulo="Unidade de estoque"
          defaultValue="un"
          opcoes={unidades.map((unidade) => ({
            valor: unidade.codigo,
            texto: `${unidade.nome} (${unidade.codigo})`,
          }))}
        />
        <CampoNumero
          nome="custo"
          formato="custo"
          rotulo="Custo inicial"
          valorInicial="0"
        />
      </div>
      <CampoNumero
        nome="quantidade"
        formato="quantidade"
        positivo
        rotulo="Quantidade usada neste kit"
        required
        dica="Na mesma unidade de estoque do insumo, definida acima."
      />
      <div>
        <BotaoEnviar carregando="Criando...">Criar e adicionar</BotaoEnviar>
      </div>
    </form>
  );
}
