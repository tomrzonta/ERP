"use client";

import { useState } from "react";

import { Modal } from "@/components/ui/modal";
import type { EstadoFormulario } from "@/modules/auth/types";
import type { Produto, Unidade } from "@/modules/produtos/types";
import { FormularioComponente } from "./formulario-componente";
import { FormularioNovoInsumo } from "./formulario-novo-insumo";
import { ListaComponentes, type ComponenteExibido } from "./lista-componentes";

type Acao = (estado: EstadoFormulario, dados: FormData) => Promise<EstadoFormulario>;

export function SecaoComponentes({
  produtoCompostoId,
  componentes,
  candidatos,
  unidades,
  podeEditar,
  acaoAdicionar,
  acaoCriarInsumo,
}: {
  produtoCompostoId: string;
  componentes: ComponenteExibido[];
  candidatos: Produto[];
  unidades: Unidade[];
  podeEditar: boolean;
  acaoAdicionar: Acao;
  acaoCriarInsumo: Acao;
}) {
  const [criandoInsumo, setCriandoInsumo] = useState(false);

  return (
    <>
      <ListaComponentes
        produtoCompostoId={produtoCompostoId}
        componentes={componentes}
        podeEditar={podeEditar}
      />

      {podeEditar ? (
        <div className="mt-8 max-w-xl">
          <FormularioComponente acao={acaoAdicionar} candidatos={candidatos} />
          <button
            type="button"
            onClick={() => setCriandoInsumo(true)}
            className="mt-4 text-sm text-[#0f6d5c] hover:underline"
          >
            Não encontrou? Cadastrar um insumo novo
          </button>
        </div>
      ) : null}

      {podeEditar ? (
        <Modal aberto={criandoInsumo} aoFechar={() => setCriandoInsumo(false)} titulo="Novo insumo">
          <FormularioNovoInsumo acao={acaoCriarInsumo} unidades={unidades} />
        </Modal>
      ) : null}
    </>
  );
}
