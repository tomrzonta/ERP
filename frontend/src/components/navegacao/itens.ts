/**
 * Estrutura do menu lateral.
 *
 * Um item com `filhos` vira um grupo em sanfona. `permissao` esconde o item
 * de quem não pode usá-lo, e `emBreve` mostra o que ainda vai existir, sem
 * link, para o lojista saber onde as coisas vão aparecer.
 */

export type ItemMenu = {
  titulo: string;
  href?: string;
  permissao?: string;
  emBreve?: boolean;
  filhos?: ItemMenu[];
};

export const MENU: ItemMenu[] = [
  { titulo: "Painel", href: "/", permissao: "relatorios.ver" },
  {
    titulo: "Produtos",
    permissao: "produtos.ver",
    filhos: [
      { titulo: "Vendáveis", href: "/produtos" },
      { titulo: "Insumos", href: "/produtos/insumos" },
      { titulo: "Kits", href: "/produtos/kits" },
      { titulo: "Novo produto", href: "/produtos/novo", permissao: "produtos.editar" },
      { titulo: "Categorias", emBreve: true },
    ],
  },
  {
    titulo: "Estoque",
    permissao: "estoque.ver",
    filhos: [{ titulo: "Saldos", href: "/estoque" }],
  },
  { titulo: "Vendas", href: "/vendas", permissao: "vendas.ver" },
  { titulo: "Clientes", href: "/clientes", permissao: "clientes.ver" },
  {
    titulo: "Financeiro",
    permissao: "financeiro.ver",
    filhos: [
      { titulo: "Caixa do dia", href: "/caixa" },
      { titulo: "Histórico de caixas", href: "/caixa/historico" },
      { titulo: "Contas a pagar e receber", href: "/contas" },
    ],
  },
  {
    titulo: "Configurações",
    filhos: [
      { titulo: "Pessoas e papéis", emBreve: true, permissao: "membros.ver" },
      { titulo: "Dados do negócio", emBreve: true, permissao: "empresa.editar" },
      { titulo: "Plano e assinatura", emBreve: true, permissao: "assinatura.ver" },
    ],
  },
];
