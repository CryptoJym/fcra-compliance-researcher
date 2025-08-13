## Evaluation Specification (RAGAS + Custom Metrics)

### Purpose
Introduce evaluation pipeline to quantify improvements in faithfulness, relevancy, citation coverage, and extraction accuracy.

### Scope
- Add `app/core/eval.py` CLI and test data under `data/test_jurisdictions.json`.
- Integrate with research pipeline to generate outputs for evaluation.

### Metrics
- RAGAS: faithfulness, answer relevancy.
- Custom: citation coverage (% fields with refs), extraction accuracy vs. gold.

### Testing Criteria
- Run CLI against sample data; produce `eval_report.json` with expected keys.


