FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /workspace/
RUN pip install -U pip && pip install -e .

COPY app /workspace/app
COPY research_inputs /workspace/research_inputs

CMD ["bash", "-lc", "pytest -q"]
