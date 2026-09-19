"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { MENU, type ItemMenu } from "@/components/navegacao/itens";
import { IndicadorConexao } from "@/components/pwa/indicador-conexao";
import { MotorSincronizacao } from "@/components/pwa/motor-sincronizacao";
import { SincronizarSessao } from "@/components/pwa/sincronizar-sessao";
import { sair } from "@/modules/auth/actions";
import type { Eu } from "@/modules/auth/types";

function podeVer(item: ItemMenu, permissoes: string[]): boolean {
  if (item.permissao && !permissoes.includes(item.permissao)) {
    return false;
  }
  if (!item.filhos) {
    return true;
  }
  return item.filhos.some((filho) => podeVer(filho, permissoes));
}

function ehAtivo(href: string | undefined, caminho: string): boolean {
  if (!href) return false;
  return href === "/" ? caminho === "/" : caminho === href;
}

function grupoAtivo(item: ItemMenu, caminho: string): boolean {
  return (item.filhos ?? []).some(
    (filho) => filho.href && caminho.startsWith(filho.href),
  );
}

export function CascaDoApp({ eu, children }: { eu: Eu; children: ReactNode }) {
  const caminho = usePathname();
  const itens = MENU.filter((item) => podeVer(item, eu.permissoes));

  const [menuAberto, setMenuAberto] = useState(false);
  const [abertos, setAbertos] = useState<string[]>(() =>
    itens.filter((item) => grupoAtivo(item, caminho)).map((item) => item.titulo),
  );

  // Navegar fecha o menu no celular. Ajustar durante a renderização (em vez
  // de um useEffect) evita o re-render em cascata de um setState no efeito.
  const [caminhoAnterior, setCaminhoAnterior] = useState(caminho);
  if (caminho !== caminhoAnterior) {
    setCaminhoAnterior(caminho);
    setMenuAberto(false);
  }

  function alternar(titulo: string) {
    setAbertos((atuais) =>
      atuais.includes(titulo)
        ? atuais.filter((item) => item !== titulo)
        : [...atuais, titulo],
    );
  }

  return (
    <div className="min-h-screen bg-[#f7f8f8] lg:grid lg:grid-cols-[16rem_1fr]">
      <MotorSincronizacao />
      <SincronizarSessao eu={eu} />
      {/* Barra do celular */}
      <div className="flex items-center justify-between border-b border-[#dbe1e4] bg-white px-4 py-3 lg:hidden">
        <button
          type="button"
          onClick={() => setMenuAberto((valor) => !valor)}
          aria-expanded={menuAberto}
          aria-controls="menu-lateral"
          className="rounded-md border border-[#dbe1e4] px-3 py-1.5 text-sm text-[#16222b]"
        >
          Menu
        </button>
        <p className="font-medium text-[#16222b]">{eu.empresa.nome}</p>
        <IndicadorConexao variante="claro" />
      </div>

      <aside
        id="menu-lateral"
        className={`${
          menuAberto ? "block" : "hidden"
        } border-b border-[#dbe1e4] bg-[#16222b] lg:sticky lg:top-0 lg:block lg:h-screen lg:border-b-0`}
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-white/10 px-5 py-5">
            <p className="text-sm font-semibold tracking-tight text-white">
              {eu.empresa.nome}
            </p>
            <p className="mt-0.5 text-xs text-[#a9bac4]">
              Plano {eu.plano === "pro" ? "Pro" : "Base"}
            </p>
            <div className="mt-2">
              <IndicadorConexao variante="escuro" />
            </div>
          </div>

          <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Menu principal">
            <ul className="flex flex-col gap-0.5">
              {itens.map((item) => {
                const filhos = (item.filhos ?? []).filter((filho) =>
                  podeVer(filho, eu.permissoes),
                );

                if (filhos.length === 0) {
                  return (
                    <li key={item.titulo}>
                      <ItemSimples item={item} caminho={caminho} />
                    </li>
                  );
                }

                const aberto = abertos.includes(item.titulo);
                const idPainel = `submenu-${item.titulo.toLowerCase()}`;

                return (
                  <li key={item.titulo}>
                    <button
                      type="button"
                      onClick={() => alternar(item.titulo)}
                      aria-expanded={aberto}
                      aria-controls={idPainel}
                      className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm text-[#e7ecef] transition-colors hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/40"
                    >
                      {item.titulo}
                      <svg
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                        className={`size-4 transition-transform ${aberto ? "rotate-90" : ""}`}
                      >
                        <path
                          d="M7 5l6 5-6 5"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>

                    {aberto ? (
                      <ul id={idPainel} className="mb-1 ml-3 flex flex-col gap-0.5 border-l border-white/10 pl-3">
                        {filhos.map((filho) => (
                          <li key={filho.titulo}>
                            <ItemSimples item={filho} caminho={caminho} />
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="border-t border-white/10 px-5 py-4">
            <p className="text-sm text-white">{eu.usuario.nome}</p>
            <p className="text-xs text-[#a9bac4]">{eu.papel}</p>
            <div className="mt-3 flex items-center gap-4 text-xs">
              <Link href="/escolher-empresa" className="text-[#a9bac4] hover:text-white">
                Trocar negócio
              </Link>
              <form action={sair}>
                <button type="submit" className="text-[#a9bac4] hover:text-white">
                  Sair
                </button>
              </form>
            </div>
          </div>
        </div>
      </aside>

      <main className="min-w-0">{children}</main>
    </div>
  );
}

function ItemSimples({ item, caminho }: { item: ItemMenu; caminho: string }) {
  if (item.emBreve || !item.href) {
    return (
      <span className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-[#7b8e99]">
        {item.titulo}
        <span className="text-[11px] text-[#5d7180]">em breve</span>
      </span>
    );
  }

  const ativo = ehAtivo(item.href, caminho);
  return (
    <Link
      href={item.href}
      aria-current={ativo ? "page" : undefined}
      className={`block rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/40 ${
        ativo
          ? "bg-white/15 font-medium text-white"
          : "text-[#e7ecef] hover:bg-white/10"
      }`}
    >
      {item.titulo}
    </Link>
  );
}
