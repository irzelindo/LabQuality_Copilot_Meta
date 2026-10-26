"use client";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Activity, ArrowRight, Bell, BookOpen, Boxes, ClipboardCheck, FileInput, FlaskConical, LayoutDashboard, ListTodo, LogOut, Menu, Network, Search, Settings, ShieldCheck, Sparkles, Users, X } from "lucide-react";
import { api, post } from "@/lib/api";
import type { Instrument, Lab, Notification, SystemStatus, User } from "@/lib/types";
import { AppContext, ErrorBox, Field, Status, useApp, useT } from "./ui";
import DashboardView from "./views/dashboard";
import AssessmentsView from "./views/assessments";
import ActionsView from "./views/actions";
import DocumentsView from "./views/documents";
import RegistersView from "./views/registers";
import AIView from "./views/ai-view";
import { AdminView, ImportView, InstrumentsView, LabsView, SystemView } from "./views/admin";

const navigation = [
  { key: "dashboard", pt: "Visão geral", en: "Overview", icon: LayoutDashboard, section: 0 },
  { key: "assessments", pt: "Avaliações", en: "Assessments", icon: ClipboardCheck, section: 0 },
  { key: "actions", pt: "Planos de melhoria", en: "Improvement plans", icon: ListTodo, section: 0 },
  { key: "ai", pt: "Copiloto de qualidade", en: "Quality copilot", icon: Sparkles, section: 0 },
  { key: "documents", pt: "Documentos", en: "Documents", icon: BookOpen, section: 1 },
  { key: "registers", pt: "Registos operacionais", en: "Operational registers", icon: Boxes, section: 1 },
  { key: "imports", pt: "Importar dados", en: "Import data", icon: FileInput, section: 1 },
  { key: "instruments", pt: "Instrumentos", en: "Instruments", icon: Activity, section: 1 },
  { key: "laboratories", pt: "Laboratórios", en: "Laboratories", icon: Network, section: 2 },
  { key: "users", pt: "Equipa e acessos", en: "Team & access", icon: Users, section: 2 },
  { key: "audit", pt: "Auditoria", en: "Audit trail", icon: ShieldCheck, section: 2 },
  { key: "system", pt: "Configuração", en: "Settings", icon: Settings, section: 2 }
];

export default function Workspace() {
  const [user, setUser] = useState<User | null>(null), [checking, setChecking] = useState(true), [locale, setLocale] = useState<"pt" | "en">("pt");
  const [view, setView] = useState("dashboard"), [labs, setLabs] = useState<Lab[]>([]), [users, setUsers] = useState<User[]>([]), [instruments, setInstruments] = useState<Instrument[]>([]), [system, setSystem] = useState<SystemStatus | null>(null);
  const [lab, setLab] = useState(""), [start, setStart] = useState(""), [end, setEnd] = useState(""), [nonce, setNonce] = useState(0), [message, setMessage] = useState("");
  const refresh = useCallback(() => setNonce(n => n + 1), []);
  useEffect(() => {
    const saved = localStorage.getItem("lq-locale"); if (saved === "en") setLocale("en");
    const readView = () => setView(new URLSearchParams(window.location.search).get("view") || "dashboard"); readView();
    window.addEventListener("popstate", readView);
    const expire = () => { setUser(null); setLabs([]); setUsers([]); setInstruments([]); };
    window.addEventListener("lq-session-expired", expire);
    api<User>("/auth/me").then(setUser).catch(() => {}).finally(() => setChecking(false));
    return () => { window.removeEventListener("popstate", readView); window.removeEventListener("lq-session-expired", expire); };
  }, []);
  useEffect(() => { document.documentElement.lang = locale === "pt" ? "pt-MZ" : "en"; localStorage.setItem("lq-locale", locale); }, [locale]);
  useEffect(() => { if (!message) return; const timer = setTimeout(() => setMessage(""), 6000); return () => clearTimeout(timer); }, [message]);
  useEffect(() => {
    if (!user) return;
    let live = true;
    Promise.allSettled([api<Lab[]>("/laboratories"), api<SystemStatus>("/system/status"), user.role !== "partner" ? api<User[]>("/users") : Promise.resolve([]), user.role !== "partner" ? api<Instrument[]>("/instruments") : Promise.resolve([])]).then(results => {
      if (!live) return;
      const [ls, sy, us, ins] = results;
      if (ls.status === "fulfilled") { setLabs(ls.value); if (lab && !ls.value.some(l => l.id === lab)) setLab(""); }
      if (sy.status === "fulfilled") setSystem(sy.value);
      if (us.status === "fulfilled") setUsers(us.value);
      if (ins.status === "fulfilled") setInstruments(ins.value);
      const failed = results.find(r => r.status === "rejected"); if (failed?.status === "rejected") setMessage(failed.reason.message);
    });
    return () => { live = false; };
  }, [user, nonce]); // lab is validated whenever the workspace data reloads.
  const navigate = (key: string) => { setView(key); const url = new URL(window.location.href); url.searchParams.set("view", key); window.history.pushState({}, "", url); };
  if (checking) return <div className="boot"><FlaskConical size={34} /><span>LabQuality Copilot</span><span className="boot-line" /></div>;
  if (!user) return <LoginView locale={locale} setLocale={setLocale} onLogin={u => { setUser(u); setLab(""); setView("dashboard"); }} />;
  return <AppContext.Provider value={{ user, labs, users, instruments, system, locale, lab, start, end, refresh, navigate, toast: setMessage }}><Shell view={view} navigate={navigate} setLab={setLab} setStart={setStart} setEnd={setEnd} setLocale={setLocale} logout={async () => { await post("/auth/logout", {}); setUser(null); }} nonce={nonce} />{message && <div className="toast" role="status">{message}<button aria-label="Close" onClick={() => setMessage("")}><X size={16} /></button></div>}</AppContext.Provider>;
}

