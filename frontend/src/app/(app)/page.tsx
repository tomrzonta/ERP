import Link from "next/link";

import { chamarApi } from "@/lib/server/api";
import { obterEu } from "@/modules/auth/eu";

type Health = { api: string; banco: string; ambiente: string };

export default async function PainelPage() {
  const eu = await obterEu();
  const health = await chamarApi<Health>("/health").catch(() => null);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">
        Tudo pronto para começar
      </h1>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Cadastre seus produtos e insumos. O controle de estoque é o próximo passo do sistema.
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
    </div>
  );
}
