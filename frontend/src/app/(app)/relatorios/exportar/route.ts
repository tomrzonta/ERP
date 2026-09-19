import { env } from "@/lib/env";
import { tokenDeAcesso } from "@/lib/server/sessao";

/** Baixa o CSV de vendas do período. O navegador nunca fala com a API nem vê
 * o token: este handler busca no servidor e repassa o arquivo. */
export async function GET(request: Request) {
  const token = await tokenDeAcesso();
  if (!token) {
    return new Response("Sessão expirada.", { status: 401 });
  }

  const parametros = new URL(request.url).searchParams;
  const dias = [7, 30, 90].includes(Number(parametros.get("dias"))) ? Number(parametros.get("dias")) : 30;
  const data = (deslocamento: number) =>
    new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo" }).format(
      new Date(Date.now() - deslocamento * 86_400_000),
    );

  const resposta = await fetch(
    `${env.apiUrl}/relatorios/exportar/vendas?inicio=${data(dias - 1)}&fim=${data(0)}`,
    { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );

  if (!resposta.ok) {
    const mensagem =
      resposta.status === 402
        ? "A exportação faz parte do plano Pro."
        : "Não foi possível gerar o arquivo.";
    return new Response(mensagem, { status: resposta.status });
  }

  return new Response(resposta.body, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition":
        resposta.headers.get("content-disposition") ?? 'attachment; filename="vendas.csv"',
    },
  });
}
