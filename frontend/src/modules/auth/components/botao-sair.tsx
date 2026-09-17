import { sair } from "../actions";

export function BotaoSair() {
  return (
    <form action={sair}>
      <button
        type="submit"
        className="text-sm text-[#5b6b75] underline decoration-[#dbe1e4] underline-offset-4 transition-colors hover:text-[#16222b]"
      >
        Sair
      </button>
    </form>
  );
}
