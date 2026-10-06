"""Record one real curator call and its usage; never edit generated skills."""
import json
import logging
import time
import warnings
from datetime import datetime, timezone

from langchain_core.callbacks import UsageMetadataCallbackHandler
from lab.curator import curate_skills
from lab.tasks import ROOT
from run_experiment import configured_model


def main():
    target = ROOT / "report" / "curator-run.json"
    if target.exists():
        raise SystemExit("Existing curator record: archive it explicitly before rerunning.")
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", message="Model.*uses fixed sampling defaults")
    usage = UsageMetadataCallbackHandler()
    model = configured_model()
    model.callbacks.append(usage)
    started = time.perf_counter()
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "error": None}
    try:
        paths = curate_skills(model=model)
        record["skills"] = [str(p.relative_to(ROOT)) for p in paths]
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["skills"] = []
    record["seconds"] = round(time.perf_counter() - started, 1)
    record["tokens"] = {short: sum(u.get(long, 0) for u in usage.usage_metadata.values())
                        for short, long in (("input", "input_tokens"),
                                            ("output", "output_tokens"), ("total", "total_tokens"))}
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)
    if record["error"] or not record["skills"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
