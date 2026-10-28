#!/usr/bin/env bash
# Rebuild everything: tests -> data -> model runs -> scores -> tables, figures, PDF, slides.
# Model calls are cached in results/cache/, so with the cache present this
# reproduces every number in about a minute without calling a model.
#   bash run_all.sh                 # local model only (free)
#   WITH_GPT=1 bash run_all.sh      # also the gpt-5.4-mini comparison (needs OPENAI_API_KEY in .env)
set -euo pipefail
PY=${PY:-.venv/bin/python}
Q="--provider ollama --model qwen2.5:3b"
G="--provider openai --model gpt-5.4-mini --workers 4"
$PY -m pytest -q tests
$PY src/prepare_data.py
$PY src/run.py --experiment stop_instruction   $Q --n 60
$PY src/run.py --experiment baseline           $Q
$PY src/run.py --experiment list_position      $Q
$PY src/run.py --experiment list_position_noex $Q
$PY src/run.py --experiment example_leak       $Q
if [[ "${WITH_GPT:-0}" == "1" ]]; then
  $PY src/run.py --experiment stop_instruction $G --n 50
  $PY src/run.py --experiment list_position    $G --n 60
  $PY src/run.py --experiment allergy_leak     $G --n 20
fi
$PY src/rescore.py
for m in qwen2.5:3b gpt-5.4-mini; do
  for e in stop_instruction list_position list_position_noex allergy_leak; do
    [[ -f "results/$e/$m.jsonl" ]] && $PY src/analyze.py --model "$m" --experiment "$e"
  done
done
$PY src/probe_report.py --model qwen2.5:3b
$PY src/leak_report.py --model qwen2.5:3b
$PY src/fig_failure1.py
$PY src/workflow_figure.py
$PY src/build_pdf.py
$PY src/build_slides.py
