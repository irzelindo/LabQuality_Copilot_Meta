"use client";
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { AlertCircle, ArrowRight, LoaderCircle, SearchX, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Instrument, Lab, Role, SystemStatus, User } from "@/lib/types";

export interface AppContextValue { user: User; labs: Lab[]; users: User[]; instruments: Instrument[]; system: SystemStatus | null; locale: "pt" | "en"; lab: string; start: string; end: string; refresh: () => void; navigate: (view: string) => void; toast: (message: string) => void }
export const AppContext = createContext<AppContextValue | null>(null);
export function useApp() { const ctx = useContext(AppContext); if (!ctx) throw new Error("App context missing"); return ctx; }
export function useT() { const { locale } = useApp(); return (pt: string, en: string) => locale === "pt" ? pt : en; }
export const editors: Role[] = ["admin", "manager", "quality", "assessor"];
export const approvers: Role[] = ["admin", "manager", "verifier"];
export function can(user: User, roles: Role[]) { return roles.includes(user.role); }
export function useData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState(""), [nonce, setNonce] = useState(0);
  useEffect(() => {
    if (!path) { setData(null); setLoading(false); return; }
    const controller = new AbortController(); let alive = true;
    setLoading(true); setError("");
    api<T>(path, { signal: controller.signal }).then(result => { if (alive) setData(result); }).catch(err => { if (alive && err.name !== "AbortError") setError(err.message); }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; controller.abort(); };
  }, [path, nonce]);
  return { data, loading, error, reload: () => setNonce(n => n + 1) };
}
export function useMutation() {
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function run(work: () => Promise<unknown>, done?: () => void) { setBusy(true); setError(""); try { await work(); done?.(); } catch (err) { setError(err instanceof Error ? err.message : "Erro inesperado."); } finally { setBusy(false); } }
  return { busy, error, run };
}
export function Loading() { const t = useT(); return <div className="loading-state" role="status"><LoaderCircle size={20} className="spin" />{t("A carregar…", "Loading…")}</div>; }
export function ErrorBox({ message, retry }: { message: string; retry?: () => void }) { const t = useT(); if (!message) return null; return <div className="error-box" role="alert"><AlertCircle size={18} /><span>{message}</span>{retry && <button className="text-button" onClick={retry}>{t("Tentar novamente", "Retry")}</button>}</div>; }
export function Empty({ title, text, action }: { title: string; text: string; action?: ReactNode }) { return <div className="empty-state"><SearchX size={32} /><h3>{title}</h3><p>{text}</p>{action}</div>; }
export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) { return <section className={"panel " + className}>{children}</section>; }
export function PanelTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) { return <div className="panel-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>; }
export function Submit({ busy, children }: { busy: boolean; children: ReactNode }) { return <button type="submit" className="button primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <ArrowRight size={16} />}{children}</button>; }
export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) { return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>; }
export function Modal({ title, children, close, wide = false }: { title: string; children: ReactNode; close: () => void; wide?: boolean }) {
  const root = useRef<HTMLDivElement>(null), closeRef = useRef(close); closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow; document.body.style.overflow = "hidden";
    const focusable = () => Array.from(root.current?.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]') || []).filter(el => el.offsetParent !== null);
    const timer = setTimeout(() => focusable()[0]?.focus(), 0);
    const listener = (event: KeyboardEvent) => { if (event.key === "Escape") closeRef.current(); if (event.key === "Tab") { const list = focusable(); if (!list.length) { event.preventDefault(); return; } if (event.shiftKey && document.activeElement === list[0]) { event.preventDefault(); list.at(-1)?.focus(); } else if (!event.shiftKey && document.activeElement === list.at(-1)) { event.preventDefault(); list[0].focus(); } } };
    document.addEventListener("keydown", listener);
    return () => { clearTimeout(timer); document.body.style.overflow = overflow; document.removeEventListener("keydown", listener); previous?.focus(); };
  }, []);
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) close(); }}><div ref={root} role="dialog" aria-modal="true" aria-labelledby="dialog-title" className={"modal " + (wide ? "wide" : "")}><div className="modal-heading"><h2 id="dialog-title">{title}</h2><button aria-label="Close / Fechar" onClick={close} className="icon-button"><X size={20} /></button></div><div className="modal-body">{children}</div></div></div>;
}
const labels: Record<string, [string, string]> = {
  proposed: ["Proposta", "Proposed"], approved: ["Aprovada", "Approved"], in_progress: ["Em execução", "In progress"], in_verification: ["Em verificação", "In verification"], closed: ["Encerrada", "Closed"], reopened: ["Reaberta", "Reopened"], review: ["Em revisão", "In review"], finalized: ["Finalizada", "Finalized"], draft: ["Rascunho", "Draft"], published: ["Publicada", "Published"], withdrawn: ["Retirada", "Withdrawn"], open: ["Aberto", "Open"], high: ["Alta", "High"], critical: ["Crítica", "Critical"], medium: ["Média", "Medium"], low: ["Baixa", "Low"], queued: ["Na fila", "Queued"], running: ["Em análise", "Running"], completed: ["Concluída", "Completed"], failed: ["Falhou", "Failed"], sources_changed: ["Fontes alteradas", "Sources changed"], effective: ["Eficaz", "Effective"], ineffective: ["Não eficaz", "Ineffective"], admin: ["Administrador", "Administrator"], coordinator: ["Coordenação", "Coordinator"], manager: ["Gestor", "Manager"], quality: ["Qualidade", "Quality officer"], assessor: ["Avaliador", "Assessor"], verifier: ["Verificador", "Verifier"], partner: ["Parceiro", "Partner"]
};
export function Status({ value }: { value: string }) { const t = useT(); return <span className={"badge " + value}>{labels[value] ? t(...labels[value]) : value}</span>; }
export function fmtPercent(n: number | null | undefined) { return n == null ? "—" : new Intl.NumberFormat("pt-MZ", { maximumFractionDigits: 1 }).format(n) + "%"; }
export function fmtDate(value: string | null | undefined) { if (!value) return "—"; return new Intl.DateTimeFormat("pt-MZ", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value.slice(0, 10) + "T12:00:00")); }
export function OwnerOptions({ labId }: { labId: string }) { const { users } = useApp(); return <>{users.filter(u => u.active && !["partner", "coordinator"].includes(u.role) && (u.role === "admin" || u.laboratory_ids.includes(labId))).map(u => <option key={u.id} value={u.id}>{u.name}</option>)}</>; }
