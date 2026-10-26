export class ApiError extends Error { constructor(message: string, public status: number) { super(message); } }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("X-LabQuality-Client", "web");
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch("/api/v1" + path, { ...options, headers, credentials: "same-origin", cache: "no-store" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message = typeof data.detail === "string" ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: { loc: string[]; msg: string }) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ") : "Não foi possível concluir o pedido.";
    if (response.status === 401 && path !== "/auth/login") window.dispatchEvent(new Event("lq-session-expired"));
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}
export const post = <T>(path: string, body: unknown) => api<T>(path, { method: "POST", body: JSON.stringify(body) });
export const query = (values: Record<string, string>) => { const params = new URLSearchParams(Object.entries(values).filter(([, v]) => !!v)); return params.size ? "?" + params : ""; };
