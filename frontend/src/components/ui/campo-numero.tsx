"use client";

import { useEffect, useLayoutEffect, useRef, useState, type InputHTMLAttributes } from "react";

import { casasDaUnidade } from "@/lib/unidades";

/**
 * Digitação padronizada de números, no estilo maquininha: o campo sempre
 * mostra o formato completo (R$ 0,00 · 0,0 g · 0 un) e cada dígito digitado
 * entra pela direita, empurrando os zeros. Digitar 5, 3, 5 em R$ dá
 * 0,05 → 0,53 → 5,35; apagar remove o último dígito.
 *
 * O formato define as casas e os enfeites:
 * - `dinheiro`: 2 casas, prefixo R$;
 * - `custo`: 4 casas, prefixo R$ (custo por grama, por ml);
 * - `percentual`: 2 casas, sufixo %;
 * - `quantidade`: casas da `unidade` (un 0 · g 1 · kg 3 · ...) e a sigla
 *   dela como sufixo; sem unidade, 3 casas.
 *
 * Só dígitos, sem negativo, até 12 dígitos inteiros. O valor que sai do
 * componente (campo oculto `nome` ou `aoMudar`) usa sempre ponto e todas as
 * casas ("5.35"), como a API espera.
 */
export type FormatoNumero = "dinheiro" | "quantidade" | "custo" | "percentual";

const MAX_DIGITOS_INTEIROS = 12;

function casasDoFormato(formato: FormatoNumero, unidade?: string, casas?: number): number {
  if (casas !== undefined) return casas;
  if (formato === "dinheiro" || formato === "percentual") return 2;
  if (formato === "custo") return 4;
  return casasDaUnidade(unidade);
}

/** Valor da API ("12.5", "3.500000") → dígitos sem vírgula, arredondando às
 * casas do campo. "" e zero viram "". */
export function digitosDe(valor: string, casas: number): string {
  const numero = Number(valor);
  if (valor.trim() === "" || !Number.isFinite(numero) || numero < 0) return "";
  const fixo = numero.toFixed(casas).replace(".", "");
  return fixo.replace(/^0+/, "");
}

function completar(digitos: string, casas: number): string {
  return digitos.padStart(casas + 1, "0");
}

/** Dígitos → texto mostrado, com milhar: "123456" (2 casas) → "1.234,56". */
export function exibir(digitos: string, casas: number): string {
  const cheio = completar(digitos, casas);
  const inteiro = casas > 0 ? cheio.slice(0, -casas) : cheio;
  const fracao = casas > 0 ? cheio.slice(-casas) : "";
  const agrupado = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return casas > 0 ? `${agrupado},${fracao}` : agrupado;
}

/** Dígitos → valor da API, com todas as casas: "535" (2) → "5.35". */
export function normalizar(digitos: string, casas: number): string {
  const cheio = completar(digitos, casas);
  const inteiro = casas > 0 ? cheio.slice(0, -casas) : cheio;
  return casas > 0 ? `${inteiro}.${cheio.slice(-casas)}` : inteiro;
}

type PropsInput = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "value" | "defaultValue" | "onChange" | "type" | "name" | "min" | "max"
> & {
  formato: FormatoNumero;
  /** Unidade de medida (só `quantidade`): define as casas e o sufixo. */
  unidade?: string;
  /** Força as casas, ignorando formato e unidade. */
  casas?: number;
  /** Cria um campo oculto com o valor normalizado pro formulário. */
  nome?: string;
  /** Modo controlado: valor com ponto ("12.5"). */
  valor?: string;
  aoMudar?: (valor: string) => void;
  /** Modo não controlado: valor inicial com ponto. */
  valorInicial?: string;
  /** Teto do valor; percentual usa 100 se não informado. */
  maximo?: number;
  /** Exige valor maior que zero (senão aceita zero). */
  positivo?: boolean;
  /** Texto fixo depois do número; padrão: % ou a unidade. */
  sufixo?: string;
  classe?: string;
};

const CLASSE_PADRAO =
  "w-full rounded-md border border-[#dbe1e4] bg-white px-3 py-2.5 text-[#16222b] outline-none transition-colors placeholder:text-[#9aa7af] focus:border-[#0f6d5c] focus:ring-2 focus:ring-[#0f6d5c]/20";

