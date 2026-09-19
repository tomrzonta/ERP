/**
 * Cache local (IndexedDB) do catálogo — produtos, preço e saldo — pra
 * consulta com o app sem internet, e a fila de vendas feitas offline
 * aguardando sincronizar. Só funciona no navegador; nada aqui roda durante
 * a renderização no servidor.
 */

import type { FormaPagamento } from "@/lib/formas-pagamento";

const NOME_BANCO = "erp-offline";
const VERSAO_BANCO = 3;
const LOJA_PRODUTOS = "produtos";
const LOJA_META = "meta";
const LOJA_FILA_VENDAS = "filaVendas";
const LOJA_FILA_LANCAMENTOS = "filaLancamentos";

export type ProdutoOffline = {
  id: string;
  sku: string;
  nome: string;
  unidade_codigo: string;
  preco_venda: string;
  controla_estoque: boolean;
  fisico: string | null;
  reservado: string | null;
  disponivel: string | null;
};

export type ItemVendaPendente = {
  produtoId: string;
  quantidade: string;
  precoTabela: string;
  descontoPercentual: string;
};

export type PagamentoPendente = {
  forma: FormaPagamento;
  valor: string;
};

export type LancamentoPendente = {
  /** UUID gerado no dispositivo — vira o id do lançamento ao sincronizar. */
  id: string;
  tipo: "entrada" | "saida";
  valor: string;
  formaPagamento: FormaPagamento;
  descricao: string | null;
  ocorridoEm: string;
  criadoEm: string;
  erro: string | null;
};

export type SessaoOffline = {
  usuarioNome: string;
  empresaNome: string;
  papel: string;
  permissoes: string[];
};

export type VendaPendente = {
  /** UUID gerado no dispositivo — é também o id da venda quando sincronizar. */
  id: string;
  clienteId: string | null;
  clienteNovo: { nome: string; telefone?: string } | null;
  itens: ItemVendaPendente[];
  pagamentos: PagamentoPendente[];
  /** ISO — quando a venda de fato aconteceu, não quando vai sincronizar. */
  ocorridoEm: string;
  criadoEm: string;
  /** Preenchido se a última tentativa de sincronizar falhou (erro de
   * negócio, não de rede — erro de rede simplesmente tenta de novo). */
  erro: string | null;
};

