"use client";

import { useEffect } from "react";

/** Registra o service worker (cache do app + página de fallback offline).
 * Sem suporte no navegador, o app continua funcionando normalmente — só
 * não fica disponível sem internet. */
export function RegistrarServiceWorker() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);

  return null;
}