function LoginView({ locale, setLocale, onLogin }: { locale: "pt" | "en"; setLocale: (v: "pt" | "en") => void; onLogin: (u: User) => void }) {
  const [email, setEmail] = useState(""), [password, setPassword] = useState(""), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const t = (pt: string, en: string) => locale === "pt" ? pt : en;
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { onLogin(await post<User>("/auth/login", { email, password })); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  return <main className="login-page"><section className="login-story"><a className="brand" href="/"><span className="brand-mark"><FlaskConical size={24} /></span><span>LabQuality<span className="brand-sub">COPILOT</span></span></a><div className="login-copy"><span className="eyebrow light">{t("QUALIDADE EM CADA ETAPA", "QUALITY AT EVERY STEP")}</span><h1>{t("Da avaliação\nà melhoria.", "From assessment\nto improvement.")}</h1><p>{t("Transforme achados em acções. Reúna evidências. Acompanhe o progresso da sua rede laboratorial.", "Turn findings into action. Gather evidence. Track progress across your laboratory network.")}</p><div className="login-loop">{[t("Avaliar", "Assess"), t("Agir", "Act"), t("Verificar", "Verify")].map((s, i) => <span key={s}><b>0{i + 1}</b>{s}{i < 2 && <ArrowRight size={15} />}</span>)}</div></div><div className="login-footer"><ShieldCheck size={17} />{t("Acesso por instituição · Decisões com revisão humana", "Institutional access · Human-reviewed decisions")}</div></section><section className="login-form-area"><button className="locale-switch" onClick={() => setLocale(locale === "pt" ? "en" : "pt")}>PT <span>/</span> EN</button><form className="login-form" onSubmit={submit}><span className="eyebrow">{t("O SEU ESPAÇO DE QUALIDADE", "YOUR QUALITY WORKSPACE")}</span><h2>{t("Bem-vindo de volta.", "Welcome back.")}</h2><p>{t("Entre com a conta atribuída pela sua instituição.", "Sign in with your institutional account.")}</p><label className="field"><span>Email</span><input type="email" autoComplete="username" placeholder="nome@instituicao.org" required value={email} onChange={e => setEmail(e.target.value)} /></label><label className="field"><span>{t("Palavra-passe", "Password")}</span><input type="password" minLength={1} maxLength={200} autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>{error && <div className="error-box" role="alert">{error}</div>}<button className="button primary login-submit" disabled={busy}>{busy ? t("A entrar…", "Signing in…") : t("Entrar no espaço de trabalho", "Sign in to workspace")}<ArrowRight size={18} /></button><div className="login-hint">{t("Demonstração local: consulte o README e a palavra-passe gerada na instalação.", "Local demonstration: see the README and the password generated during setup.")}</div></form><small className="login-legal">LabQuality Copilot · {t("Plataforma em desenvolvimento", "Platform in development")}</small></section></main>;
}

function Shell({ view, navigate, setLab, setStart, setEnd, setLocale, logout, nonce }: { view: string; navigate: (v: string) => void; setLab: (v: string) => void; setStart: (v: string) => void; setEnd: (v: string) => void; setLocale: (v: "pt" | "en") => void; logout: () => Promise<void>; nonce: number }) {
  const app = useApp(), t = useT(), [mobile, setMobile] = useState(false), [notifications, setNotifications] = useState<Notification[]>([]), [bell, setBell] = useState(false);
  useEffect(() => { api<Notification[]>("/notifications").then(setNotifications).catch(() => {}); }, [nonce]);
  const items = navigation.filter(n => app.user.role === "partner" ? ["dashboard", "system"].includes(n.key) : n.key === "users" ? app.user.role === "admin" : n.key === "audit" ? ["admin", "manager", "verifier"].includes(app.user.role) : true);
  const current = items.find(n => n.key === view) || items[0];
  function content() { switch (current.key) { case "assessments": return <AssessmentsView />; case "actions": return <ActionsView />; case "documents": return <DocumentsView />; case "registers": return <RegistersView />; case "ai": return <AIView />; case "imports": return <ImportView />; case "instruments": return <InstrumentsView />; case "laboratories": return <LabsView />; case "users": return <AdminView mode="users" />; case "audit": return <AdminView mode="audit" />; case "system": return <SystemView />; default: return <DashboardView />; } }
  return <div className="app-layout">{mobile && <button className="mobile-overlay" onClick={() => setMobile(false)} aria-label="Close menu" />}<aside className={"sidebar " + (mobile ? "open" : "")}><a href="?view=dashboard" onClick={e => { e.preventDefault(); navigate("dashboard"); }} className="brand"><span className="brand-mark"><FlaskConical size={23} /></span><span>LabQuality<span className="brand-sub">COPILOT</span></span></a><div className="workspace-chip"><span className="workspace-avatar">LQ</span><div><b>{t("Gestão da qualidade", "Quality management")}</b><small>{t("Espaço institucional", "Institutional workspace")}</small></div><span className="online-dot" /></div><nav aria-label={t("Navegação principal", "Main navigation")}>{[0, 1, 2].map(section => <div className="nav-group" key={section}><p>{[t("ACOMPANHAMENTO", "MONITORING"), t("OPERAÇÕES", "OPERATIONS"), t("ORGANIZAÇÃO", "ORGANIZATION")][section]}</p>{items.filter(n => n.section === section).map(n => <a key={n.key} href={"?view=" + n.key} className={current.key === n.key ? "active" : ""} aria-current={current.key === n.key ? "page" : undefined} onClick={e => { if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); navigate(n.key); setMobile(false); } }}><n.icon size={18} />{t(n.pt, n.en)}{n.key === "ai" && <span className="nav-ai">AI</span>}</a>)}</div>)}</nav><div className="sidebar-foot"><ShieldCheck size={18} /><p>{t("Cada melhoria começa com uma acção.", "Every improvement starts with an action.")}</p><small>LabQuality · v{app.system?.version || "0.1.0"}</small></div></aside><div className="main-column"><header className="topbar"><button className="icon-button mobile-menu" aria-label="Menu" onClick={() => setMobile(true)}><Menu size={22} /></button><div className="breadcrumb"><span>{t("Espaço de trabalho", "Workspace")}</span><span>/</span><b>{t(current.pt, current.en)}</b></div><div className="topbar-tools"><button className="locale-switch" onClick={() => setLocale(app.locale === "pt" ? "en" : "pt")}>{app.locale.toUpperCase()}</button><div className="notification-anchor"><button className="icon-button" aria-label={t("Notificações", "Notifications")} aria-expanded={bell} onClick={() => setBell(!bell)}><Bell size={20} />{notifications.some(n => !n.read) && <i className="notification-dot" />}</button>{bell && <div className="notification-panel"><h3>{t("Notificações", "Notifications")}</h3>{notifications.length === 0 && <p>{t("Sem notificações.", "No notifications.")}</p>}{notifications.map(n => <button key={n.id} className={n.read ? "notification-item" : "notification-item unread"} onClick={async () => { try { await post(`/notifications/${n.id}/read`, {}); setNotifications(items => items.map(i => i.id === n.id ? { ...i, read: true } : i)); } catch (e) { app.toast((e as Error).message); } }}><b>{n.title}</b><span>{n.message}</span></button>)}</div>}</div><div className="user-chip"><span className="user-avatar">{app.user.name.split(" ").slice(0, 2).map(s => s[0]).join("")}</span><div><b>{app.user.name}</b><small><Status value={app.user.role} /></small></div></div><button className="icon-button" aria-label={t("Terminar sessão", "Sign out")} onClick={() => logout().catch(e => app.toast(e.message))}><LogOut size={18} /></button></div></header><main className="main-content"><div className="page-heading"><div><span className="eyebrow">LABQUALITY WORKSPACE</span><h1>{t(current.pt, current.en)}</h1><p>{current.key === "dashboard" ? t("Uma visão clara do progresso. Um próximo passo para cada achado.", "A clear view of progress. A next step for every finding.") : t("Dados partilhados com a equipa e acessos definidos por laboratório.", "Shared team records with laboratory-level access.")}</p></div>{["dashboard", "assessments", "actions", "registers"].includes(current.key) && <div className="lab-filter"><label htmlFor="global-lab">{t("LABORATÓRIO", "LABORATORY")}</label><select id="global-lab" value={app.lab} onChange={e => setLab(e.target.value)}><option value="">{t("Todos os laboratórios", "All laboratories")}</option>{app.labs.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select></div>}</div>{["dashboard", "assessments"].includes(current.key) && <div className="date-filter"><span>{t("Período de avaliação", "Assessment period")}</span><label>{t("De", "From")}<input aria-label={t("Data inicial", "Start date")} type="date" value={app.start} onChange={e => setStart(e.target.value)} /></label><label>{t("Até", "To")}<input aria-label={t("Data final", "End date")} type="date" value={app.end} onChange={e => setEnd(e.target.value)} /></label>{(app.start || app.end) && <button className="text-button" onClick={() => { setStart(""); setEnd(""); }}>{t("Limpar", "Clear")}</button>}</div>}<div key={current.key} className="view-enter">{content()}</div><footer className="page-footer"><span>LabQuality Copilot</span><span>{t("DEMO-QMS: instrumento fictício · Sem classificação oficial SLIPTA", "DEMO-QMS: fictional instrument · No official SLIPTA classification")}</span></footer></main></div></div>;
}
