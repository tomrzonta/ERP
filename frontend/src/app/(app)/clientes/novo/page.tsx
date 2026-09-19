import Link from "next/link";
import { redirect } from "next/navigation";

import { obterEu } from "@/modules/auth/eu";
import { criarCliente } from "@/modules/clientes/actions";
import { FormularioCliente } from "@/modules/clientes/components/formulario-cliente";

export const metadata = { title: "Novo cliente · ERP" };

export default async function NovoClientePage() {
  const eu = await obterEu();
  if (!eu.permissoes.includes("clientes.editar")) {
    redirect("/clientes");
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <Link href="/clientes" className="text-sm text-[#5b6b75] hover:text-[#16222b]">
        Voltar para clientes
      </Link>
      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-[#16222b]">Novo cliente</h1>

      <div className="mt-8">
        <FormularioCliente acao={criarCliente} textoBotao="Criar cliente" />
      </div>
    </div>
  );
}