function abrirBanco(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const pedido = indexedDB.open(NOME_BANCO, VERSAO_BANCO);
    pedido.onupgradeneeded = () => {
      const db = pedido.result;
      if (!db.objectStoreNames.contains(LOJA_PRODUTOS)) {
        db.createObjectStore(LOJA_PRODUTOS, { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains(LOJA_META)) {
        db.createObjectStore(LOJA_META, { keyPath: "chave" });
      }
      if (!db.objectStoreNames.contains(LOJA_FILA_VENDAS)) {
        db.createObjectStore(LOJA_FILA_VENDAS, { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains(LOJA_FILA_LANCAMENTOS)) {
        db.createObjectStore(LOJA_FILA_LANCAMENTOS, { keyPath: "id" });
      }
    };
    pedido.onsuccess = () => resolve(pedido.result);
    pedido.onerror = () => reject(pedido.error);
  });
}

/** Substitui o catálogo salvo pelo mais recente e marca a hora da sincronização. */
export async function salvarCatalogoOffline(produtos: ProdutoOffline[]): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction([LOJA_PRODUTOS, LOJA_META], "readwrite");
    const lojaProdutos = transacao.objectStore(LOJA_PRODUTOS);
    lojaProdutos.clear();
    for (const produto of produtos) {
      lojaProdutos.put(produto);
    }
    transacao.objectStore(LOJA_META).put({
      chave: "ultimaSincronizacao",
      valor: new Date().toISOString(),
    });
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function listarCatalogoOffline(): Promise<ProdutoOffline[]> {
  const db = await abrirBanco();
  const produtos = await new Promise<ProdutoOffline[]>((resolve, reject) => {
    const transacao = db.transaction(LOJA_PRODUTOS, "readonly");
    const pedido = transacao.objectStore(LOJA_PRODUTOS).getAll();
    pedido.onsuccess = () => resolve(pedido.result as ProdutoOffline[]);
    pedido.onerror = () => reject(pedido.error);
  });
  db.close();
  return produtos;
}

export async function obterUltimaSincronizacao(): Promise<string | null> {
  const db = await abrirBanco();
  const valor = await new Promise<string | null>((resolve, reject) => {
    const transacao = db.transaction(LOJA_META, "readonly");
    const pedido = transacao.objectStore(LOJA_META).get("ultimaSincronizacao");
    pedido.onsuccess = () =>
      resolve((pedido.result as { valor: string } | undefined)?.valor ?? null);
    pedido.onerror = () => reject(pedido.error);
  });
  db.close();
  return valor;
}

/** Guarda quem estava logado, pra saber quem é o usuário (e o que ele pode
 * fazer) na página /offline sem depender do servidor. Não é uma sessão de
 * verdade — o servidor revalida tudo quando a venda sincronizar; isso é só
 * pra decidir o que mostrar na tela enquanto offline. */
export async function salvarSessaoOffline(sessao: SessaoOffline): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_META, "readwrite");
    transacao.objectStore(LOJA_META).put({ chave: "sessao", valor: sessao });
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function obterSessaoOffline(): Promise<SessaoOffline | null> {
  const db = await abrirBanco();
  const sessao = await new Promise<SessaoOffline | null>((resolve, reject) => {
    const transacao = db.transaction(LOJA_META, "readonly");
    const pedido = transacao.objectStore(LOJA_META).get("sessao");
    pedido.onsuccess = () =>
      resolve((pedido.result as { valor: SessaoOffline } | undefined)?.valor ?? null);
    pedido.onerror = () => reject(pedido.error);
  });
  db.close();
  return sessao;
}

export async function adicionarVendaPendente(venda: VendaPendente): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_VENDAS, "readwrite");
    transacao.objectStore(LOJA_FILA_VENDAS).put(venda);
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function listarVendasPendentes(): Promise<VendaPendente[]> {
  const db = await abrirBanco();
  const vendas = await new Promise<VendaPendente[]>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_VENDAS, "readonly");
    const pedido = transacao.objectStore(LOJA_FILA_VENDAS).getAll();
    pedido.onsuccess = () => resolve(pedido.result as VendaPendente[]);
    pedido.onerror = () => reject(pedido.error);
  });
  db.close();
  return vendas.sort((a, b) => a.criadoEm.localeCompare(b.criadoEm));
}

export async function removerVendaPendente(id: string): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_VENDAS, "readwrite");
    transacao.objectStore(LOJA_FILA_VENDAS).delete(id);
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function marcarVendaPendenteComErro(id: string, erro: string): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_VENDAS, "readwrite");
    const loja = transacao.objectStore(LOJA_FILA_VENDAS);
    const pedido = loja.get(id);
    pedido.onsuccess = () => {
      const venda = pedido.result as VendaPendente | undefined;
      if (venda) loja.put({ ...venda, erro });
    };
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function adicionarLancamentoPendente(lancamento: LancamentoPendente): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_LANCAMENTOS, "readwrite");
    transacao.objectStore(LOJA_FILA_LANCAMENTOS).put(lancamento);
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function listarLancamentosPendentes(): Promise<LancamentoPendente[]> {
  const db = await abrirBanco();
  const itens = await new Promise<LancamentoPendente[]>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_LANCAMENTOS, "readonly");
    const pedido = transacao.objectStore(LOJA_FILA_LANCAMENTOS).getAll();
    pedido.onsuccess = () => resolve(pedido.result as LancamentoPendente[]);
    pedido.onerror = () => reject(pedido.error);
  });
  db.close();
  return itens.sort((a, b) => a.criadoEm.localeCompare(b.criadoEm));
}

export async function removerLancamentoPendente(id: string): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_LANCAMENTOS, "readwrite");
    transacao.objectStore(LOJA_FILA_LANCAMENTOS).delete(id);
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}

export async function marcarLancamentoPendenteComErro(id: string, erro: string): Promise<void> {
  const db = await abrirBanco();
  await new Promise<void>((resolve, reject) => {
    const transacao = db.transaction(LOJA_FILA_LANCAMENTOS, "readwrite");
    const loja = transacao.objectStore(LOJA_FILA_LANCAMENTOS);
    const pedido = loja.get(id);
    pedido.onsuccess = () => {
      const item = pedido.result as LancamentoPendente | undefined;
      if (item) loja.put({ ...item, erro });
    };
    transacao.oncomplete = () => resolve();
    transacao.onerror = () => reject(transacao.error);
  });
  db.close();
}
