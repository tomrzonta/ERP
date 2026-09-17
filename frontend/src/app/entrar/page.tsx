import Link from "next/link";

import { FormularioEntrar } from "@/modules/auth/components/formulario-entrar";
import { MolduraAuth } from "@/modules/auth/components/moldura";

export const metadata = { title: "Entrar · ERP" };

export default function EntrarPage() {
  return (
    <MolduraAuth
      titulo="Entrar"
      descricao="Use o e-mail e a senha da sua conta."
      rodape={
        <>
          Ainda não tem conta?{" "}
          <Link href="/criar-conta" className="font-medium text-[#0f6d5c] underline underline-offset-4">
            Criar conta
          </Link>
        </>
      }
    >
      <FormularioEntrar />
    </MolduraAuth>
  );
}
