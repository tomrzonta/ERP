"use client";

import { useState } from "react";

import { Modal } from "@/components/ui/modal";
import { ToastDesfazer } from "@/components/ui/toast-desfazer";
import { atualizarCliente } from "../actions";
import { clienteParaFormData } from "../formato-cliente";
import type { Cliente } from "../types";
import { FormularioCliente } from "./formulario-cliente";

/** Botão "Editar" autocontido: abre o formulário de edição em modal, de
 * dentro de qualquer linha da lista de clientes. */
export function BotaoEditarCliente({ cliente }: { cliente: Cliente }) {
  const [aberto, setAberto] = useState(false);
  const [antesDeEditar, setAntesDeEditar] = useState<Cliente | null>(null);
  const [mostrarDesfazer, setMostrarDesfazer] = useState(false);

  function abrir() {
    setAntesDeEditar(cliente);
    setAberto(true);
  }

  function aoSalvar(sair: boolean) {
    if (sair) setAberto(false);
    setMostrarDesfazer(true);
  }

  async function desfazer() {
    if (!antesDeEditar) return;
    await atualizarCliente(antesDeEditar.id, undefined, clienteParaFormData(antesDeEditar));
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
      <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo={`Editar ${cliente.nome}`}>
        <FormularioCliente
          acao={atualizarCliente.bind(null, cliente.id)}
          cliente={cliente}
          textoBotao="Salvar e continuar editando"
          aoSalvar={aoSalvar}
        />
      </Modal>
      {mostrarDesfazer ? (
        <ToastDesfazer
          mensagem={`Alterações salvas em ${cliente.nome}.`}
          aoDesfazer={desfazer}
          aoEncerrar={() => setMostrarDesfazer(false)}
        />
      ) : null}
    </>
  );
}
