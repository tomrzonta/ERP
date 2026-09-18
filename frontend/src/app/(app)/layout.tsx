import type { ReactNode } from "react";

import { CascaDoApp } from "@/components/casca/casca-do-app";
import { obterEu } from "@/modules/auth/eu";

/** Layout das telas com sessão: menu lateral e área de conteúdo. */
export default async function AppLayout({ children }: { children: ReactNode }) {
  const eu = await obterEu();
  return <CascaDoApp eu={eu}>{children}</CascaDoApp>;
}
