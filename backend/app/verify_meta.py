"""Check local settings. --probe explicitly sends a small non-laboratory request to Meta."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import httpx
from .config import settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = settings()
    receipt = {"checked_at": datetime.now(timezone.utc).isoformat(), "model": cfg.model_id,
               "key_configured": bool(cfg.model_api_key), "live_probe": "not_run",
               "grounded_analysis": "not_validated"}
    if args.probe and cfg.model_api_key:
        try:
            response = httpx.post(cfg.model_base_url.rstrip("/") + "/responses",
                headers={"Authorization": "Bearer " + cfg.model_api_key}, timeout=45,
                json={"model": cfg.model_id, "input": "Reply with the single word READY.", "max_output_tokens": 64})
            receipt["http_status"] = response.status_code
            response.raise_for_status()
            data = response.json()
            texts = [part.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
                     for part in item.get("content", []) if part.get("type") == "output_text"]
            receipt["live_probe"] = "passed" if any(t.strip() for t in texts) and data.get("status", "completed") == "completed" else "failed"
            receipt["usage"] = data.get("usage", {})
            receipt["provider_response_id"] = data.get("id", "")
        except (httpx.HTTPError, ValueError):
            receipt["live_probe"] = "failed"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    raise SystemExit(0 if receipt["live_probe"] == "passed" else 2)


if __name__ == "__main__":
    main()
