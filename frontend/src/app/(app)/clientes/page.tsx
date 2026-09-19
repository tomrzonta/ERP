import Link from "next/link";

import { carregarDaSessao } from "@/lib/server/sessao";
import { obterEu } from "@/modules/auth/eu";
import { TabelaClientes } from "@/modules/clientes/components/tabela-clientes";
import type { Cliente } from "@/modules/clientes/types";

export const metadata = { title: "Clientes · ERP" };

export default async function ClientesPage({
  searchParams,
}: {
  searchParams: Promise<{ termo?: string }>;
}) {
  const { termo } = await searchParams;
  const eu = await obterEu();
  const parametros = new URLSearchParams();
  if (termo) parametros.set("termo", termo);
  const clientes = await carregarDaSessao<Cliente[]>(`/clientes?${parametros}`);

  const podeEditar = eu.permissoes.includes("clientes.editar");

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Clientes</h1>
        {podeEditar ? (
          <Link
            href="/clientes/novo"
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            Novo cliente
          </Link>
        ) : null}
      </div>

      <form action="/clientes" className="mt-6 flex gap-3">
        <input
          name="termo"
          defaultValue={termo ?? ""}
          placeholder="Buscar por nome, telefone ou e-mail"
          aria-label="Buscar clientes"
          className="w-full max-w-sm rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-[#16222b] outline-none focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
        />
        <button
          type="submit"
          className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
        >
          Buscar
        </button>
      </form>

      <TabelaClientes
        clientes={clientes}
        podeEditar={podeEditar}
        mensagemVazia={
          termo
            ? "Nenhum cliente encontrado para essa busca."
            : "Você ainda não cadastrou clientes."
        }
      />
    </div>
  );
}
