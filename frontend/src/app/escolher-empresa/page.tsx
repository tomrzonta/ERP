import { carregarDaSessao } from "@/lib/server/sessao";
import { escolherEmpresa } from "@/modules/auth/actions";
import { BotaoSair } from "@/modules/auth/components/botao-sair";
import type { EmpresaDisponivel } from "@/modules/auth/types";

export const metadata = { title: "Escolher negócio · ERP" };

export default async function EscolherEmpresaPage() {
  const empresas = await carregarDaSessao<EmpresaDisponivel[]>("/auth/empresas");

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f7f8f8] px-6 py-12">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
          Em qual negócio você vai trabalhar?
        </h1>
        <p className="mt-2 text-sm text-[#5b6b75]">
          Você pode trocar depois, sem sair da conta.
        </p>

        <ul className="mt-8 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
          {empresas.map((empresa) => (
            <li key={empresa.id}>
              <form action={escolherEmpresa}>
                <input type="hidden" name="empresa_id" value={empresa.id} />
                <button
                  type="submit"
                  className="flex w-full items-center justify-between gap-4 px-4 py-4 text-left transition-colors hover:bg-[#f7f8f8] focus-visible:bg-[#f7f8f8] focus-visible:outline-none"
                >
                  <span className="font-medium text-[#16222b]">{empresa.nome}</span>
                  <span className="text-sm text-[#5b6b75]">{empresa.papel}</span>
                </button>
              </form>
            </li>
          ))}
        </ul>

        {empresas.length === 0 ? (
          <p className="mt-6 text-sm text-[#5b6b75]">
            Sua conta não está ligada a nenhum negócio ativo. Peça um convite a quem administra.
          </p>
        ) : null}

        <div className="mt-6">
          <BotaoSair />
        </div>
      </div>
    </main>
  );
}
