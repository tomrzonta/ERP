"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { BuscaSelecao } from "@/components/ui/busca-selecao";
import { CampoNumero } from "@/components/ui/campo-numero";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Produto } from "@/modules/produtos/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioComponente({
  acao,
  candidatos,
}: {
  acao: Acao;
  candidatos: Produto[];
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);

  if (candidatos.length === 0) {
    return (
      <p className="text-sm text-[#5b6b75]">
        Não há produtos disponíveis para virar componente. Cadastre um produto simples primeiro.
      </p>
    );
  }

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <BuscaSelecao
            nome="componente_id"
            rotulo="Componente"
            placeholder="Digite pra buscar por nome ou SKU"
            opcoes={candidatos.map((produto) => ({
              valor: produto.id,
              texto: `${produto.nome} (${produto.sku})`,
            }))}
          />
        </div>
        <CampoNumero
          nome="quantidade"
          formato="quantidade"
          positivo
          rotulo="Quantidade"
          required
        />
      </div>

      <details className="group">
        <summary className="cursor-pointer text-sm text-[#0f6d5c] select-none">
          Mais opções
        </summary>
        <div className="mt-3 max-w-xs">
          <CampoNumero
            nome="perda_percentual"
            formato="percentual"
            maximo={99.99}
            rotulo="Perda percentual"
            valorInicial="0"
            dica="Some ao que é consumido em cada montagem, além da quantidade cadastrada."
          />
        </div>
      </details>

      <div>
        <BotaoEnviar carregando="Adicionando...">Adicionar componente</BotaoEnviar>
      </div>
    </form>
  );
}
