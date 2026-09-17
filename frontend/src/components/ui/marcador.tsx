/** Caixa de marcação. O hidden garante o valor "false" quando desmarcada. */
export function Marcador({
  nome,
  rotulo,
  dica,
  defaultChecked,
}: {
  nome: string;
  rotulo: string;
  dica?: string;
  defaultChecked?: boolean;
}) {
  return (
    <div className="flex gap-3">
      <input type="hidden" name={nome} value="false" />
      <input
        id={nome}
        name={nome}
        type="checkbox"
        value="true"
        defaultChecked={defaultChecked}
        className="mt-1 size-4 accent-[#0f6d5c]"
      />
      <div>
        <label htmlFor={nome} className="text-sm font-medium text-[#16222b]">
          {rotulo}
        </label>
        {dica ? <p className="text-xs text-[#5b6b75]">{dica}</p> : null}
      </div>
    </div>
  );
}
