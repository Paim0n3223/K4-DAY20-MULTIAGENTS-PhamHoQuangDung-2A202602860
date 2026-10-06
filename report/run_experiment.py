"""Bounded, sequential API runs; retain failed attempts without changing provided CLI."""
import argparse
import json
import logging
import shutil
import subprocess
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.rate_limiters import InMemoryRateLimiter
from lab.model import make_model
from lab.runner import CONDITIONS, run_task
from lab.tasks import ROOT, list_tasks


class Progress(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        print("  Model response received", flush=True)


def configured_model():
    model = make_model()
    model.timeout = 60
    model.max_retries = 0
    model.rate_limiter = InMemoryRateLimiter(requests_per_second=0.14,
                                            check_every_n_seconds=0.1, max_bucket_size=1)
    if type(model).__name__ == "ChatGoogleGenerativeAI":
        model.reasoning_effort = "low"
    model.callbacks = [Progress()]
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=CONDITIONS)
    parser.add_argument("--tasks", nargs="+", default=["learn"])
    parser.add_argument("--attempts", type=int, default=2)
    args = parser.parse_args()
    tasks = list_tasks(args.tasks[0]) if args.tasks in (["learn"], ["eval"]) else (
        list_tasks() if args.tasks == ["all"] else None)
    ids = [t.id for t in tasks] if tasks is not None else args.tasks
    if any(t.endswith("-eval") for t in ids):
        tagged = subprocess.run(["git", "rev-parse", "--verify", "refs/tags/freeze"],
                                cwd=ROOT, capture_output=True)
        if tagged.returncode:
            raise SystemExit("Refusing evaluation before freeze tag.")
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", message="Model.*uses fixed sampling defaults")
    for task in ids:
        directory = ROOT / "results" / args.condition / task
        path = directory / "run.json"
        if path.exists() and not json.loads(path.read_text(encoding="utf-8")).get("error"):
            print(f"Already completed: {args.condition}/{task}", flush=True)
            continue
        for attempt in range(args.attempts):
            if directory.exists() and any(directory.iterdir()):
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
                archive = ROOT / "results" / "api-attempts" / f"{args.condition}-{task}-{stamp}"
                archive.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(directory), str(archive))
            print(f"Starting {args.condition}/{task}, attempt {attempt + 1}", flush=True)
            record = run_task(task, args.condition, model=configured_model())
            print(f"Result {record['passed']}/{record['total']}; tokens={record['tokens']['total']}; "
                  f"seconds={record['seconds']}; error={record['error']}", flush=True)
            if not record["error"]:
                break
            if not any(code in record["error"] for code in ("429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                raise SystemExit(1)
            if attempt + 1 < args.attempts:
                time.sleep(30)
        else:
            raise SystemExit("API remains unavailable; resume later without rerunning completed tasks.")


if __name__ == "__main__":
    main()
