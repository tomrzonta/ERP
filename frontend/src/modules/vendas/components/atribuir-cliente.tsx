"use client";

import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { SeletorBusca } from "@/components/ui/seletor-busca";
import type { Cliente } from "@/modules/clientes/types";
import { atualizarClienteDaVenda } from "../actions";
import type { Venda } from "../types";

export function AtribuirCliente({
  venda,
  clientes,
  aoAtualizar,
}: {
  venda: Venda;
  clientes: Cliente[];
  aoAtualizar: (venda: Venda) => void;
}) {
  const [editando, setEditando] = useState(false);
  const [novoCliente, setNovoCliente] = useState(false);
  const [nome, setNome] = useState("");
  const [telefone, setTelefone] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  const clienteAtual = clientes.find((c) => c.id === venda.cliente_id) ?? null;

  async function escolher(cliente: Cliente) {
    setEnviando(true);
    const resultado = await atualizarClienteDaVenda(venda.id, { cliente_id: cliente.id });
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoAtualizar(resultado.venda);
    setEditando(false);
  }

  async function criarECliente() {
    if (!nome.trim()) {
      setErro("Informe o nome do cliente.");
      return;
    }
    setErro("");
    setEnviando(true);
    const resultado = await atualizarClienteDaVenda(venda.id, {
      cliente_novo: { nome, telefone: telefone || undefined },
    });
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoAtualizar(resultado.venda);
    setEditando(false);
    setNovoCliente(false);
    setNome("");
    setTelefone("");
  }

  async function remover() {
    setEnviando(true);
    const resultado = await atualizarClienteDaVenda(venda.id, { cliente_id: null });
    setEnviando(false);
    if (resultado.ok) aoAtualizar(resultado.venda);
  }

  if (!editando) {
    return (
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-[#5b6b75]">Cliente:</span>
        <span className="font-medium text-[#16222b]">
          {clienteAtual ? clienteAtual.nome : "Balcão (sem cliente)"}
        </span>
        {venda.status === "aberto" ? (
          <button
            type="button"
            onClick={() => setEditando(true)}
            className="text-[#0f6d5c] hover:underline"
          >
            {clienteAtual ? "trocar" : "atribuir"}
          </button>
        ) : null}
        {venda.status === "aberto" && clienteAtual ? (
          <button type="button" onClick={remover} className="text-[#a8341f] hover:underline">
            remover
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-md border border-[#dbe1e4] bg-white p-4">
      {!novoCliente ? (
        <>
          <SeletorBusca
            itens={clientes}
            chave={(c) => c.id}
            correspondeAoTermo={(c, termo) =>
              c.nome.toLowerCase().includes(termo) || (c.telefone ?? "").includes(termo)
            }
            aoEscolher={escolher}
            placeholder="Buscar cliente por nome ou telefone..."
            renderItem={(c) => (
              <>
                <span>{c.nome}</span>
                <span className="text-sm text-[#5b6b75]">{c.telefone ?? ""}</span>
              </>
            )}
          />
          <div className="flex justify-between text-sm">
            <button
              type="button"
              onClick={() => setNovoCliente(true)}
              className="text-[#0f6d5c] hover:underline"
            >
              Cadastrar cliente novo
            </button>
            <button
              type="button"
              onClick={() => setEditando(false)}
              className="text-[#5b6b75] hover:text-[#16222b]"
            >
              Cancelar
            </button>
          </div>
        </>
      ) : (
        <>
          <input
            value={nome}
            onChange={(evento) => setNome(evento.target.value)}
            placeholder="Nome"
            className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          />
          <input
            value={telefone}
            onChange={(evento) => setTelefone(evento.target.value)}
            placeholder="Telefone (opcional)"
            className="rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
          />
          <div className="flex justify-between text-sm">
            <button
              type="button"
              disabled={enviando}
              onClick={criarECliente}
              className="text-[#0f6d5c] hover:underline disabled:opacity-60"
            >
              {enviando ? "Salvando..." : "Salvar cliente"}
            </button>
            <button
              type="button"
              onClick={() => setNovoCliente(false)}
              className="text-[#5b6b75] hover:text-[#16222b]"
            >
              Buscar existente
            </button>
          </div>
        </>
      )}
      {erro ? <Aviso>{erro}</Aviso> : null}
    </div>
  );
}
