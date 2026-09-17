import Link from "next/link";

import { FormularioCriarConta } from "@/modules/auth/components/formulario-criar-conta";
import { MolduraAuth } from "@/modules/auth/components/moldura";

export const metadata = { title: "Criar conta · ERP" };

export default function CriarContaPage() {
  return (
    <MolduraAuth
      titulo="Criar conta"
      descricao="Sua conta começa com 14 dias do plano Pro, sem cartão."
      rodape={
        <>
          Já tem conta?{" "}
          <Link href="/entrar" className="font-medium text-[#0f6d5c] underline underline-offset-4">
            Entrar
          </Link>
        </>
      }
    >
      <FormularioCriarConta />
    </MolduraAuth>
  );
}
