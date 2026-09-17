import Link from "next/link";

import { BotaoSair } from "@/modules/auth/components/botao-sair";
import type { Eu } from "@/modules/auth/types";

const LINKS = [
  { href: "/", texto: "Início" },
  { href: "/produtos", texto: "Produtos" },
];

export function Cabecalho({ eu }: { eu: Eu }) {
  return (
    <header className="border-b border-[#dbe1e4] bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div>
          <p className="font-semibold tracking-tight text-[#16222b]">{eu.empresa.nome}</p>
          <p className="text-sm text-[#5b6b75]">
            {eu.usuario.nome} · {eu.papel}
          </p>
        </div>

        <nav className="flex items-center gap-5 text-sm">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-[#16222b] transition-colors hover:text-[#0f6d5c]"
            >
              {link.texto}
            </Link>
          ))}
          <Link
            href="/escolher-empresa"
            className="text-[#5b6b75] transition-colors hover:text-[#16222b]"
          >
            Trocar negócio
          </Link>
          <BotaoSair />
        </nav>
      </div>
    </header>
  );
}
