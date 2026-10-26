import { NextRequest } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
type RouteContext = { params: Promise<{ path: string[] }> };
async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (path.some(p => p === "." || p === ".." || p.includes("\\") || p.includes("/"))) return Response.json({ detail: "Caminho inválido." }, { status: 400 });
  const target = new URL("/api/" + path.map(encodeURIComponent).join("/"), process.env.LQ_API_URL || "http://127.0.0.1:8000");
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["cookie", "content-type", "origin", "x-labquality-client"]) { const value = request.headers.get(name); if (value) headers.set(name, value); }
  let body: Uint8Array | undefined;
  if (!["GET", "HEAD"].includes(request.method) && request.body) {
    const reader = request.body.getReader(), chunks: Uint8Array[] = []; let total = 0;
    while (true) { const chunk = await reader.read(); if (chunk.done) break; total += chunk.value.byteLength; if (total > 12_000_000) { await reader.cancel(); return Response.json({ detail: "Pedido demasiado grande." }, { status: 413 }); } chunks.push(chunk.value); }
    body = new Uint8Array(total); let offset = 0; for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.length; }
  }
  try {
    const response = await fetch(target, { method: request.method, headers, body: body ? Buffer.from(body) : undefined, redirect: "manual", cache: "no-store", signal: AbortSignal.timeout(120000) });
    const output = new Headers({ "Cache-Control": "no-store" });
    for (const name of ["content-type", "content-disposition", "x-content-type-options"]) { const value = response.headers.get(name); if (value) output.set(name, value); }
    for (const cookie of response.headers.getSetCookie()) output.append("set-cookie", cookie);
    return new Response(response.body, { status: response.status, headers: output });
  } catch {
    return Response.json({ detail: "A API está indisponível. Confirme que o backend está em execução." }, { status: 503 });
  }
}
export { proxy as GET, proxy as POST, proxy as PATCH, proxy as PUT, proxy as DELETE, proxy as HEAD };
