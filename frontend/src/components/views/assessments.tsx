"use client";
import { useMemo, useState, type FormEvent } from "react";
import { ArrowRight, Check, ClipboardCheck, Download, Eye, FilePenLine, Plus, Search, Sparkles } from "lucide-react";
import { post, query } from "@/lib/api";
import { assessmentOrigin } from "@/lib/assessment-origin";
import type { Assessment, Finding, Instrument } from "@/lib/types";
import { Empty, ErrorBox, Field, Loading, Modal, Panel, PanelTitle, Status, Submit, approvers, can, editors, fmtDate, fmtPercent, useApp, useData, useMutation, useT } from "../ui";
import { ActionForm } from "./actions";
import AIReadinessPanel from "./ai-readiness";

export default function AssessmentsView() {
  const app = useApp(), t = useT(), [search, setSearch] = useState(""), [selected, setSelected] = useState<string | null>(null), [creating, setCreating] = useState(false), [editing, setEditing] = useState<Assessment | null>(null), [finding, setFinding] = useState<Finding | null>(null);
  const [origin, setOrigin] = useState<"all" | "odk" | "demo">("all");
  const params = query({ laboratory_id: app.lab, start: app.start, end: app.end, origin });
  const state = useData<{ items: Assessment[]; total: number }>("/assessments" + params);
  const rows = state.data?.items.filter(a => `${a.laboratory_name} ${a.external_id} ${a.instrument_name}`.toLowerCase().includes(search.toLowerCase())) || [];
  const complete = rows.filter(a => a.score.complete && a.score.percentage != null).length;
  const pending = rows.length - complete;
  const sources = [
    { value: "all", label: t("Todas", "All") },
    { value: "odk", label: t("Submissões ODK", "ODK submissions") },
    { value: "demo", label: t("Simulações", "Simulations") },
  ] as const;
  function done() { setCreating(false); setEditing(null); setFinding(null); state.reload(); app.refresh(); }
  return <>
    <Panel>
      <PanelTitle
        title={t("Histórico de avaliações", "Assessment history")}
        subtitle={t("Cada data representa um momento distinto de auditoria. É apresentada a revisão actual de cada avaliação.", "Each date represents a separate audit. The current revision of each assessment is shown.")}
        action={<div className="button-row"><a href={"/api/v1/reports/assessments.csv" + params} className="button secondary small"><Download size={15} />CSV</a>{can(app.user, editors) && <button className="button primary small" disabled={!app.instruments.length || !app.labs.length} onClick={() => setCreating(true)}><Plus size={16} />{t("Nova avaliação", "New assessment")}</button>}</div>}
      />
      <div className="assessment-filters">
        <div className="assessment-source-filter">
          <span className="assessment-filter-label">{t("Origem dos dados", "Data source")}</span>
          <div className="assessment-source-options" aria-label={t("Origem dos dados", "Data source")}>
            {sources.map(source => <button key={source.value} type="button" aria-pressed={origin === source.value} onClick={() => setOrigin(source.value)}>{source.label}</button>)}
          </div>
        </div>
        <label className="search-box assessment-search"><Search size={17} /><input aria-label={t("Pesquisar avaliações", "Search assessments")} placeholder={t("Laboratório, referência ou instrumento…", "Laboratory, reference or instrument…")} value={search} onChange={e => setSearch(e.target.value)} /></label>
      </div>
      {!state.loading && !state.error && state.data && <div className="assessment-overview" aria-label={t("Resumo das avaliações apresentadas", "Summary of displayed assessments")}>
        <div><span>{t("À vista", "On screen")}</span><strong>{rows.length}</strong><small>{search ? t(`de ${state.data.total} no filtro`, `of ${state.data.total} in this filter`) : t("avaliações", "assessments")}</small></div>
        <div><span>{t("Concluídas", "Complete")}</span><strong>{complete}</strong><small>{t("com percentagem final", "with a final percentage")}</small></div>
        <div><span>{t("Por concluir", "Incomplete")}</span><strong>{pending}</strong><small>{t("pontos ainda provisórios", "points still provisional")}</small></div>
      </div>}
      <p className="assessment-context">{origin === "odk" ? t("Submissões importadas do ODK; as datas são avaliações distintas, mesmo para o mesmo laboratório.", "Imported ODK submissions; different dates are separate assessments, even for the same laboratory.") : origin === "demo" ? t("Dados simulados para demonstração; não representam auditorias reais.", "Simulated demonstration data; these are not real audits.") : t("Resultados incompletos mostram pontos provisórios e cobertura, sem percentagem final.", "Incomplete results show provisional points and coverage, without a final percentage.")}</p>
      <ErrorBox message={state.error} retry={state.reload} />
      {state.loading ? <Loading /> : rows.length ? <div className="table-scroll assessment-table"><table>
        <thead><tr><th>{t("AVALIAÇÃO", "ASSESSMENT")}</th><th>{t("DATA", "DATE")}</th><th>{t("INSTRUMENTO", "INSTRUMENT")}</th><th>{t("PONTUAÇÃO E COBERTURA", "SCORE AND COVERAGE")}</th><th>{t("ESTADO", "STATUS")}</th><th><span className="sr-only">{t("Acções", "Actions")}</span></th></tr></thead>
        <tbody>{rows.map(a => <tr key={a.id}>
          <td><div className="assessment-identity"><span className="assessment-identity-icon" aria-hidden="true"><ClipboardCheck size={18} /></span><div><b>{a.laboratory_name}</b><small><span className={a.source.startsWith("odk:") ? "assessment-origin-tag odk" : "assessment-origin-tag"}>{assessmentOrigin(a.source, app.locale)}</span><span>{t("Revisão", "Revision")} {a.revision}</span></small><span className="assessment-reference" title={a.external_id}>{a.external_id}</span></div></div></td>
          <td className="assessment-date">{fmtDate(a.assessment_date)}</td>
          <td><b>{a.instrument_code}</b><small>v{a.instrument_version}</small></td>
          <td><div className="assessment-result"><strong className={a.score.complete ? "score-text" : "assessment-provisional"}>{a.score.complete && a.score.percentage != null ? fmtPercent(a.score.percentage) : t("Por concluir", "Incomplete")}</strong><span>{a.score.obtained}/{a.score.maximum} {t(a.score.complete ? "pontos" : "pontos provisórios", a.score.complete ? "points" : "provisional points")}</span><progress value={Math.max(0, Math.min(100, a.score.coverage))} max="100" aria-label={t("Cobertura", "Coverage")} /><small>{a.score.coverage}% {t("preenchido", "coverage")}</small></div></td>
          <td><Status value={a.status} /></td>
          <td><button className="button secondary small" onClick={() => setSelected(a.id)}><Eye size={15} />{t("Abrir", "Open")}</button></td>
        </tr>)}</tbody>
      </table></div> : <Empty title={t("Sem avaliações para apresentar", "No assessments to display")} text={t("Ajuste os filtros ou importe os dados dos seus laboratórios.", "Adjust filters or import your laboratory data.")} />}
    </Panel>
    {selected && <AssessmentDetail id={selected} close={() => setSelected(null)} changed={state.reload} edit={a => { setSelected(null); setEditing(a); }} createAction={f => { setSelected(null); setFinding(f); }} selectRevision={setSelected} />}
    {(creating || editing) && <AssessmentForm previous={editing} close={() => { setCreating(false); setEditing(null); }} done={done} />}
    {finding && <ActionForm finding={finding} close={() => setFinding(null)} done={done} />}
  </>;
}

