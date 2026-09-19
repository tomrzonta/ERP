"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import { Selecao } from "@/components/ui/selecao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { UnidadeAlternativa } from "@/modules/produtos/types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioEntrada({
  acao,
  unidadeBase,
  unidadesAlternativas,
}: {
  acao: Acao;
  unidadeBase: string;
  unidadesAlternativas: UnidadeAlternativa[];
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);
  const paraCompra = unidadesAlternativas.filter((unidade) => unidade.usa_na_compra);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <CampoNumero
          nome="quantidade"
          formato="quantidade"
          unidade={unidadeBase}
          positivo
          rotulo="Quantidade"
          required
        />
        {paraCompra.length > 0 ? (
          <Selecao
            nome="unidade_id"
            rotulo="Unidade da compra"
            vazio={`${unidadeBase} (unidade de estoque)`}
            opcoes={paraCompra.map((unidade) => ({ valor: unidade.id, texto: unidade.nome }))}
          />
        ) : null}
      </div>

      <CampoNumero
        nome="custo_unitario"
        formato="custo"
        rotulo="Custo por unidade da compra"
        required
        dica={
          paraCompra.length > 0
            ? "Se comprar em outra unidade (ex. rolo), informe o custo do rolo, não da unidade de estoque."
            : "O custo médio é recalculado automaticamente a partir daqui."
        }
      />

      <Campo nome="origem" rotulo="Origem" placeholder="Compra, fornecedor..." maxLength={60} />

      <div>
        <BotaoEnviar carregando="Registrando...">Registrar entrada</BotaoEnviar>
      </div>
    </form>
  );
}
