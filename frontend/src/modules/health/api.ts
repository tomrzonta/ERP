import { apiFetch } from "@/lib/api-client";
import type { HealthStatus } from "./types";

export function getHealth() {
  return apiFetch<HealthStatus>("/health", { cache: "no-store" });
}
