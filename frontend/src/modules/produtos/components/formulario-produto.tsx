"use client";

import { useActionState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { Marcador } from "@/components/ui/marcador";
import { Selecao } from "@/components/ui/selecao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Categoria, Produto, Unidade } from "../types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function FormularioProduto({
  acao,
  unidades,
  categorias,
  produto,
  podeVerCusto,
  textoBotao,
}: {
  acao: Acao;
  unidades: Unidade[];
  categorias: Categoria[];
  produto?: Produto;
  podeVerCusto: boolean;
  textoBotao: string;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);
  const salvo = estado?.erro === "";

  return (
    <form action={enviar} className="flex max-w-xl flex-col gap-5">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      {salvo ? (
        <p className="rounded-md border border-[#0f6d5c]/25 bg-[#0f6d5c]/5 px-3 py-2 text-sm text-[#0f6d5c]">
          Alterações salvas.
        </p>
      ) : null}

      <Campo nome="nome" rotulo="Nome" required defaultValue={produto?.nome} maxLength={120} />

      <div className="grid gap-5 sm:grid-cols-2">
        <Campo
          nome="sku"
          rotulo="SKU"
          defaultValue={produto?.sku}
          dica={produto ? undefined : "Deixe vazio para gerar automaticamente."}
          maxLength={40}
        />
        <Selecao
          nome="unidade_codigo"
          rotulo="Unidade de estoque"
          defaultValue={produto?.unidade_codigo ?? "un"}
          opcoes={unidades.map((unidade) => ({
            valor: unidade.codigo,
            texto: `${unidade.nome} (${unidade.codigo})`,
          }))}
        />
      </div>

      <Selecao
        nome="categoria_id"
        rotulo="Categoria"
        vazio="Sem categoria"
        defaultValue={produto?.categoria_id ?? ""}
        opcoes={categorias.map((categoria) => ({
          valor: categoria.id,
          texto: categoria.nome,
        }))}
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <Campo
          nome="preco_venda"
          rotulo="Preço de venda"
          tipo="number"
          step="0.01"
          min="0"
          defaultValue={produto?.preco_venda ?? "0"}
        />
        {produto ? null : (
          <Campo
            nome="custo"
            rotulo="Custo por unidade"
            tipo="number"
            step="0.000001"
            min="0"
            defaultValue="0"
            dica={
              podeVerCusto
                ? "Custo inicial. As compras vão atualizar o custo médio."
                : undefined
            }
          />
        )}
      </div>

      <Campo
        nome="codigo_barras"
        rotulo="Código de barras"
        defaultValue={produto?.codigo_barras ?? ""}
        maxLength={20}
        dica="O EAN da embalagem, usado pelo leitor no caixa."
      />

      <Campo
        nome="descricao"
        rotulo="Descrição"
        defaultValue={produto?.descricao ?? ""}
        maxLength={500}
      />

      <fieldset className="flex flex-col gap-3 border-t border-[#dbe1e4] pt-5">
        <legend className="sr-only">Como o produto é usado</legend>
        <Marcador
          nome="vendavel"
          rotulo="Vendável"
          dica="Aparece no caixa e na vitrine."
          defaultChecked={produto ? produto.vendavel : true}
        />
        <Marcador
          nome="insumo"
          rotulo="Usado como insumo"
          dica="Entra na composição de outros produtos, como filamento ou terra."
          defaultChecked={produto?.insumo ?? false}
        />
        <Marcador
          nome="controla_estoque"
          rotulo="Controla estoque"
          dica="Desmarque para serviços e mão de obra."
          defaultChecked={produto ? produto.controla_estoque : true}
        />
        {produto ? (
          <Marcador
            nome="publicado_na_vitrine"
            rotulo="Publicar na vitrine"
            defaultChecked={produto.publicado_na_vitrine}
          />
        ) : null}
      </fieldset>

      <div>
        <BotaoEnviar carregando="Salvando...">{textoBotao}</BotaoEnviar>
      </div>
    </form>
  );
}
