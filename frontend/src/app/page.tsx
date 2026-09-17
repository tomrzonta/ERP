import Link from "next/link";

import { chamarApi } from "@/lib/server/api";
import { carregarDaSessao } from "@/lib/server/sessao";
import { BotaoSair } from "@/modules/auth/components/botao-sair";
import type { Eu } from "@/modules/auth/types";

type Health = { api: string; banco: string; ambiente: string };

export default async function PainelPage() {
  const eu = await carregarDaSessao<Eu>("/auth/eu");
  const health = await chamarApi<Health>("/health").catch(() => null);

  return (
    <main className="min-h-screen bg-[#f7f8f8]">
      <header className="border-b border-[#dbe1e4] bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="font-semibold tracking-tight text-[#16222b]">{eu.empresa.nome}</p>
            <p className="text-sm text-[#5b6b75]">
              {eu.usuario.nome} · {eu.papel}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/escolher-empresa"
              className="text-sm text-[#5b6b75] underline decoration-[#dbe1e4] underline-offset-4 transition-colors hover:text-[#16222b]"
            >
              Trocar negócio
            </Link>
            <BotaoSair />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
          Tudo pronto para começar
        </h1>
        <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
          Sua conta está no plano {eu.plano === "pro" ? "Pro" : "Base"}. O cadastro de produtos é
          o próximo passo do sistema.
        </p>

        <dl className="mt-10 grid gap-px overflow-hidden rounded-lg border border-[#dbe1e4] bg-[#dbe1e4] sm:grid-cols-3">
          {[
            ["Plano", eu.plano === "pro" ? "Pro" : "Base"],
            ["Permissões", String(eu.permissoes.length)],
            ["Ambiente", health?.ambiente ?? "sem resposta"],
          ].map(([rotulo, valor]) => (
            <div key={rotulo} className="bg-white px-4 py-5">
              <dt className="text-sm text-[#5b6b75]">{rotulo}</dt>
              <dd className="mt-1 text-lg font-medium text-[#16222b]">{valor}</dd>
            </div>
          ))}
        </dl>
      </div>
    </main>
  );
}
