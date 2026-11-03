"""Derive a limited pilot catalogue and ODK field map from the supplied XLSForm.

Only short item headings, weights and field paths are stored; the questionnaire
itself stays outside the public repository. Run with the workbook as argument.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import openpyxl

SECTIONS = ["Documentos e registos", "Organização e liderança", "Gestão de pessoal",
            "Foco no cliente", "Gestão de equipamentos", "Avaliação", "Fornecedores e inventário",
            "Gestão dos processos", "Gestão da informação", "Eventos não conformes",
            "Melhoria contínua", "Instalações e segurança"]
PATTERN = re.compile(r"p2_s(\d+)_\1_(\d+)_calculate$")
TITLE_CORRECTIONS = {
    "1.6": "Acessibilidade dos documentos de qualidade",
    "7.3": "Sistema de inventário e orçamentação",
    # The supplied 8.18 heading repeats the referral-laboratory title, while
    # its question and subitems concern daily environmental monitoring.
    "8.18": "Monitorização diária das condições ambientais",
    "8.25": "Procedimento para incerteza de medição",
    "12.2": "Instalações e condições ambientais",
}


def build(path: Path):
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = iter(book["survey"].iter_rows(values_only=True))
    header = next(rows)
    stack, catalogue, row_data, paths = [], [], [], {}
    for cells in rows:
        row = dict(zip(header, cells))
        name, kind = str(row.get("name") or ""), str(row.get("type") or "").replace(" ", "_")
        if kind == "begin_group":
            stack.append(name)
        paths[name] = ".".join([*stack, name]) if name else ""
        row_data.append(row)
        match = PATTERN.fullmatch(name)
        if match:
            section, question = map(int, match.groups())
            code = f"{section}.{question}"
            prefix = f"p2_s{section}_{section}_{question}"
            heading = next((r.get("label") for r in row_data[-100:] if
                            r.get("type") in ("note", "select_one answers") and
                            re.search(r"\*\*\s*" + re.escape(code) + r"\s+", str(r.get("label") or ""))), None)
            label = re.sub(r"<[^>]*>", "", str(heading or ""))
            title = re.search(r"\*\*\s*" + re.escape(code) + r"\s+([^*\n]+)", label)
            if not title:
                raise ValueError(f"Falta o título do item {code}")
            title = TITLE_CORRECTIONS.get(code, " ".join(title.group(1).strip().split())[:130])
            calculation = str(row.get("calculation") or "")
            maximum = max(map(int, re.findall(r",\s*([0-3])\s*[,)]", calculation)))
            selection_names = sorted(set(re.findall(r"selected\(\$\{([^}]+)\},\s*'na'", calculation)))
            # For direct questions the final calculation does not reference NA.
            if not selection_names:
                selection_names = [prefix]
            catalogue.append({"code": code, "section": f"{section:02d} {SECTIONS[section-1]}",
                              "title": f"{code} {title}", "maximum": maximum, "critical": False,
                              "odk": {"score": paths[name], "na": selection_names,
                                      "comment": [], "prefix": prefix}})
        if kind == "end_group" and stack:
            stack.pop()
    for item in catalogue:
        item["odk"]["na"] = [paths[name] for name in item["odk"]["na"]]
        prefix = item["odk"].pop("prefix")
        item["odk"]["comment"] = [paths[str(r["name"])] for r in row_data
            if r.get("type") == "text" and "coment" in str(r.get("name") or "").lower()
            and (str(r["name"]).startswith(prefix + "_") or
                 (item["code"] == "3.3" and r["name"] == "p2_p2_s3_3_3_comentarios"))]
    if len(catalogue) != 151 or sum(c["maximum"] for c in catalogue) != 365:
        raise ValueError("O formulário não corresponde ao piloto verificado (151 itens/365 pontos).")
    return {"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "instrument_code": "SLIPTA-ODK-PILOT", "instrument_version": "2026.10",
            "form_id": "slipta_v3_2023_mozambique", "criteria": catalogue,
            "identity_field": "__id", "revision_field": "__system.updatedAt",
            "laboratory_code_field": "tt_pp_01.tf_numero_laboratorio",
            "assessment_date_field": "tt_pp_01.data_group.df_data_auditoria_actual"}


if __name__ == "__main__":
    result = build(Path(sys.argv[1]))
    target = Path(__file__).resolve().parents[1] / "backend" / "app" / "slipta_pilot.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['criteria'])} itens, {sum(x['maximum'] for x in result['criteria'])} pontos: {target}")
