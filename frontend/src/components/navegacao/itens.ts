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
  { titulo: "Início", href: "/" },
  {
    titulo: "Produtos",
    permissao: "produtos.ver",
    filhos: [
      { titulo: "Todos os produtos", href: "/produtos" },
      { titulo: "Novo produto", href: "/produtos/novo", permissao: "produtos.editar" },
      { titulo: "Categorias", emBreve: true },
      { titulo: "Composições", emBreve: true },
    ],
  },
  {
    titulo: "Estoque",
    filhos: [
      { titulo: "Movimentações", emBreve: true },
      { titulo: "Entradas e compras", emBreve: true },
      { titulo: "Ajustes", emBreve: true },
    ],
  },
  {
    titulo: "Vendas",
    filhos: [
      { titulo: "Caixa", emBreve: true },
      { titulo: "Histórico", emBreve: true },
    ],
  },
  { titulo: "Clientes", emBreve: true },
  {
    titulo: "Financeiro",
    filhos: [
      { titulo: "Caixa do dia", emBreve: true },
      { titulo: "Contas a pagar e receber", emBreve: true },
    ],
  },
  { titulo: "Relatórios", emBreve: true },
  {
    titulo: "Configurações",
    filhos: [
      { titulo: "Pessoas e papéis", emBreve: true, permissao: "membros.ver" },
      { titulo: "Dados do negócio", emBreve: true, permissao: "empresa.editar" },
      { titulo: "Plano e assinatura", emBreve: true, permissao: "assinatura.ver" },
    ],
  },
];