function AssessmentDetail({ id, close, changed, edit, createAction, selectRevision }: { id: string; close: () => void; changed: () => void; edit: (a: Assessment) => void; createAction: (f: Finding) => void; selectRevision: (id: string) => void }) {
  const app = useApp(), t = useT(), state = useData<Assessment>("/assessments/" + id), mutation = useMutation();
  const a = state.data;
  const unanswered = a?.criteria.filter(c => {
    const answer = a.answers[c.code];
    return !answer?.not_applicable && (answer?.value === null || answer?.value === undefined);
  }) || [];
  return <Modal title={t("Detalhes da avaliação", "Assessment details")} close={close} wide>{state.loading ? <Loading /> : state.error ? <ErrorBox message={state.error} retry={state.reload} /> : a && <>
    <div className="detail-summary"><div><h3>{a.laboratory_name}</h3><p>{fmtDate(a.assessment_date)} · {a.instrument_code} v{a.instrument_version}</p><Status value={a.status} /><span className="badge">{assessmentOrigin(a.source, app.locale)}</span>{!a.current && <span className="badge withdrawn">{t("Revisão anterior", "Previous revision")}</span>}</div><div className="big-score">{fmtPercent(a.score.percentage)}<small>{a.score.obtained}/{a.score.maximum} {t(a.score.complete ? "pontos" : "pontos provisórios", a.score.complete ? "points" : "provisional points")}</small></div></div>
    <div className="button-row wrap">{a.current && can(app.user, approvers) && a.status === "review" && <button className="button primary small" disabled={mutation.busy || !a.score.complete} title={!a.score.complete ? t("Responda a todos os critérios aplicáveis antes de finalizar.", "Answer all applicable criteria before finalizing.") : undefined} onClick={() => mutation.run(() => post(`/assessments/${a.id}/finalize`, { version: a.version }), () => { state.reload(); changed(); })}><Check size={15} />{t("Finalizar avaliação", "Finalize assessment")}</button>}{a.current && can(app.user, editors) && <button className="button secondary small" onClick={() => edit(a)}><FilePenLine size={15} />{t("Criar correcção", "Create correction")}</button>}{a.current && can(app.user, [...editors, "verifier"]) && <button className="button secondary small" onClick={() => { sessionStorage.setItem("lq-ai-assessment", a.id); close(); app.navigate("ai"); }}><Sparkles size={15} />{t("Analisar com Meta", "Analyze with Meta")}</button>}</div>
    <ErrorBox message={mutation.error} />
    {!a.score.complete && <div className="notice warning" role="status"><div><b>{t("Avaliação por concluir", "Assessment not yet complete")}</b><p>{unanswered.length ? t(`${unanswered.length} critério(s) por avaliar: ${unanswered.map(c => c.code).join(", ")}. ${a.source.startsWith("odk:") ? "Corrija a resposta na origem ODK e sincronize novamente, ou crie uma correcção fundamentada." : "Crie uma correcção fundamentada para completar as respostas."} Não atribua pontos sem evidência.`, `${unanswered.length} unanswered criterion/criteria: ${unanswered.map(c => c.code).join(", ")}. ${a.source.startsWith("odk:") ? "Correct the answer in ODK and sync again, or create a justified correction." : "Create a justified correction to complete the answers."} Do not assign points without evidence.`) : t("Não há pontos aplicáveis para calcular a percentagem. Reveja as respostas NA e as respectivas justificações.", "There are no applicable points for a percentage. Review NA answers and their reasons.")}</p></div></div>}
    {a.current && can(app.user, [...editors, "verifier"]) && <AIReadinessPanel key={a.id} assessmentId={a.id} />}
    <p className="muted small-text">{t("Cobertura", "Coverage")}: {a.score.coverage}%. {a.score.not_applicable > 0 && `${a.score.not_applicable} NA · ${a.score.full_maximum - a.score.maximum} ${t("pontos excluídos do denominador", "points excluded from denominator")}. `}{!a.score.complete && t("Resultados incompletos não têm percentagem final.", "Incomplete results have no final percentage.")}</p>
    <div className="table-scroll detail-table"><table><thead><tr><th>{t("CRITÉRIO", "CRITERION")}</th><th>{t("PONTOS", "POINTS")}</th><th>{t("COMENTÁRIO", "COMMENT")}</th></tr></thead><tbody>{a.criteria.map(c => <tr key={c.code}><td><b>{c.code} {c.critical && <span className="tiny-critical">{t("CRÍTICO", "CRITICAL")}</span>}</b><p>{c.title}</p><small>{c.section}</small></td><td>{a.answers[c.code]?.not_applicable ? "NA" : `${a.answers[c.code]?.value ?? "—"} / ${c.maximum}`}</td><td>{a.answers[c.code]?.comment || "—"}</td></tr>)}</tbody></table></div>
    <h3 className="subheading">{t("Achados", "Findings")} ({a.findings.length})</h3>{a.findings.map(f => <div className="finding-row" key={f.id}><div><Status value={f.critical ? "critical" : "medium"} /><b>{f.criterion_code} · {f.title}</b></div>{can(app.user, editors) && <button className="button secondary small" onClick={() => createAction(f)}><Plus size={14} />{t("Criar acção", "Create action")}</button>}</div>)}
    <details className="disclosure"><summary>{t("Origem e revisões", "Source and revisions")}</summary><p>{a.source} · {a.external_id}</p><p>{a.reason}</p>{a.revisions.map(r => <button key={r.id} className="revision-button" disabled={r.id === a.id} onClick={() => selectRevision(r.id)}>{t("Revisão", "Revision")} {r.revision} · {r.reason}<ArrowRight size={15} /></button>)}</details>
  </>}</Modal>;
}

