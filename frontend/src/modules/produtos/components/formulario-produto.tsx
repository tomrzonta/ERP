"use client";

import { useActionState, useEffect, useRef, useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import { Marcador } from "@/components/ui/marcador";
import { Selecao } from "@/components/ui/selecao";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Categoria, Produto, TipoProduto, Unidade } from "../types";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

const ROTULOS_TIPO: Record<TipoProduto, string> = {
  simples: "Simples",
  kit: "Kit (montagem dá baixa nos componentes e credita o saldo dele)",
};

export function FormularioProduto({
  acao,
  unidades,
  categorias,
  produto,
  podeVerCusto,
  textoBotao,
  tipoInicial = "simples",
  vendavelInicial = true,
  insumoInicial = false,
  aoSalvar,
}: {
  acao: Acao;
  unidades: Unidade[];
  categorias: Categoria[];
  produto?: Produto;
  podeVerCusto: boolean;
  textoBotao: string;
  /** Só valem na criação (produto ainda não existe); vindos da tela de origem. */
  tipoInicial?: TipoProduto;
  vendavelInicial?: boolean;
  insumoInicial?: boolean;
  /** Só faz sentido editando dentro de um modal: chamado a cada salvamento
   * bem-sucedido, com `true` se o botão clicado foi "Salvar e sair". */
  aoSalvar?: (sair: boolean) => void;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(acao, undefined);
  const salvo = estado?.erro === "";
  const [tipo, setTipo] = useState<TipoProduto>(produto?.tipo ?? tipoInicial);

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

      {produto ? (
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-[#16222b]">Tipo</span>
          <p className="text-sm text-[#5b6b75]">
            {ROTULOS_TIPO[produto.tipo]} — não pode ser alterado depois de criado.
          </p>
        </div>
      ) : (
        <Selecao
          nome="tipo"
          rotulo="Tipo"
          value={tipo}
          onChange={(evento) => setTipo(evento.target.value as TipoProduto)}
          opcoes={(Object.keys(ROTULOS_TIPO) as TipoProduto[]).map((valor) => ({
            valor,
            texto: ROTULOS_TIPO[valor],
          }))}
        />
      )}

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
        <CampoNumero
          nome="preco_venda"
          formato="dinheiro"
          rotulo="Preço de venda"
          valorInicial={produto?.preco_venda ?? "0"}
        />
        {!produto ? (
          <CampoNumero
            nome="custo"
            formato="custo"
            rotulo="Custo por unidade"
            valorInicial="0"
            dica={
              podeVerCusto
                ? "Custo inicial. Compras (ou montagens) vão atualizar o custo médio."
                : undefined
            }
          />
        ) : null}
        {produto && podeVerCusto ? (
          <CampoNumero
            nome="custo_medio"
            formato="custo"
            rotulo="Custo por unidade (atual)"
            valorInicial={produto.custo_medio ?? "0"}
            dica="Corrige o custo agora (ex.: fornecedor reajustou o preço). Não muda montagens já feitas — só vale para as próximas entradas/montagens que usarem este item."
          />
        ) : null}
      </div>

      <CampoNumero
        nome="estoque_minimo"
        formato="quantidade"
        unidade={produto?.unidade_codigo}
        rotulo="Estoque mínimo"
        valorInicial={produto?.estoque_minimo ?? "0"}
        dica="Quando o disponível chegar nesse valor, o Painel avisa (plano Pro). Deixe zerado para não avisar."
      />

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
          defaultChecked={produto ? produto.vendavel : vendavelInicial}
        />
        <Marcador
          nome="insumo"
          rotulo="Usado como insumo"
          dica="Entra na composição de outros produtos, como filamento ou terra."
          defaultChecked={produto ? produto.insumo : insumoInicial}
        />
        {tipo === "simples" ? (
          <Marcador
            nome="controla_estoque"
            rotulo="Controla estoque"
            dica="Desmarque para serviços e mão de obra."
            defaultChecked={produto ? produto.controla_estoque : true}
          />
        ) : (
          <p className="text-xs text-[#5b6b75]">
            Kit sempre controla estoque próprio: a montagem credita o saldo dele.
          </p>
        )}
        {produto ? (
          <Marcador
            nome="publicado_na_vitrine"
            rotulo="Publicar na vitrine"
            defaultChecked={produto.publicado_na_vitrine}
          />
        ) : null}
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
