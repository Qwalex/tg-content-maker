"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Copier = {
  id: number;
  name: string;
  source_chat_id: string;
  is_active: boolean;
  source_override_enabled: boolean;
  ignore_images_override: boolean | null;
  ignore_videos_override: boolean | null;
};

export default function CopiersPage() {
  const [list, setList] = useState<Copier[]>([]);
  const [newCopier, setNewCopier] = useState({ session_id: 1, name: "", source_chat_id: "" });
  const [newTarget, setNewTarget] = useState({ copier_id: 0, target_chat_id: "", language_code: "en", user_prompt: "" });
  const [error, setError] = useState("");

  async function load() {
    setList(await api<Copier[]>("/api/copiers"));
  }

  useEffect(() => {
    load();
  }, []);

  async function createCopier() {
    try {
      setError("");
      await api("/api/copiers", {
        method: "POST",
        body: JSON.stringify(newCopier)
      });
      setNewCopier({ ...newCopier, name: "", source_chat_id: "" });
      await load();
    } catch (e) {
      setError(String(e));
    }
  }

  async function toggleActive(copier: Copier) {
    await api(`/api/copiers/${copier.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !copier.is_active })
    });
    await load();
  }

  async function setOverride(copier: Copier, key: "ignore_images_override" | "ignore_videos_override", value: boolean) {
    await api(`/api/copiers/${copier.id}/group-settings`, {
      method: "PATCH",
      body: JSON.stringify({ source_override_enabled: true, [key]: value })
    });
    await load();
  }

  async function addTarget() {
    if (!newTarget.copier_id) return;
    try {
      setError("");
      await api(`/api/copiers/${newTarget.copier_id}/targets`, {
        method: "POST",
        body: JSON.stringify({
          target_chat_id: newTarget.target_chat_id,
          language_code: newTarget.language_code,
          user_prompt: newTarget.user_prompt || null
        })
      });
      setNewTarget({ ...newTarget, target_chat_id: "", user_prompt: "" });
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <main className="space-y-4">
      <h1 className="text-xl font-semibold">Copiers</h1>
      <div className="rounded border border-slate-800 p-3 space-y-2">
        <div className="font-medium">Create Copier</div>
        <div className="flex gap-2">
          <input
            className="rounded bg-slate-900 p-2"
            type="number"
            value={newCopier.session_id}
            onChange={(e) => setNewCopier({ ...newCopier, session_id: Number(e.target.value) })}
            placeholder="session_id"
          />
          <input
            className="rounded bg-slate-900 p-2"
            value={newCopier.name}
            onChange={(e) => setNewCopier({ ...newCopier, name: e.target.value })}
            placeholder="name"
          />
          <input
            className="rounded bg-slate-900 p-2"
            value={newCopier.source_chat_id}
            onChange={(e) => setNewCopier({ ...newCopier, source_chat_id: e.target.value })}
            placeholder="source_chat_id"
          />
          <button className="rounded bg-blue-600 px-3 py-1" onClick={createCopier}>Create</button>
        </div>
      </div>

      {list.map((c) => (
        <div key={c.id} className="rounded border border-slate-800 p-3 space-y-2">
          <div>{c.name} | {c.source_chat_id} | {c.is_active ? "active" : "paused"}</div>
          <div className="flex gap-2">
            <button className="rounded bg-slate-700 px-2 py-1 text-sm" onClick={() => toggleActive(c)}>
              {c.is_active ? "Pause" : "Activate"}
            </button>
            <button className="rounded bg-slate-700 px-2 py-1 text-sm" onClick={() => setOverride(c, "ignore_images_override", true)}>
              Ignore images
            </button>
            <button className="rounded bg-slate-700 px-2 py-1 text-sm" onClick={() => setOverride(c, "ignore_videos_override", true)}>
              Ignore videos
            </button>
          </div>
        </div>
      ))}

      <div className="rounded border border-slate-800 p-3 space-y-2">
        <div className="font-medium">Add Target</div>
        <div className="flex gap-2">
          <input
            className="rounded bg-slate-900 p-2"
            type="number"
            value={newTarget.copier_id || ""}
            onChange={(e) => setNewTarget({ ...newTarget, copier_id: Number(e.target.value) })}
            placeholder="copier_id"
          />
          <input
            className="rounded bg-slate-900 p-2"
            value={newTarget.target_chat_id}
            onChange={(e) => setNewTarget({ ...newTarget, target_chat_id: e.target.value })}
            placeholder="@channel or -100..."
          />
          <input
            className="rounded bg-slate-900 p-2"
            value={newTarget.language_code}
            onChange={(e) => setNewTarget({ ...newTarget, language_code: e.target.value })}
            placeholder="lang"
          />
          <input
            className="rounded bg-slate-900 p-2"
            value={newTarget.user_prompt}
            onChange={(e) => setNewTarget({ ...newTarget, user_prompt: e.target.value })}
            placeholder="prompt (optional)"
          />
          <button className="rounded bg-blue-600 px-3 py-1" onClick={addTarget}>Add</button>
        </div>
      </div>
      {error && <div className="text-red-400">{error}</div>}
    </main>
  );
}
