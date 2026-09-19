"use client";

import { FORMAS_SELECIONAVEIS, ROTULOS_FORMA, type FormaPagamento } from "@/lib/formas-pagamento";
import { InputNumero } from "@/components/ui/campo-numero";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { SeletorBusca } from "@/components/ui/seletor-busca";
import { MotorSincronizacao, avisarFilaAtualizada, EVENTO_FILA_ATUALIZADA } from "@/components/pwa/motor-sincronizacao";
import {
  adicionarLancamentoPendente,
  adicionarVendaPendente,
  listarCatalogoOffline,
  listarLancamentosPendentes,
  listarVendasPendentes,
  obterSessaoOffline,
  obterUltimaSincronizacao,
  removerLancamentoPendente,
  removerVendaPendente,
  type LancamentoPendente,
  type ProdutoOffline,
  type SessaoOffline,
  type VendaPendente,
} from "@/lib/client/banco-local";
import { moeda, numero } from "@/lib/formato";

function tempoOffline(ultimaSincronizacao: string): string {
  const minutos = Math.max(
    0,
    Math.round((Date.now() - new Date(ultimaSincronizacao).getTime()) / 60000),
  );
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return `${horas}h`;
  const dias = Math.floor(horas / 24);
  return `${dias} dia${dias === 1 ? "" : "s"}`;
}


type ItemCarrinho = {
  produto: ProdutoOffline;
  quantidade: string;
  descontoPercentual: string;
};

type LinhaPagamento = {
  chave: string;
  forma: FormaPagamento;
  valor: string;
};

function precoFinalUnitario(item: ItemCarrinho): number {
  const preco = Number(item.produto.preco_venda);
  const desconto = Number(item.descontoPercentual || "0");
  return preco * (1 - desconto / 100);
}

/** Página fora do grupo autenticado (não depende do servidor pra
 * renderizar): é o que o service worker mostra quando a navegação falha
 * por falta de internet. Consulta o catálogo salvo, monta vendas offline
 * (guardadas numa fila local) e mostra o que ainda aguarda sincronizar. */
