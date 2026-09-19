import type { StatusVenda } from "../types";

const ESTILOS: Record<StatusVenda, string> = {
  aberto: "bg-[#fdf3e0] text-[#a86b0f]",
  fechado: "bg-[#0f6d5c]/10 text-[#0f6d5c]",
  cancelado: "bg-[#a8341f]/10 text-[#a8341f]",
};

const ROTULOS: Record<StatusVenda, string> = {
  aberto: "Aberto",
  fechado: "Fechado",
  cancelado: "Cancelado",
};

export function SeloStatus({ status }: { status: StatusVenda }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${ESTILOS[status]}`}
    >
      {ROTULOS[status]}
    </span>
  );
}
