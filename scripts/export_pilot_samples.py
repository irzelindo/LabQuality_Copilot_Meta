"""Export the nine deterministic, clearly simulated pilot cases as JSON and CSV."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.demo import pilot_assessments  # noqa: E402

records = [record.model_dump(mode="json") for record in pilot_assessments()]
(ROOT / "backend/samples/slipta-pilot-assessments.json").write_text(
    json.dumps({"assessments": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with (ROOT / "frontend/public/demo/slipta-pilot-assessments.csv").open("w", newline="", encoding="utf-8-sig") as out:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["source", "external_id", "source_revision", "laboratory_code", "instrument_code",
                     "instrument_version", "assessment_date", "criterion_code", "value", "comment"])
    for record in records:
        for code, answer in record["answers"].items():
            writer.writerow([record[key] for key in ("source", "external_id", "source_revision", "laboratory_code",
                            "instrument_code", "instrument_version", "assessment_date")] +
                            [code, answer["value"], answer["comment"]])