/** Campo numérico sem rótulo (para tabelas, carrinhos e linhas). */
export function InputNumero({
  formato,
  unidade,
  casas: casasForcadas,
  nome,
  valor,
  aoMudar,
  valorInicial,
  positivo,
  maximo,
  sufixo,
  classe,
  onFocus,
  ...resto
}: PropsInput) {
  const casas = casasDoFormato(formato, unidade, casasForcadas);
  const controlado = valor !== undefined;
  const [digitos, setDigitos] = useState(() => digitosDe(valor ?? valorInicial ?? "", casas));
  const [valorAnterior, setValorAnterior] = useState(valor);
  const referencia = useRef<HTMLInputElement>(null);

  // Valor de fora mudou (ex. o formulário limpou o campo): acompanha.
  if (valor !== valorAnterior) {
    setValorAnterior(valor);
    if (valor !== undefined && digitosDe(valor, casas) !== digitos) {
      setDigitos(digitosDe(valor, casas));
    }
  }

  // Formulário não controlado que é resetado (useActionState) volta ao inicial.
  useEffect(() => {
    const formulario = referencia.current?.form;
    if (!formulario || controlado) return;
    const aoResetar = () => setDigitos(digitosDe(valorInicial ?? "", casas));
    formulario.addEventListener("reset", aoResetar);
    return () => formulario.removeEventListener("reset", aoResetar);
  }, [controlado, valorInicial, casas]);

  // O cursor fica sempre no fim: os dígitos entram pela direita.
  useLayoutEffect(() => {
    const campo = referencia.current;
    if (campo && document.activeElement === campo) {
      campo.setSelectionRange(campo.value.length, campo.value.length);
    }
  }, [digitos]);

  const normalizado = normalizar(digitos, casas);
  const mensagem = positivo && !(Number(normalizado) > 0) ? "Informe um valor maior que zero." : "";
  useEffect(() => {
    referencia.current?.setCustomValidity(mensagem);
  }, [mensagem]);

  const prefixo = formato === "dinheiro" || formato === "custo" ? "R$" : null;
  const final = sufixo ?? (formato === "percentual" ? "%" : formato === "quantidade" ? unidade : null);

  return (
    <div className="relative">
      {prefixo ? (
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-[#5b6b75]">
          {prefixo}
        </span>
      ) : null}
      <input
        {...resto}
        ref={referencia}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        value={exibir(digitos, casas)}
        onChange={(evento) => {
          let novos = evento.target.value.replace(/\D/g, "").replace(/^0+/, "");
          novos = novos.slice(0, MAX_DIGITOS_INTEIROS + casas);
          const teto = maximo ?? (formato === "percentual" ? 100 : undefined);
          if (teto !== undefined && Number(normalizar(novos, casas)) > teto) {
            novos = digitosDe(String(teto), casas);
          }
          setDigitos(novos);
          aoMudar?.(normalizar(novos, casas));
        }}
        onFocus={(evento) => {
          const campo = evento.currentTarget;
          campo.setSelectionRange(campo.value.length, campo.value.length);
          onFocus?.(evento);
        }}
        onClick={(evento) => {
          const campo = evento.currentTarget;
          campo.setSelectionRange(campo.value.length, campo.value.length);
        }}
        className={`${classe ?? CLASSE_PADRAO} text-right tabular-nums ${prefixo ? "pl-10" : ""} ${
          final ? (final.length > 2 ? "pr-12" : "pr-9") : ""
        }`}
      />
      {final ? (
        <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-[#5b6b75]">
          {final}
        </span>
      ) : null}
      {nome ? <input type="hidden" name={nome} value={normalizado} /> : null}
    </div>
  );
}

/** Campo numérico com rótulo e dica, no mesmo estilo do `Campo`. */
export function CampoNumero({
  nome,
  rotulo,
  dica,
  ...props
}: PropsInput & { nome: string; rotulo: string; dica?: string }) {
  const idDica = dica ? `${nome}-dica` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={nome} className="text-sm font-medium text-[#16222b]">
        {rotulo}
      </label>
      <InputNumero id={nome} nome={nome} aria-describedby={idDica} {...props} />
      {dica ? (
        <p id={idDica} className="text-sm text-[#5b6b75]">
          {dica}
        </p>
      ) : null}
    </div>
  );
}
