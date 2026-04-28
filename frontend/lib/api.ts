function getBase(): string {
  if (typeof window !== "undefined") {
    // Browser requests go through Next rewrite proxy.
    return "/backend";
  }
  if (process.env.RAILWAY_PRIVATE_DOMAIN) {
    return `http://${process.env.RAILWAY_PRIVATE_DOMAIN}`;
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getBase()}${path}`, {
    cache: "no-store",
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}
