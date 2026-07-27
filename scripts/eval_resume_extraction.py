#!/usr/bin/env -S uv run python
"""Run live resume extraction evals against the configured LLM provider.

Usage:
    RUN_LIVE_LLM=1 uv run python scripts/eval_resume_extraction.py
    RUN_LIVE_LLM=1 uv run python scripts/eval_resume_extraction.py --case qwen_shape
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.services.resume_structurer import structure_resume
from tests.evals.eval_assertions import evaluate_extraction, load_json

FIXTURES_DIR = ROOT / "tests" / "evals" / "fixtures"


async def run_case(case_dir: Path) -> bool:
    case_name = case_dir.name
    resume_text = (case_dir / "resume.txt").read_text(encoding="utf-8").strip()
    expected = load_json(case_dir / "expected.json")

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            extraction = await structure_resume(db, resume_text)
    finally:
        await engine.dispose()

    failures = evaluate_extraction(extraction, expected, case_name=f"live:{case_name}")
    if failures:
        print(f"FAIL {case_name}")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print(f"PASS {case_name}")
    print(json.dumps(extraction.model_dump(), indent=2))
    return True


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run live resume extraction evals")
    parser.add_argument(
        "--case",
        help="Run a single fixture case directory name (default: all)",
    )
    args = parser.parse_args()

    if os.getenv("RUN_LIVE_LLM") != "1":
        print("Set RUN_LIVE_LLM=1 to run live LLM evals.", file=sys.stderr)
        return 2

    case_dirs = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
    if args.case:
        case_dirs = [FIXTURES_DIR / args.case]

    results = [await run_case(case_dir) for case_dir in case_dirs]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} cases passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
