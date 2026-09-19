/**
 * Service worker mínimo: só garante que a página de fallback offline
 * (/offline) esteja disponível quando a navegação falhar por falta de
 * internet. Não faz cache agressivo de páginas nem de chamadas à API —
 * essas continuam sempre pedindo a versão mais nova quando há rede.
 */
const CACHE_NOME = "erp-offline-v1";
const URLS_PRECACHE = ["/offline", "/manifest.json", "/icon.svg"];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches
      .open(CACHE_NOME)
      .then((cache) => cache.addAll(URLS_PRECACHE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((chaves) =>
        Promise.all(chaves.filter((chave) => chave !== CACHE_NOME).map((chave) => caches.delete(chave))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (evento) => {
  // Só intercepta navegação (carregar uma página) — assets, API etc. seguem
  // direto pra rede, sem passar pelo service worker.
  if (evento.request.mode !== "navigate") return;

  evento.respondWith(
    fetch(evento.request).catch(() => caches.match("/offline").then((resposta) => resposta ?? Response.error())),
  );
});
