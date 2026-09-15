import { StatusSistema } from "@/modules/health/components/status-sistema";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-2xl font-bold">ERP</h1>
      <StatusSistema />
    </main>
  );
}