function AssessmentForm({ previous, close, done }: { previous: Assessment | null; close: () => void; done: () => void }) {
  const app = useApp(), t = useT(), mutation = useMutation();
  const [labId, setLabId] = useState(previous?.laboratory_id || app.lab || app.labs[0]?.id || ""), [instrumentId, setInstrumentId] = useState(previous?.instrument_id || app.instruments[0]?.id || "");
  const [assessmentDate, setAssessmentDate] = useState(previous?.assessment_date || new Date().toISOString().slice(0, 10)), [reason, setReason] = useState("");
  const [answers, setAnswers] = useState<Record<string, { value: number | null; comment: string; not_applicable?: boolean }>>(previous?.answers || {});
  const [externalId] = useState(previous?.external_id || crypto.randomUUID());
  const instrument = app.instruments.find(i => i.id === instrumentId);
  const sections = [...new Set(instrument?.criteria.map(c => c.section) || [])];
  async function submit(event: FormEvent) { event.preventDefault(); if (!instrument) return; const lab = app.labs.find(l => l.id === labId); if (!lab) return; await mutation.run(() => post("/imports/assessments", { assessments: [{ source: previous?.source || "manual", external_id: externalId, source_revision: String(Date.now()), laboratory_code: lab.code, instrument_code: instrument.code, instrument_version: instrument.version, assessment_date: assessmentDate, answers, reason }] }), done); }
  return <Modal title={previous ? t("Corrigir avaliação com nova revisão", "Correct assessment with a new revision") : t("Nova avaliação", "New assessment")} close={close} wide><form onSubmit={submit} className="stack-form"><div className="form-grid"><Field label={t("Laboratório", "Laboratory")}><select required disabled={!!previous} value={labId} onChange={e => setLabId(e.target.value)}>{app.labs.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}</select></Field><Field label={t("Instrumento", "Instrument")}><select required disabled={!!previous} value={instrumentId} onChange={e => { setInstrumentId(e.target.value); setAnswers({}); }}>{app.instruments.map(i => <option key={i.id} value={i.id}>{i.code} v{i.version}</option>)}</select></Field><Field label={t("Data da avaliação", "Assessment date")}><input required type="date" value={assessmentDate} onChange={e => setAssessmentDate(e.target.value)} /></Field></div>{previous && <Field label={t("Motivo da correcção", "Reason for correction")}><textarea required minLength={5} maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} /></Field>}{previous?.source.startsWith("odk:") && <div className="notice warning">{t("Esta avaliação veio do ODK. Prefira corrigir a submissão na origem e sincronizar novamente: uma importação posterior pode substituir uma correcção local.", "This assessment came from ODK. Prefer correcting the original submission and syncing again: a later import may supersede a local correction.")}</div>}<div className="notice">{t("Pode guardar respostas em falta. Num instrumento que permite NA, justifique cada NA; a percentagem usa apenas os pontos aplicáveis.", "Missing answers can be saved. For an instrument that permits NA, justify each NA; the percentage uses applicable points only.")}</div>{sections.map(section => <fieldset className="question-section" key={section}><legend>{section}</legend>{instrument?.criteria.filter(c => c.section === section).map(c => <div className="question" key={c.code}><div className="question-label"><b>{c.code}</b><p>{c.title}</p>{c.critical && <Status value="critical" />}</div><div className="question-controls"><Field label={t("Pontuação", "Score")}><select value={answers[c.code]?.not_applicable ? "NA" : answers[c.code]?.value ?? ""} onChange={e => setAnswers(prev => ({ ...prev, [c.code]: { comment: prev[c.code]?.comment || "", value: e.target.value === "" || e.target.value === "NA" ? null : Number(e.target.value), not_applicable: e.target.value === "NA" } }))}><option value="">{t("Por avaliar", "Not assessed")}</option>{Array.from({ length: c.maximum + 1 }, (_, i) => <option key={i} value={i}>{i} / {c.maximum}</option>)}{instrument?.scoring_rule === "sum_applicable_v1" && <option value="NA">NA · {t("Não aplicável", "Not applicable")}</option>}</select></Field><Field label={t("Comentário", "Comment")}><input maxLength={5000} required={answers[c.code]?.not_applicable ?? false} value={answers[c.code]?.comment || ""} onChange={e => setAnswers(prev => ({ ...prev, [c.code]: { value: prev[c.code]?.value ?? null, comment: e.target.value, not_applicable: prev[c.code]?.not_applicable ?? false } }))} /></Field></div></div>)}</fieldset>)}<ErrorBox message={mutation.error} /><div className="form-footer"><button type="button" className="button secondary" onClick={close}>{t("Cancelar", "Cancel")}</button><Submit busy={mutation.busy}>{t("Guardar avaliação", "Save assessment")}</Submit></div></form></Modal>;
}
