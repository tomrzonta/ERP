"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api-client";
import { getHealth } from "../api";
import type { HealthStatus } from "../types";

type Estado =
  | { tipo: "carregando" }
  | { tipo: "ok"; dados: HealthStatus }
  | { tipo: "erro"; mensagem: string };

export function StatusSistema() {
  const [estado, setEstado] = useState<Estado>({ tipo: "carregando" });

  const verificar = useCallback(() => {
    getHealth()
      .then((dados) => setEstado({ tipo: "ok", dados }))
      .catch((erro: unknown) =>
        setEstado({
          tipo: "erro",
          mensagem: erro instanceof ApiError ? erro.message : "Erro inesperado.",
        }),
      );
  }, []);

  useEffect(() => {
    verificar();
  }, [verificar]);

  function tentarNovamente() {
    setEstado({ tipo: "carregando" });
    verificar();
  }

  return (
    <div className="w-full max-w-sm rounded-xl border border-neutral-200 p-6 dark:border-neutral-800">
      <h2 className="mb-4 text-lg font-semibold">Status do sistema</h2>

      {estado.tipo === "carregando" && (
        <p className="text-neutral-500">Verificando...</p>
      )}

      {estado.tipo === "ok" && (
        <dl className="space-y-2 text-sm">
          <Linha rotulo="API" valor={estado.dados.api} ok />
          <Linha
            rotulo="Banco"
            valor={estado.dados.banco}
            ok={estado.dados.banco === "ok"}
          />
          <Linha rotulo="Ambiente" valor={estado.dados.ambiente} ok />
        </dl>
      )}

      {estado.tipo === "erro" && (
        <div className="space-y-3">
          <p className="text-sm text-red-600">{estado.mensagem}</p>
          <button
            onClick={tentarNovamente}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm text-white dark:bg-white dark:text-neutral-900"
          >
            Tentar novamente
          </button>
        </div>
      )}
    </div>
  );
}

function Linha({ rotulo, valor, ok }: { rotulo: string; valor: string; ok: boolean }) {
  return (
    <div className="flex justify-between">
      <dt className="text-neutral-500">{rotulo}</dt>
      <dd className={ok ? "font-medium text-green-600" : "font-medium text-red-600"}>
        {valor}
      </dd>
    </div>
  );
}
