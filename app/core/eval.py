from __future__ import annotations

import json
from typing import Dict, Any

import typer


cli = typer.Typer(add_completion=False)


def compute_custom_metrics(output: Dict[str, Any], gold: Dict[str, Any]) -> Dict[str, float]:
    gold_fields = gold.get("fields", [])
    citations = output.get("citations", [])
    coverage = (len(citations) / max(1, len(gold_fields))) * 100.0

    correct = 0
    total = 0
    for k, v in gold.items():
        if k in ("fields", "expected_citations"):
            continue
        total += 1
        if output.get(k) == v:
            correct += 1
    accuracy = (correct / max(1, total)) * 100.0
    return {"citation_coverage": coverage, "extraction_accuracy": accuracy}


@cli.command()
def run_eval(query: str, gold_file: str = "data/test_jurisdictions.json"):
    try:
        from .research_agent import build_agent
    except Exception:
        raise typer.Abort()
    agent = build_agent()
    if agent is None:
        typer.echo("Deep research agent unavailable; install extras 'deep'.")
        raise typer.Abort()

    result = agent.invoke({"query": query})  # type: ignore[operator]

    try:
        from ragas import evaluate  # type: ignore
        from ragas.metrics import faithfulness, answer_relevancy  # type: ignore
        from datasets import Dataset  # type: ignore
    except Exception:
        # RAGAS unavailable; compute only custom metrics
        ragas_scores = {}
    else:
        ds = Dataset.from_dict({
            "question": [query],
            "answer": [result.get("output", "")],
            "contexts": [[d.get("text", "") for d in result.get("docs", [])]],
        })
        ragas_scores = evaluate(ds, metrics=[faithfulness, answer_relevancy]).to_dict()  # type: ignore[attr-defined]

    with open(gold_file, "r", encoding="utf-8") as f:
        gold_data = json.load(f)
    gold = gold_data.get(query, {}) if isinstance(gold_data, dict) else {}
    custom = compute_custom_metrics(result, gold)
    report = {**ragas_scores, **custom}
    with open("eval_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    typer.echo(json.dumps(report))


if __name__ == "__main__":
    cli()


