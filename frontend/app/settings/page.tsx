"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [ignoreImages, setIgnoreImages] = useState(false);
  const [ignoreVideos, setIgnoreVideos] = useState(false);

  useEffect(() => {
    api<{ ignore_images: boolean; ignore_videos: boolean }>("/api/settings/global").then((s) => {
      setIgnoreImages(s.ignore_images);
      setIgnoreVideos(s.ignore_videos);
    });
  }, []);

  async function save() {
    await api("/api/settings/global", {
      method: "PATCH",
      body: JSON.stringify({ ignore_images: ignoreImages, ignore_videos: ignoreVideos })
    });
  }

  return (
    <main className="space-y-3">
      <h1 className="text-xl font-semibold">Global Filters</h1>
      <label className="block">
        <input type="checkbox" checked={ignoreImages} onChange={(e) => setIgnoreImages(e.target.checked)} /> Ignore images
      </label>
      <label className="block">
        <input type="checkbox" checked={ignoreVideos} onChange={(e) => setIgnoreVideos(e.target.checked)} /> Ignore videos
      </label>
      <button onClick={save} className="rounded bg-blue-600 px-3 py-1">Save</button>
    </main>
  );
}
