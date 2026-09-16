"""
run_eval_e4.py — Run the benchmark against V1 adapter + fixed parser (Experiment E4).

This evaluates the V1 LoRA adapter (35 trajectories) using the V2 two-pass parser.
It isolates the parser effect: same model, same benchmark, different parser.

Usage:
    python run_eval_e4.py
    python run_eval_e4.py --url https://your-ngrok-url.ngrok.io

Expected result: Varies. If parser was a major factor, E4 > V1 (18/23).
                 If parser was minor, E4 ≈ V1.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import asyncio
import json
import os
import time
from typing import Optional

from ft_agent import QwenRemoteClient
from eval.tasks import TASKS
from eval.harness import run_benchmark, TaskResult


def task_result_to_dict(result: TaskResult) -> dict:
    return {
        "task_id": result.task.id,
        "category": result.task.category,
        "success": result.success,
        "failure_reasons": result.failure_reasons,
        "steps_taken": result.trace.steps_taken,
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "is_error": tc.is_error,
                "result_preview": tc.result[:200] if len(tc.result) > 200 else tc.result,
            }
            for tc in result.trace.tool_calls
        ],
        "final_answer": result.trace.final_answer,
        "latency_seconds": result.trace.latency_seconds,
        "compute_latency_seconds": result.trace.compute_latency_seconds,
        "retry_wait_seconds": result.trace.retry_wait_seconds,
        "hit_max_steps": result.trace.hit_max_steps,
    }


def generate_markdown_report(results: list[TaskResult]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed

    lines = [
        "# E4 Benchmark Report: V1 Adapter + Fixed Parser",
        "",
        f"**Overall: {passed}/{total} passed ({100 * passed / total:.1f}%)**",
        "",
        "**Configuration:**",
        "- Model: Qwen2.5-7B-Instruct + LoRA v1 (35 trajectories)",
        "- Parser: V2 two-pass robust parser",
        "- Benchmark: 23-task held-out set",
        "- max_steps=3, greedy decoding",
        "",
        "| Task ID | Category | Result | Steps | Tool Calls | Latency (s) |",
        "|---|---|---|---|---|---|",
    ]

    for r in results:
        status = "PASS" if r.success else f"FAIL ({', '.join(r.failure_reasons)})"
        lines.append(
            f"| {r.task.id} | {r.task.category} | {status} | "
            f"{r.trace.steps_taken} | {len(r.trace.tool_calls)} | "
            f"{r.trace.latency_seconds:.2f} |"
        )

    lines.extend(["", "## Category Breakdown", ""])
    categories = sorted(set(r.task.category for r in results))
    for cat in categories:
        cat_results = [r for r in results if r.task.category == cat]
        cat_passed = sum(1 for r in cat_results if r.success)
        lines.append(f"- **{cat}**: {cat_passed}/{len(cat_results)} passed")

    if failed > 0:
        lines.extend(["", "## Failed Tasks", ""])
        for r in results:
            if not r.success:
                lines.append(f"- **{r.task.id}**: {', '.join(r.failure_reasons)}")

    return "\n".join(lines)


async def run_evaluation(
    colab_server_url: Optional[str] = None,
    max_steps: int = 3,
    verbose: bool = False,
    pace_delay: float = 1.0,
) -> list[TaskResult]:
    server_url = colab_server_url or os.environ.get("COLAB_SERVER_URL_E4")
    if not server_url:
        raise RuntimeError(
            "COLAB_SERVER_URL_E4 not set. Pass --url or set the environment variable."
        )

    print("=" * 60)
    print("E4 Benchmark: V1 Adapter + Fixed Parser")
    print(f"Server: {server_url}")
    print("=" * 60)

    agent = QwenRemoteClient(
        colab_server_url=server_url,
        mcp_server_script="mcp_server.py",
        max_steps=max_steps,
    )
    await agent.connect(verbose=True)

    try:
        results = await run_benchmark(
            agent, TASKS, verbose=verbose, pace_delay_seconds=pace_delay,
        )
    finally:
        await agent.close()

    return results


def save_json_results(results: list[TaskResult], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": "qwen2.5-7b-lora-v1-fixed-parser",
                "base_model": "Qwen2.5-7B-Instruct",
                "adapter": "agentlab_qwen_lora_7b",
                "parser": "v2_two_pass",
                "training_data": "training_data.jsonl",
                "training_trajectories": 35,
                "experiment": "E4",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tasks": len(results),
                "passed": sum(1 for r in results if r.success),
                "results": [task_result_to_dict(r) for r in results],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"JSON results saved to {filepath}")


async def main():
    parser = argparse.ArgumentParser(description="E4: V1 adapter + fixed parser benchmark")
    parser.add_argument("--url", dest="server_url", help="Colab server URL (or set COLAB_SERVER_URL_E4 env var)")
    parser.add_argument("--max-steps", type=int, default=3, help="Maximum tool-call steps (default: 3)")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--pace-delay", type=float, default=1.0, help="Delay between tasks")
    parser.add_argument("--json-output", default="results/eval_results_e4.json", help="Output JSON path")
    parser.add_argument("--md-output", default="results/eval_report_e4.md", help="Output markdown path")

    args = parser.parse_args()

    results = await run_evaluation(
        colab_server_url=args.server_url,
        max_steps=args.max_steps,
        verbose=args.verbose,
        pace_delay=args.pace_delay,
    )

    total = len(results)
    passed = sum(1 for r in results if r.success)
    print("\n" + "=" * 60)
    print("E4 BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"Total: {total} tasks")
    print(f"Passed: {passed} ({100 * passed / total:.1f}%)")
    print(f"Failed: {total - passed} ({100 * (total - passed) / total:.1f}%)")

    save_json_results(results, args.json_output)

    md_report = generate_markdown_report(results)
    with open(args.md_output, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Markdown report saved to {args.md_output}")

    print("\n--- Category Breakdown ---")
    categories = sorted(set(r.task.category for r in results))
    for cat in categories:
        cat_results = [r for r in results if r.task.category == cat]
        cat_passed = sum(1 for r in cat_results if r.success)
        print(f"  {cat:26s} {cat_passed}/{len(cat_results)} passed")

    if total - passed > 0:
        print("\n--- Failed Tasks ---")
        for r in results:
            if not r.success:
                print(f"  [{r.task.id}] {', '.join(r.failure_reasons)}")

    # Print comparison summary
    print("\n--- Comparison ---")
    print(f"  V1 (original parser):    18/23 = 78.3%")
    print(f"  E4 (fixed parser):       {passed}/{total} = {100 * passed / total:.1f}%")
    print(f"  Parser improvement:      +{passed - 18}/23 = +{100 * (passed - 18) / total:.1f} pp")
    print(f"  V2 (fixed parser + data): 23/23 = 100.0%")
    print(f"  Data improvement (E4→V2): +{23 - passed}/23 = +{100 * (23 - passed) / total:.1f} pp")


if __name__ == "__main__":
    asyncio.run(main())
