"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { SeletorBusca } from "@/components/ui/seletor-busca";
import { mesclarClientes } from "../actions";
import type { Cliente } from "../types";

export function MesclarCliente({ cliente, clientes }: { cliente: Cliente; clientes: Cliente[] }) {
  const router = useRouter();
  const [aberto, setAberto] = useState(false);
  const [duplicado, setDuplicado] = useState<Cliente | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  const candidatos = clientes.filter((c) => c.id !== cliente.id);

  async function confirmar() {
    if (!duplicado) return;
    setEnviando(true);
    setErro("");
    const resultado = await mesclarClientes(cliente.id, duplicado.id);
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    router.refresh();
    setAberto(false);
    setDuplicado(null);
  }

  if (!aberto) {
    return (
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="text-sm text-[#0f6d5c] hover:underline"
      >
        Mesclar cadastro duplicado
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-md border border-[#dbe1e4] bg-white p-4">
      <p className="text-sm text-[#5b6b75]">
        Busque o cadastro duplicado. Os dados que <strong>{cliente.nome}</strong> não tem são
        herdados dele, as vendas dele passam a valer pra {cliente.nome}, e ele some da listagem.
      </p>
      {!duplicado ? (
        <SeletorBusca
          itens={candidatos}
          chave={(c) => c.id}
          correspondeAoTermo={(c, termo) =>
            c.nome.toLowerCase().includes(termo) || (c.telefone ?? "").includes(termo)
          }
          aoEscolher={setDuplicado}
          placeholder="Buscar cliente duplicado por nome ou telefone..."
          renderItem={(c) => (
            <>
              <span>{c.nome}</span>
              <span className="text-sm text-[#5b6b75]">{c.telefone ?? ""}</span>
            </>
          )}
        />
      ) : (
        <div className="flex items-center gap-3 rounded-md border border-[#a86b0f]/25 bg-[#fdf3e0] px-3 py-2 text-sm">
          <span>
            Mesclar <strong>{duplicado.nome}</strong> em <strong>{cliente.nome}</strong>?
          </span>
          <button
            type="button"
            disabled={enviando}
            onClick={confirmar}
            className="font-medium text-[#a86b0f] hover:underline disabled:opacity-60"
          >
            {enviando ? "Mesclando..." : "Confirmar"}
          </button>
          <button
            type="button"
            onClick={() => setDuplicado(null)}
            className="text-[#5b6b75] hover:text-[#16222b]"
          >
            Voltar
          </button>
        </div>
      )}
      {erro ? <Aviso>{erro}</Aviso> : null}
      <button
        type="button"
        onClick={() => {
          setAberto(false);
          setDuplicado(null);
          setErro("");
        }}
        className="self-start text-sm text-[#5b6b75] hover:text-[#16222b]"
      >
        Cancelar
      </button>
    </div>
  );
}