export default function OfflinePage() {
  const [produtos, setProdutos] = useState<ProdutoOffline[] | null>(null);
  const [ultimaSincronizacao, setUltimaSincronizacao] = useState<string | null>(null);
  const [sessao, setSessao] = useState<SessaoOffline | null | undefined>(undefined);
  const [termo, setTermo] = useState("");
  const [pendentes, setPendentes] = useState<VendaPendente[]>([]);

  const [itens, setItens] = useState<ItemCarrinho[]>([]);
  const [nomeCliente, setNomeCliente] = useState("");
  const [telefoneCliente, setTelefoneCliente] = useState("");
  const proximoIdPagamento = useRef(1);
  const [pagamentos, setPagamentos] = useState<LinhaPagamento[]>(() => [
    { chave: "p0", forma: "dinheiro", valor: "" },
  ]);
  const [mensagem, setMensagem] = useState("");

  const [lancamentosPendentes, setLancamentosPendentes] = useState<LancamentoPendente[]>([]);
  const [tipoLancamento, setTipoLancamento] = useState<"entrada" | "saida">("saida");
  const [formaLancamento, setFormaLancamento] = useState<FormaPagamento>("dinheiro");
  const [valorLancamento, setValorLancamento] = useState("");
  const [descricaoLancamento, setDescricaoLancamento] = useState("");
  const [mensagemLancamento, setMensagemLancamento] = useState("");

  function carregar() {
    listarCatalogoOffline()
      .then(setProdutos)
      .catch(() => setProdutos([]));
    obterUltimaSincronizacao()
      .then(setUltimaSincronizacao)
      .catch(() => {});
    obterSessaoOffline()
      .then(setSessao)
      .catch(() => setSessao(null));
    listarVendasPendentes()
      .then(setPendentes)
      .catch(() => {});
    listarLancamentosPendentes()
      .then(setLancamentosPendentes)
      .catch(() => {});
  }

  useEffect(() => {
    carregar();
    window.addEventListener(EVENTO_FILA_ATUALIZADA, carregar);
    return () => window.removeEventListener(EVENTO_FILA_ATUALIZADA, carregar);
  }, []);

  const podeRegistrarVenda = sessao != null && sessao.permissoes.includes("vendas.registrar");

  const termoBusca = termo.trim().toLowerCase();
  const catalogoFiltrado = (produtos ?? []).filter(
    (produto) =>
      !termoBusca ||
      produto.nome.toLowerCase().includes(termoBusca) ||
      produto.sku.toLowerCase().includes(termoBusca),
  );

  function adicionarProduto(produto: ProdutoOffline) {
    setItens((atual) => {
      if (atual.some((item) => item.produto.id === produto.id)) return atual;
      return [...atual, { produto, quantidade: "1", descontoPercentual: "0" }];
    });
  }

  function atualizarItem(produtoId: string, campo: "quantidade" | "descontoPercentual", valor: string) {
    setItens((atual) =>
      atual.map((item) => (item.produto.id === produtoId ? { ...item, [campo]: valor } : item)),
    );
  }

  function removerItem(produtoId: string) {
    setItens((atual) => atual.filter((item) => item.produto.id !== produtoId));
  }

  const total = itens.reduce(
    (soma, item) => soma + precoFinalUnitario(item) * Number(item.quantidade || "0"),
    0,
  );
  const somaPagamentos = pagamentos.reduce((soma, p) => soma + Number(p.valor || "0"), 0);
  const diferenca = Math.round((total - somaPagamentos) * 100) / 100;

  function adicionarPagamento() {
    const chave = `p${proximoIdPagamento.current++}`;
    setPagamentos((atual) => [
      ...atual,
      { chave, forma: "dinheiro", valor: Math.max(total - somaPagamentos, 0).toFixed(2) },
    ]);
  }

  function atualizarPagamento(chave: string, campo: "forma" | "valor", valor: string) {
    setPagamentos((atual) => atual.map((p) => (p.chave === chave ? { ...p, [campo]: valor } : p)));
  }

  function removerPagamento(chave: string) {
    setPagamentos((atual) => atual.filter((p) => p.chave !== chave));
  }

  async function registrarVenda() {
    setMensagem("");
    if (itens.length === 0) {
      setMensagem("Adicione pelo menos um produto.");
      return;
    }
    if (diferenca !== 0) {
      setMensagem("A soma dos pagamentos precisa bater com o total da venda.");
      return;
    }

    const agora = new Date().toISOString();
    const venda: VendaPendente = {
      id: crypto.randomUUID(),
      clienteId: null,
      clienteNovo: nomeCliente.trim() ? { nome: nomeCliente.trim(), telefone: telefoneCliente || undefined } : null,
      itens: itens.map((item) => ({
        produtoId: item.produto.id,
        quantidade: item.quantidade || "0",
        precoTabela: item.produto.preco_venda,
        descontoPercentual: item.descontoPercentual || "0",
      })),
      pagamentos: pagamentos
        .filter((p) => Number(p.valor || "0") > 0)
        .map((p) => ({ forma: p.forma, valor: p.valor })),
      ocorridoEm: agora,
      criadoEm: agora,
      erro: null,
    };

    await adicionarVendaPendente(venda);
    avisarFilaAtualizada();
    carregar();

    setItens([]);
    setNomeCliente("");
    setTelefoneCliente("");
    setPagamentos([{ chave: "p0", forma: "dinheiro", valor: "" }]);
    setMensagem("Venda guardada. Vai sincronizar sozinha quando a conexão voltar.");
  }

  async function registrarLancamento() {
    setMensagemLancamento("");
    if (!valorLancamento || Number(valorLancamento) <= 0) {
      setMensagemLancamento("Informe um valor maior que zero.");
      return;
    }
    const agora = new Date().toISOString();
    await adicionarLancamentoPendente({
      id: crypto.randomUUID(),
      tipo: tipoLancamento,
      valor: valorLancamento,
      formaPagamento: formaLancamento,
      descricao: descricaoLancamento.trim() || null,
      ocorridoEm: agora,
      criadoEm: agora,
      erro: null,
    });
    avisarFilaAtualizada();
    carregar();
    setValorLancamento("");
    setDescricaoLancamento("");
    setMensagemLancamento(
      "Lançamento guardado. Entra no caixa aberto quando a conexão voltar.",
    );
  }

  async function cancelarLancamentoPendente(id: string) {
    await removerLancamentoPendente(id);
    avisarFilaAtualizada();
    carregar();
  }

  async function cancelarPendente(id: string) {
    await removerVendaPendente(id);
    avisarFilaAtualizada();
    carregar();
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <MotorSincronizacao />
      <h1 className="text-2xl font-semibold tracking-tight text-[#16222b]">Sem conexão</h1>
      <p className="mt-2 max-w-prose text-sm text-[#5b6b75]">
        Você está offline
        {ultimaSincronizacao ? ` há ${tempoOffline(ultimaSincronizacao)}` : ""}. Dá pra registrar
        uma venda com o catálogo salvo
        {ultimaSincronizacao
          ? ` da última vez online, em ${new Date(ultimaSincronizacao).toLocaleString("pt-BR")}`
          : ""}
        . Ela fica guardada neste aparelho e sincroniza sozinha quando a conexão voltar.
      </p>
      {sessao ? (
        <p className="mt-1 text-sm text-[#5b6b75]">
          Logado como <span className="text-[#16222b]">{sessao.usuarioNome}</span> (
          {sessao.papel}) em {sessao.empresaNome}.
        </p>
      ) : null}

      {produtos !== null && produtos.length === 0 ? (
        <p className="mt-6 rounded-md border border-[#a86b0f]/25 bg-[#fdf3e0] px-3 py-2 text-sm text-[#8a5a0f]">
          Nenhum catálogo salvo ainda — abra o app uma vez com internet antes de usar offline.
        </p>
      ) : (
        <>
          {sessao === null ? (
            <p className="mt-6 rounded-md border border-[#a86b0f]/25 bg-[#fdf3e0] px-3 py-2 text-sm text-[#8a5a0f]">
              Nenhuma sessão salva neste aparelho — entre com internet pelo menos uma vez antes de
              registrar vendas offline. Ainda dá pra consultar o catálogo salvo, mais abaixo.
            </p>
          ) : sessao !== undefined && !podeRegistrarVenda ? (
            <p className="mt-6 rounded-md border border-[#a86b0f]/25 bg-[#fdf3e0] px-3 py-2 text-sm text-[#8a5a0f]">
              Seu papel ({sessao.papel}) não registra vendas — só é possível consultar o catálogo
              salvo, mais abaixo.
            </p>
          ) : podeRegistrarVenda ? (
            <>
              <section className="mt-8">
                <h2 className="text-sm font-semibold text-[#16222b]">Itens</h2>
                <div className="mt-3">
              <SeletorBusca
                itens={produtos ?? []}
                chave={(produto) => produto.id}
                correspondeAoTermo={(produto, t) =>
                  produto.nome.toLowerCase().includes(t) || produto.sku.toLowerCase().includes(t)
                }
                aoEscolher={adicionarProduto}
                placeholder="Buscar produto por nome ou SKU..."
                renderItem={(produto) => (
                  <>
                    <span>{produto.nome}</span>
                    <span className="tabular-nums text-sm text-[#5b6b75]">
                      {moeda(produto.preco_venda)}
                    </span>
                  </>
                )}
              />
            </div>

            {itens.length > 0 ? (
              <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
                <table className="w-full text-sm">
                  <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                    <tr>
                      <th className="px-3 py-2 font-medium">Produto</th>
                      <th className="px-3 py-2 font-medium">Qtd.</th>
                      <th className="px-3 py-2 font-medium">Desc. %</th>
                      <th className="px-3 py-2 text-right font-medium">Total</th>
                      <th className="px-3 py-2" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#dbe1e4]">
                    {itens.map((item) => (
                      <tr key={item.produto.id}>
                        <td className="px-3 py-2 font-medium text-[#16222b]">{item.produto.nome}</td>
                        <td className="px-3 py-2">
                          <InputNumero formato="quantidade" unidade={item.produto.unidade_codigo}
                            valor={item.quantidade}
                            aoMudar={(valorNovo) => atualizarItem(item.produto.id, "quantidade", valorNovo)}
                            classe="w-28 rounded-md border border-[#dbe1e4] px-2 py-1.5 text-[#16222b] outline-none focus:border-[#0f6d5c]"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <InputNumero formato="percentual"
                            valor={item.descontoPercentual}
                            aoMudar={(valorNovo) =>
                              atualizarItem(item.produto.id, "descontoPercentual", valorNovo)
                            }
                            classe="w-24 rounded-md border border-[#dbe1e4] px-2 py-1.5 text-[#16222b] outline-none focus:border-[#0f6d5c]"
                          />
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums text-[#16222b]">
                          {moeda((precoFinalUnitario(item) * Number(item.quantidade || "0")).toFixed(2))}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => removerItem(item.produto.id)}
                            className="text-sm text-[#a8341f] hover:underline"
                          >
                            Remover
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-[#5b6b75]">Nenhum item ainda.</p>
            )}
          </section>

          <section className="mt-8">
            <h2 className="text-sm font-semibold text-[#16222b]">Cliente (opcional)</h2>
            <p className="mt-1 text-xs text-[#5b6b75]">
              Offline só dá pra cadastrar cliente novo — buscar um já existente precisa de conexão.
            </p>
            <div className="mt-3 flex flex-wrap gap-3">
              <input
                value={nomeCliente}
                onChange={(e) => setNomeCliente(e.target.value)}
                placeholder="Nome"
                className="w-full max-w-xs rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
              />
              <input
                value={telefoneCliente}
                onChange={(e) => setTelefoneCliente(e.target.value)}
                placeholder="Telefone (opcional)"
                className="w-full max-w-xs rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
              />
            </div>
          </section>

          <section className="mt-8">
            <h2 className="text-sm font-semibold text-[#16222b]">Pagamento</h2>
            <div className="mt-3 flex flex-col gap-3">
              {pagamentos.map((pagamento) => (
                <div key={pagamento.chave} className="flex items-center gap-2">
                  <select
                    value={pagamento.forma}
                    onChange={(e) => atualizarPagamento(pagamento.chave, "forma", e.target.value)}
                    className="rounded-md border border-[#dbe1e4] bg-white px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                  >
                    {FORMAS_SELECIONAVEIS.map((forma) => (
                      <option key={forma} value={forma}>
                        {ROTULOS_FORMA[forma]}
                      </option>
                    ))}
                  </select>
                  <InputNumero formato="dinheiro"
                    valor={pagamento.valor}
                    aoMudar={(valorNovo) => atualizarPagamento(pagamento.chave, "valor", valorNovo)}
                    classe="w-28 rounded-md border border-[#dbe1e4] px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                  />
                  {pagamentos.length > 1 ? (
                    <button
                      type="button"
                      onClick={() => removerPagamento(pagamento.chave)}
                      className="text-sm text-[#a8341f] hover:underline"
                    >
                      Remover
                    </button>
                  ) : null}
                </div>
              ))}
              <button
                type="button"
                onClick={adicionarPagamento}
                className="self-start text-sm text-[#0f6d5c] hover:underline"
              >
                + Dividir em outra forma de pagamento
              </button>
            </div>

            <dl className="mt-4 flex flex-col gap-1 border-t border-[#dbe1e4] pt-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-[#5b6b75]">Total</dt>
                <dd className="font-medium tabular-nums text-[#16222b]">{moeda(total.toFixed(2))}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[#5b6b75]">Pagamentos informados</dt>
                <dd className="tabular-nums text-[#16222b]">{moeda(somaPagamentos.toFixed(2))}</dd>
              </div>
              {diferenca !== 0 ? (
                <div className="flex justify-between text-[#a8341f]">
                  <dt>Diferença</dt>
                  <dd className="tabular-nums">{moeda(diferenca.toFixed(2))}</dd>
                </div>
              ) : null}
            </dl>

            {mensagem ? (
              <p className="mt-3 rounded-md border border-[#dbe1e4] bg-white px-3 py-2 text-sm text-[#16222b]">
                {mensagem}
              </p>
            ) : null}

            <button
              type="button"
              onClick={registrarVenda}
              className="mt-4 rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
            >
                  Registrar venda offline
                </button>
              </section>
            </>
          ) : null}

          {sessao != null && sessao.permissoes.includes("financeiro.operar") ? (
            <section className="mt-8 border-t border-[#dbe1e4] pt-8">
              <h2 className="text-sm font-semibold text-[#16222b]">
                Entrada ou saída de caixa
              </h2>
              <p className="mt-1 text-xs text-[#5b6b75]">
                Sangria, suprimento, conta paga na hora. Entra no caixa aberto quando a conexão
                voltar (é preciso ter um caixa aberto até lá).
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <select
                  value={tipoLancamento}
                  onChange={(e) => setTipoLancamento(e.target.value as "entrada" | "saida")}
                  className="rounded-md border border-[#dbe1e4] bg-white px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                >
                  <option value="saida">Saída</option>
                  <option value="entrada">Entrada</option>
                </select>
                <select
                  value={formaLancamento}
                  onChange={(e) => setFormaLancamento(e.target.value as FormaPagamento)}
                  className="rounded-md border border-[#dbe1e4] bg-white px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                >
                  {FORMAS_SELECIONAVEIS.map((forma) => (
                    <option key={forma} value={forma}>
                      {ROTULOS_FORMA[forma]}
                    </option>
                  ))}
                </select>
                <InputNumero formato="dinheiro"
                  valor={valorLancamento}
                  aoMudar={(valorNovo) => setValorLancamento(valorNovo)}
                  placeholder="Valor"
                  classe="w-28 rounded-md border border-[#dbe1e4] px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                />
                <input
                  value={descricaoLancamento}
                  onChange={(e) => setDescricaoLancamento(e.target.value)}
                  placeholder="Descrição (opcional)"
                  className="w-full max-w-xs rounded-md border border-[#dbe1e4] px-2 py-2 text-sm text-[#16222b] outline-none focus:border-[#0f6d5c]"
                />
                <button
                  type="button"
                  onClick={registrarLancamento}
                  className="rounded-md bg-[#0f6d5c] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#0b564a]"
                >
                  Guardar
                </button>
              </div>
              {mensagemLancamento ? (
                <p className="mt-3 text-sm text-[#16222b]">{mensagemLancamento}</p>
              ) : null}
            </section>
          ) : null}

          {lancamentosPendentes.length > 0 ? (
            <section className="mt-8">
              <h2 className="text-sm font-semibold text-[#16222b]">
                Lançamentos de caixa aguardando sincronizar ({lancamentosPendentes.length})
              </h2>
              <ul className="mt-3 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
                {lancamentosPendentes.map((item) => (
                  <li key={item.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                    <div>
                      <p className="text-[#16222b]">
                        {item.tipo === "entrada" ? "+" : "-"} {moeda(item.valor)} ·{" "}
                        {ROTULOS_FORMA[item.formaPagamento]}
                        {item.descricao ? ` · ${item.descricao}` : ""}
                      </p>
                      {item.erro ? <p className="text-xs text-[#a8341f]">{item.erro}</p> : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => cancelarLancamentoPendente(item.id)}
                      className="shrink-0 text-sm text-[#a8341f] hover:underline"
                    >
                      Cancelar
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {pendentes.length > 0 ? (
            <section className="mt-10 border-t border-[#dbe1e4] pt-8">
              <h2 className="text-sm font-semibold text-[#16222b]">
                Vendas aguardando sincronizar ({pendentes.length})
              </h2>
              <ul className="mt-3 divide-y divide-[#dbe1e4] overflow-hidden rounded-lg border border-[#dbe1e4] bg-white">
                {pendentes.map((venda) => (
                  <li key={venda.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                    <div>
                      <p className="text-[#16222b]">
                        {new Date(venda.ocorridoEm).toLocaleString("pt-BR")} · {venda.itens.length}{" "}
                        {venda.itens.length === 1 ? "item" : "itens"}
                      </p>
                      {venda.erro ? <p className="text-xs text-[#a8341f]">{venda.erro}</p> : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => cancelarPendente(venda.id)}
                      className="shrink-0 text-sm text-[#a8341f] hover:underline"
                    >
                      Cancelar
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="mt-10 border-t border-[#dbe1e4] pt-8">
            <h2 className="text-sm font-semibold text-[#16222b]">Catálogo salvo</h2>
            <input
              value={termo}
              onChange={(e) => setTermo(e.target.value)}
              placeholder="Buscar por nome ou SKU..."
              className="mt-3 w-full max-w-sm rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20"
            />
            <div className="mt-4 overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                  <tr>
                    <th className="px-4 py-3 font-medium">Produto</th>
                    <th className="px-4 py-3 text-right font-medium">Preço</th>
                    <th className="px-4 py-3 text-right font-medium">Disponível</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#dbe1e4]">
                  {catalogoFiltrado.map((produto) => (
                    <tr key={produto.id}>
                      <td className="px-4 py-3 font-medium text-[#16222b]">{produto.nome}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#16222b]">
                        {moeda(produto.preco_venda)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-[#5b6b75]">
                        {produto.controla_estoque && produto.disponivel !== null
                          ? numero(produto.disponivel, 2)
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <Link href="/" className="mt-8 inline-block text-sm text-[#0f6d5c] hover:underline">
        Tentar reconectar
      </Link>
    </div>
  );
}
