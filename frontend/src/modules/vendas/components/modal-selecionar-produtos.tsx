"use client";

import { InputNumero } from "@/components/ui/campo-numero";
import { useState } from "react";

import { Aviso } from "@/components/ui/aviso";
import { Modal } from "@/components/ui/modal";
import { SeletorBusca } from "@/components/ui/seletor-busca";
import { moeda } from "@/lib/formato";
import type { Produto } from "@/modules/produtos/types";

export type ItemSelecionado = {
  produtoId: string;
  quantidade: string;
  descontoPercentual: string;
};

type LinhaCarrinho = {
  produto: Produto;
  quantidade: string;
  descontoPercentual: string;
};

export function ModalSelecionarProdutos({
  aberto,
  aoFechar,
  produtos,
  titulo,
  textoConfirmar,
  aoConfirmar,
}: {
  aberto: boolean;
  aoFechar: () => void;
  produtos: Produto[];
  titulo: string;
  textoConfirmar: string;
  aoConfirmar: (itens: ItemSelecionado[]) => Promise<{ ok: true } | { ok: false; erro: string }>;
}) {
  const [itens, setItens] = useState<LinhaCarrinho[]>([]);
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  // Zera o carrinho sempre que o modal reabre (compara com o valor
  // anterior durante a renderização, em vez de um efeito à parte).
  const [estavaAberto, setEstavaAberto] = useState(aberto);
  if (aberto !== estavaAberto) {
    setEstavaAberto(aberto);
    if (aberto) {
      setItens([]);
      setErro("");
    }
  }

  function adicionarProduto(produto: Produto) {
    setItens((atual) => {
      if (atual.some((item) => item.produto.id === produto.id)) return atual;
      return [...atual, { produto, quantidade: "1", descontoPercentual: "0" }];
    });
  }

  function atualizarItem(
    produtoId: string,
    campo: "quantidade" | "descontoPercentual",
    valor: string,
  ) {
    setItens((atual) =>
      atual.map((item) => (item.produto.id === produtoId ? { ...item, [campo]: valor } : item)),
    );
  }

  function removerItem(produtoId: string) {
    setItens((atual) => atual.filter((item) => item.produto.id !== produtoId));
  }

  async function confirmar() {
    if (itens.length === 0) {
      setErro("Selecione pelo menos um produto.");
      return;
    }
    setErro("");
    setEnviando(true);
    const resultado = await aoConfirmar(
      itens.map((item) => ({
        produtoId: item.produto.id,
        quantidade: item.quantidade || "0",
        descontoPercentual: item.descontoPercentual || "0",
      })),
    );
    setEnviando(false);
    if (!resultado.ok) {
      setErro(resultado.erro);
      return;
    }
    aoFechar();
  }

  return (
    <Modal aberto={aberto} aoFechar={aoFechar} titulo={titulo}>
      <div className="flex flex-col gap-4">
        <SeletorBusca
          itens={produtos}
          chave={(produto) => produto.id}
          correspondeAoTermo={(produto, termo) =>
            produto.nome.toLowerCase().includes(termo) || produto.sku.toLowerCase().includes(termo)
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

        {itens.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-[#dbe1e4] bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-[#dbe1e4] text-left text-[#5b6b75]">
                <tr>
                  <th className="px-3 py-2 font-medium">Produto</th>
                  <th className="px-3 py-2 font-medium">Qtd.</th>
                  <th className="px-3 py-2 font-medium">Desc. %</th>
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
                        aoMudar={(valorNovo) =>
                          atualizarItem(item.produto.id, "quantidade", valorNovo)
                        }
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
          <p className="text-sm text-[#5b6b75]">Nenhum produto selecionado ainda.</p>
        )}

        {erro ? <Aviso>{erro}</Aviso> : null}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={aoFechar}
            className="rounded-md border border-[#dbe1e4] bg-white px-4 py-2.5 text-sm text-[#16222b] transition-colors hover:border-[#0f6d5c]"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={enviando}
            onClick={confirmar}
            className="rounded-md bg-[#0f6d5c] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#0b564a] disabled:opacity-60"
          >
            {enviando ? "Adicionando..." : textoConfirmar}
          </button>
        </div>
      </div>
    </Modal>
  );
}
