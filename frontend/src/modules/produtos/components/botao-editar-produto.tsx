"use client";

import { useState } from "react";

import { Modal } from "@/components/ui/modal";
import { ToastDesfazer } from "@/components/ui/toast-desfazer";
import { atualizarProduto } from "../actions";
import { produtoParaFormData } from "../formato-produto";
import type { Categoria, Produto, Unidade } from "../types";
import { FormularioProduto } from "./formulario-produto";

/** Botão "Editar" autocontido: abre o mesmo formulário de edição em modal,
 * de dentro de qualquer linha de tabela (Produtos, Insumos, Kits, Estoque). */
export function BotaoEditarProduto({
  produto,
  unidades,
  categorias,
  podeVerCusto,
}: {
  produto: Produto;
  unidades: Unidade[];
  categorias: Categoria[];
  podeVerCusto: boolean;
}) {
  const [aberto, setAberto] = useState(false);
  const [antesDeEditar, setAntesDeEditar] = useState<Produto | null>(null);
  const [mostrarDesfazer, setMostrarDesfazer] = useState(false);

  function abrir() {
    setAntesDeEditar(produto);
    setAberto(true);
  }

  function aoSalvar(sair: boolean) {
    if (sair) setAberto(false);
    setMostrarDesfazer(true);
  }

  async function desfazer() {
    if (!antesDeEditar) return;
    await atualizarProduto(antesDeEditar.id, undefined, produtoParaFormData(antesDeEditar));
  }

  return (
    <>
      <button
        type="button"
        onClick={abrir}
        className="rounded-md border border-[#dbe1e4] bg-white px-3 py-1.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
      >
        Editar
      </button>
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo={`Editar ${produto.nome}`}>
        <FormularioProduto
          acao={atualizarProduto.bind(null, produto.id)}
          unidades={unidades}
          categorias={categorias}
          produto={produto}
          podeVerCusto={podeVerCusto}
          textoBotao="Salvar e continuar editando"
          aoSalvar={aoSalvar}
        />
      </Modal>
      {mostrarDesfazer ? (
        <ToastDesfazer
          mensagem={`Alterações salvas em ${produto.nome}.`}
          aoDesfazer={desfazer}
          aoEncerrar={() => setMostrarDesfazer(false)}
        />
      ) : null}
    </>
  );
}
