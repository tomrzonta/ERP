"use client";

import Link from "next/link";
import { useActionState, useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { BotaoEnviar } from "@/components/ui/botao";
import { Campo } from "@/components/ui/campo";
import { CampoNumero } from "@/components/ui/campo-numero";
import { Modal } from "@/components/ui/modal";
import { numero } from "@/lib/formato";
import type { EstadoFormulario } from "@/modules/auth/types";
import { registrarAjuste, registrarEntrada } from "../actions";

type Modo = "entrada" | "contagem";

/** Botão "Estoque" autocontido: abre um modal pra dar entrada (somar) ou
 * contar (definir o total) sem sair da lista. Usado em Produtos, Insumos e
 * na tela de Estoque. Compra em unidade alternativa (rolo, caixa) fica na
 * página do produto, pelo link no rodapé do modal. */
export function BotaoEstoque({
  produtoId,
  nome,
  unidadeCodigo,
  fisico,
  casas,
  custoMedio,
  podeMovimentar,
  podeAjustar,
}: {
  produtoId: string;
  nome: string;
  unidadeCodigo: string;
  /** Saldo físico atual, se a tela já o tem (a lista de produtos não tem). */
  fisico?: string;
  casas: number;
  custoMedio: string | null;
  podeMovimentar: boolean;
  podeAjustar: boolean;
}) {
  const [aberto, setAberto] = useState(false);
  const [modo, setModo] = useState<Modo>(podeMovimentar ? "entrada" : "contagem");

  if (!podeMovimentar && !podeAjustar) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="rounded-md border border-[#dbe1e4] bg-white px-3 py-1.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
      >
        Estoque
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo={`Estoque de ${nome}`}>
        {fisico !== undefined ? (
          <p className="mt-2 text-sm text-[#5b6b75]">
            Saldo atual: {numero(fisico, casas)} {unidadeCodigo}
          </p>
        ) : null}

        {podeMovimentar && podeAjustar ? (
          <div className="mt-4 flex gap-2">
            {(
              [
                ["entrada", "Dar entrada (somar)"],
                ["contagem", "Contar (definir total)"],
              ] as const
            ).map(([valor, texto]) => (
              <button
                key={valor}
                type="button"
                onClick={() => setModo(valor)}
                className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
                  modo === valor
                    ? "border-[#0f6d5c] bg-[#0f6d5c] text-white"
                    : "border-[#dbe1e4] bg-white text-[#16222b] hover:border-[#0f6d5c]"
                }`}
              >
                {texto}
              </button>
            ))}
          </div>
        ) : null}

        <div className="mt-5">
          {modo === "entrada" ? (
            <FormularioEntradaRapida
              produtoId={produtoId}
              unidadeCodigo={unidadeCodigo}
              custoMedio={custoMedio}
              aoConcluir={() => setAberto(false)}
            />
          ) : (
            <FormularioContagemRapida
              produtoId={produtoId}
              unidadeCodigo={unidadeCodigo}
              aoConcluir={() => setAberto(false)}
            />
          )}
        </div>

        <p className="mt-5 text-sm text-[#5b6b75]">
          Comprou em outra unidade (rolo, caixa) ou quer ver o histórico?{" "}
          <Link href={`/produtos/${produtoId}/estoque`} className="text-[#0f6d5c] hover:underline">
            Abrir estoque do produto
          </Link>
        </p>
      </Modal>
    </>
  );
}

function FormularioEntradaRapida({
  produtoId,
  unidadeCodigo,
  custoMedio,
  aoConcluir,
}: {
  produtoId: string;
  unidadeCodigo: string;
  custoMedio: string | null;
  aoConcluir: () => void;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(async (anterior, dados) => {
    const resultado = await registrarEntrada(produtoId, anterior, dados);
    if (resultado && !resultado.erro) aoConcluir();
    return resultado;
  }, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <CampoNumero
        nome="quantidade"
        formato="quantidade"
        unidade={unidadeCodigo}
        positivo
        rotulo={`Quantidade a somar (${unidadeCodigo})`}
        required
        autoFocus
      />
      <CampoNumero
        nome="custo_unitario"
        formato="custo"
        rotulo={`Custo por ${unidadeCodigo}`}
        required
        valorInicial={custoMedio ?? "0"}
        dica="Já vem com o custo médio atual. Ajuste se pagou outro valor; a média é recalculada."
      />
      <Campo nome="origem" rotulo="Origem" placeholder="Compra, fornecedor..." maxLength={60} />
      <div>
        <BotaoEnviar carregando="Registrando...">Registrar entrada</BotaoEnviar>
      </div>
    </form>
  );
}

function FormularioContagemRapida({
  produtoId,
  unidadeCodigo,
  aoConcluir,
}: {
  produtoId: string;
  unidadeCodigo: string;
  aoConcluir: () => void;
}) {
  const [estado, enviar] = useActionState<EstadoFormulario, FormData>(async (anterior, dados) => {
    const resultado = await registrarAjuste(produtoId, anterior, dados);
    if (resultado && !resultado.erro) aoConcluir();
    return resultado;
  }, undefined);

  return (
    <form action={enviar} className="flex flex-col gap-4">
      {estado?.erro ? <Aviso>{estado.erro}</Aviso> : null}
      <CampoNumero
        nome="quantidade_contada"
        formato="quantidade"
        unidade={unidadeCodigo}
        rotulo={`Quantidade contada (${unidadeCodigo})`}
        required
        autoFocus
        dica="O saldo passa a ser exatamente este número. A diferença fica registrada como ajuste."
      />
      <Campo nome="origem" rotulo="Motivo" placeholder="Contagem inicial, inventário..." maxLength={60} />
      <div>
        <BotaoEnviar carregando="Registrando...">Definir quantidade</BotaoEnviar>
      </div>
    </form>
  );
}
