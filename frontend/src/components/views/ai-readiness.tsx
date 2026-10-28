"use client";
import { ArrowRight, BookOpenCheck, Sparkles } from "lucide-react";
import type { AIReadiness } from "@/lib/types";
import { ErrorBox, useApp, useData, useT } from "../ui";

export default function AIReadinessPanel({ assessmentId }: { assessmentId: string }) {
  const app = useApp(), t = useT(), state = useData<AIReadiness>("/ai/readiness/" + assessmentId);
  const readiness = state.data;
  if (state.error) return <ErrorBox message={state.error} retry={state.reload} />;
  if (!readiness) return null;
  if (readiness.ready) return <div className="notice"><Sparkles size={17} /><span>{t(`${readiness.applicable_findings_count} achados com fontes publicadas aplicáveis. Reveja os comentários antes de enviar à Meta.`, `${readiness.applicable_findings_count} findings with applicable published sources. Review comments before sending them to Meta.`)}</span></div>;
  const message = readiness.findings_count === 0
    ? t("Esta avaliação não tem achados. Escolha uma avaliação com pontuações abaixo do máximo.", "This assessment has no findings. Choose one with scores below the maximum.")
    : readiness.published_sources_count === 0
      ? t("Há achados, mas nenhum documento publicado está acessível a este laboratório.", "There are findings, but no published document is accessible to this laboratory.")
      : t("Os documentos publicados não cobrem os critérios destes achados.", "Published documents do not cover the criteria of these findings.");
  return <div className="notice warning"><BookOpenCheck size={20} /><div><b>{t("A análise Meta ainda não tem fontes suficientes", "Meta analysis needs applicable sources")}</b><p>{message}{readiness.uncovered_criteria.length > 0 && ` ${t("Critérios sem fonte", "Criteria without a source")}: ${readiness.uncovered_criteria.join(", ")}.`}</p></div>{readiness.findings_count > 0 && <button type="button" className="text-button" onClick={() => app.navigate("documents")}>{t("Ver documentos", "View documents")}<ArrowRight size={15} /></button>}</div>;
}
