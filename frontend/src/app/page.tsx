import Link from "next/link";

import { Cabecalho } from "@/components/cabecalho";
import { chamarApi } from "@/lib/server/api";
import { carregarDaSessao } from "@/lib/server/sessao";
import type { Eu } from "@/modules/auth/types";

type Health = { api: string; banco: string; ambiente: string };

export default async function PainelPage() {
  const eu = await carregarDaSessao<Eu>("/auth/eu");
  const health = await chamarApi<Health>("/health").catch(() => null);

  return (
    <>
      <Cabecalho eu={eu} />
      <main className="mx-auto max-w-5xl px-6 py-12">
        <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
          Tudo pronto para começar
        </h1>
        <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
          Sua conta está no plano {eu.plano === "pro" ? "Pro" : "Base"}. Cadastre seus produtos e
          insumos; o controle de estoque é o próximo passo do sistema.
        </p>

        <div className="mt-8">
          <Link
            href="/produtos"
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
          >
            Ir para produtos
          </Link>
        </div>

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
      </main>
    </>
  );
}
