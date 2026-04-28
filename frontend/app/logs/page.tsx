import { api } from "@/lib/api";

type Log = { id: number; level: string; component: string; message: string };

export default async function LogsPage() {
  const logs = await api<Log[]>("/api/logs");
  return (
    <main className="space-y-3">
      <h1 className="text-xl font-semibold">Logs</h1>
      {logs.map((l) => (
        <div key={l.id} className="rounded border border-slate-800 p-2">
          [{l.level}] {l.component}: {l.message}
        </div>
      ))}
    </main>
  );
}
