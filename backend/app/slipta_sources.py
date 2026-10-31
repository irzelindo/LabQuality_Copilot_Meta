"""Prepare a private, reviewable source pack from the user's original SLIPTA files."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
import openpyxl


def clean(text):
    text = re.sub(r"<[^>]+>", "", str(text or ""))
    return html.unescape(text).replace("**", "").replace("\u200b", "").strip()


def catalog(xlsform):
    workbook = openpyxl.load_workbook(xlsform, read_only=True, data_only=False)
    rows = list(workbook["survey"].values)
    headers = rows[0]
    rows = [dict(zip(headers, r)) for r in rows[1:] if r[1]]
    by_name = {r["name"]: r for r in rows}
    config = list(workbook["settings"].values)[1]
    sections = {int(r["name"].rsplit("s", 1)[1]): clean(r.get("label"))
                for r in rows if re.fullmatch(r"tt_pp_02_s\d+", r["name"])}
    items = []
    for row in rows:
        match = re.fullmatch(r"(p2_s(\d+)_(\d+)_(\d+))_calculate", row["name"])
        if not match:
            continue
        parent, section, major, minor = match.groups()
        question = next((r for r in rows if (r["name"] == parent or r["name"].startswith(parent + "_"))
                         and re.search(r"Pontua[çc][ãa]o total:\s*\d+", clean(r.get("label")), re.I)), None)
        question = question or by_name.get(parent)
        label = clean(question.get("label")) if question else ""
        points = re.search(r"Pontua[çc][ãa]o total:\s*(\d+)", label, re.I)
        weight_origin = "printed_label"
        if not points:
            points = re.search(r"if\(selected\(\$\{" + re.escape(parent) +
                               r"\},\s*'sim'\),\s*(\d+),", str(row.get("calculation") or ""))
            weight_origin = "explicit_yes_calculation"
        if not points:
            raise ValueError(f"Pontuação máxima explícita em falta: {parent}")
        children = [r for r in rows if r["name"].startswith(parent + "_") and
                    str(r.get("type")) == "select_one answers"]
        fragments = [label] + [clean(c.get("label")) for c in children]
        iso = by_name.get(parent + "_iso")
        if iso:
            fragments.append(clean(iso.get("label")))
        title = label.split("\n")[0]
        if len(title) > 1000:
            title = title[:997] + "..."
        items.append({"code": f"{major}.{minor}", "field": parent,
                      "score_field": row["name"], "answer_fields": [r["name"] for r in children] or [parent],
                      "maximum": int(points.group(1)), "weight_origin": weight_origin, "title": title,
                      "section": sections.get(int(section), f"Secção {section}"),
                      "content": "\n\n".join(fragments)})
    workbook.close()
    if not items:
        raise ValueError("O XLSForm não contém os critérios SLIPTA esperados.")
    return {"form_id": str(config[1]), "version": str(config[2]), "items": items,
            "maximum": sum(i["maximum"] for i in items)}


def prepare_pack(pdf, xlsform):
    from pypdf import PdfReader
    data = catalog(xlsform)
    pages = [page.extract_text() or "" for page in PdfReader(pdf).pages]
    # Anchor headings at line starts. A reference within a paragraph is not a heading.
    joined = "\n".join(pages)
    headings = list(re.finditer(r"(?m)^\s*(\d{1,2}\.\d{1,2})\s+[A-Z]", joined))
    excerpts = {}
    printed_weights = {}
    for n, heading in enumerate(headings):
        code = heading.group(1)
        start = heading.start()
        end = headings[n + 1].start() if n + 1 < len(headings) else min(len(joined), start + 8000)
        excerpts.setdefault(code, joined[start:end].strip()[:8000])
        score = re.search(r"Score\s*/\s*(\d+)", joined[start:end])
        if score:
            printed_weights.setdefault(code, int(score.group(1)))
    sources = []
    for item in data["items"]:
        matching_pages = [n + 1 for n, text in enumerate(pages)
                          if re.search(r"(?m)^\s*" + re.escape(item["code"]) + r"\s+[A-Z]", text)]
        locator = ", ".join(str(p) for p in matching_pages) or "consultar a checklist original"
        excerpt = excerpts.get(item["code"], "")
        mismatch = (printed_weights.get(item["code"]) is not None and
                    printed_weights[item["code"]] != item["maximum"])
        content = (
            f"REFERÊNCIA EXTERNA: SLIPTA Checklist Version 3:2023. Critério {item['code']}. "
            f"Página(s) do PDF: {locator}.\n"
            "A lista de verificação descreve requisitos e notas de orientação. "
            "Este documento não é um procedimento local nem comprova implementação.\n\n"
            f"Texto do formulário ODK português fornecido pelo utilizador:\n{item['content']}\n\n"
            + (f"Trecho da checklist original em inglês:\n{excerpt}\n\n" if excerpt else "")
            + (f"DIVERGÊNCIA A REVER: XLSForm {item['maximum']} pontos; PDF {printed_weights[item['code']]} pontos. Não harmonizar automaticamente.\n" if mismatch else "")
            + "Revisão necessária: conferir a tradução, aplicabilidade e correspondência com o original antes de publicar."
        )
        aliases = [item["code"], item["field"], item["score_field"], *item["answer_fields"]]
        sources.append({"code": "SLIPTA-V3-" + item["code"], "title": item["title"][:250],
                        "content": content, "criterion_codes": list(dict.fromkeys(aliases))})
    return {
        "pack_version": "slipta-sources-v1",
        "provenance": {"pdf_sha256": hashlib.sha256(Path(pdf).read_bytes()).hexdigest(),
                       "xlsform_sha256": hashlib.sha256(Path(xlsform).read_bytes()).hexdigest(),
                       "pdf_name": Path(pdf).name, "xlsform_name": Path(xlsform).name,
                       "form_id": data["form_id"], "form_version": data["version"],
                       "criterion_count": len(sources), "form_maximum": data["maximum"],
                       "pdf_printed_question_maximum": sum(printed_weights.values()),
                       "pdf_declared_maximum": max([int(n) for n in re.findall(r"(\d+)\s*pts", joined)] or [0]),
                       "weight_differences": [{"criterion": i["code"], "xlsform": i["maximum"],
                                               "pdf": printed_weights.get(i["code"])}
                                              for i in data["items"] if i["maximum"] != printed_weights.get(i["code"])],
                       "notice": "Piloto técnico. Diferenças entre pesos do formulário e totais impressos exigem revisão."},
        "documents": sources
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--xlsform", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    pack = prepare_pack(args.pdf, args.xlsform)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "provenance": pack["provenance"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
