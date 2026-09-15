export type HealthStatus = {
  api: "ok";
  banco: "ok" | "indisponivel";
  ambiente: "local" | "staging" | "production";
};
