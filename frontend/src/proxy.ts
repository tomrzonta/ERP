/**
 * Guarda as rotas e renova o token de acesso quando ele expira.
 *
 * O cookie de renovação vale 30 dias; o de acesso, 14 minutos. Quando o de
 * acesso desaparece e o de renovação continua válido, trocamos por um novo par
 * sem incomodar o visitante. Se a renovação falhar, a sessão é limpa.
 */
import { NextResponse, type NextRequest } from "next/server";

const COOKIE_ACESSO = "erp_acesso";
const COOKIE_RENOVACAO = "erp_renovacao";
const SEGUNDOS_ACESSO = 60 * 14;
const SEGUNDOS_RENOVACAO = 60 * 60 * 24 * 30;

const OPCOES = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

const ROTAS_PUBLICAS = ["/entrar", "/criar-conta"];

function paraEntrada(request: NextRequest) {
  const resposta = NextResponse.redirect(new URL("/entrar", request.url));
  resposta.cookies.delete(COOKIE_ACESSO);
  resposta.cookies.delete(COOKIE_RENOVACAO);
  return resposta;
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const publica = ROTAS_PUBLICAS.includes(pathname);
  const acesso = request.cookies.get(COOKIE_ACESSO)?.value;
  const renovacao = request.cookies.get(COOKIE_RENOVACAO)?.value;

  if (!renovacao) {
    return publica ? NextResponse.next() : paraEntrada(request);
  }

  if (publica) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  if (acesso) {
    return NextResponse.next();
  }

  try {
    const resposta = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/renovar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: renovacao }),
    });
    if (!resposta.ok) {
      return paraEntrada(request);
    }
    const tokens = (await resposta.json()) as {
      access_token: string;
      refresh_token: string;
    };

    // Também no request: a página renderizada nesta mesma volta já usa o token novo
    request.cookies.set(COOKIE_ACESSO, tokens.access_token);
    const seguir = NextResponse.next({ request });
    seguir.cookies.set(COOKIE_ACESSO, tokens.access_token, {
      ...OPCOES,
      maxAge: SEGUNDOS_ACESSO,
    });
    seguir.cookies.set(COOKIE_RENOVACAO, tokens.refresh_token, {
      ...OPCOES,
      maxAge: SEGUNDOS_RENOVACAO,
    });
    return seguir;
  } catch {
    return paraEntrada(request);
  }
}

export const config = {
  // Arquivos do PWA (manifest, ícone, service worker) e a página de
  // fallback offline precisam responder sem sessão — inclusive pro próprio
  // service worker conseguir pré-cachear /offline na instalação.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|manifest.json|icon.svg|sw.js|offline).*)",
  ],
};
