import Link from "next/link";

import { BotaoEditarCliente } from "./botao-editar-cliente";
import type { Cliente } from "../types";

export function TabelaClientes({
  clientes,
  podeEditar,
  mensagemVazia,
}: {
  clientes: Cliente[];
  podeEditar: boolean;
  mensagemVazia: string;
}) {
  if (clientes.length === 0) {
    return <p className="mt-10 text-sm text-[#5b6b75]">{mensagemVazia}</p>;
  }

  return (
    <div className="mt-8 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
      <table className="w-full text-sm">
        <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
          <tr>
            <th className="px-4 py-3 font-medium">Nome</th>
            <th className="px-4 py-3 font-medium">Telefone</th>
            <th className="px-4 py-3 font-medium">E-mail</th>
            {podeEditar ? <th className="px-4 py-3" /> : null}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#dbe1e4]">
          {clientes.map((cliente) => (
            <tr key={cliente.id} className="transition-colors hover:bg-[#f7f8f8]">
              <td className="px-4 py-3">
                <Link
                  href={`/clientes/${cliente.id}`}
                  className="font-medium text-[#16222b] hover:text-[#0f6d5c]"
                >
                  {cliente.nome}
                </Link>
              </td>
              <td className="px-4 py-3 tabular-nums text-[#5b6b75]">{cliente.telefone ?? "—"}</td>
              <td className="px-4 py-3 text-[#5b6b75]">{cliente.email ?? "—"}</td>
              {podeEditar ? (
                <td className="px-4 py-3 text-right">
                  <BotaoEditarCliente cliente={cliente} />
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
