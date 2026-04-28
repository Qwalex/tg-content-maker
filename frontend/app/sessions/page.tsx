"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function SessionsPage() {
  const [owner, setOwner] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function create() {
    try {
      setError("");
      const data = await api<{ id: number; auth_state: string }>("/api/sessions", {
        method: "POST",
        body: JSON.stringify({ owner_id: owner })
      });
      setSessionId(data.id);
      setStatus(data.auth_state);
    } catch (e) {
      setError(String(e));
    }
  }

  async function qr() {
    if (!sessionId) return;
    try {
      setError("");
      const data = await api<{ auth_state: string }>(`/api/sessions/${sessionId}/qr`);
      setStatus(data.auth_state);
    } catch (e) {
      setError(String(e));
    }
  }

  async function confirm2fa() {
    if (!sessionId) return;
    try {
      setError("");
      const data = await api<{ auth_state: string }>(`/api/sessions/${sessionId}/2fa`, {
        method: "POST",
        body: JSON.stringify({ password })
      });
      setStatus(data.auth_state);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <main className="space-y-3">
      <h1 className="text-xl font-semibold">Sessions</h1>
      <input className="rounded bg-slate-900 p-2" value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="owner_id" />
      <div className="flex gap-2">
        <button onClick={create} className="rounded bg-blue-600 px-3 py-1">Create</button>
        <button onClick={qr} className="rounded bg-slate-700 px-3 py-1">QR</button>
        <input
          className="rounded bg-slate-900 px-2"
          value={password}
          placeholder="2FA password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={confirm2fa} className="rounded bg-emerald-700 px-3 py-1">Confirm 2FA</button>
      </div>
      <div>Session: {sessionId ?? "-"}</div>
      <div>Status: {status || "-"}</div>
      {error && <div className="text-red-400">{error}</div>}
    </main>
  );
}
