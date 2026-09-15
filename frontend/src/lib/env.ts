/**
 * Variáveis de ambiente do frontend, validadas em um único lugar.
 * Variáveis NEXT_PUBLIC_* ficam visíveis no navegador: nunca coloque segredos nelas.
 */
const apiUrl = process.env.NEXT_PUBLIC_API_URL;

if (!apiUrl) {
  throw new Error(
    "NEXT_PUBLIC_API_URL não definida. Copie .env.example para .env.local.",
  );
}

export const env = { apiUrl };
