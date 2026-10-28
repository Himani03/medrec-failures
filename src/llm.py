"""Call a language model, with a disk cache and automatic retries.

Supported providers:
  gemini     Google Gemini API      (env: GEMINI_API_KEY)
  openai     OpenAI API             (env: OPENAI_API_KEY)
  anthropic  Anthropic API          (env: ANTHROPIC_API_KEY)
  ollama     local Ollama server    (env: OLLAMA_BASE_URL, optional)
  mock       offline fake model, ONLY for testing the pipeline without a key

Every response is cached in results/cache/, keyed by (provider, model,
settings, prompt). Rerunning never pays twice, and an interrupted run resumes
where it stopped.
"""
import hashlib
import json
import os
import random
import re
import threading
import time

import requests
from openai import APIConnectionError, APIStatusError

from config import CACHE_DIR, ROOT, TEMPERATURE, fname

TIMEOUT_SECONDS = 600
MAX_RETRIES = 6


def load_env_file():
    """Read KEY=value lines from a .env file in the repo root (if present)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


load_env_file()


# ------------------------------------------------------------- providers --

def _gemini(model, prompt, thinking_budget):
    from openai import OpenAI

    if thinking_budget is not None:
        raise ValueError("The Gemini OpenAI-compatible route does not use --thinking-budget.")
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ["GEMINI_API_KEY"],
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""


def _openai(model, prompt, thinking_budget):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={"model": model, "temperature": TEMPERATURE,
              "response_format": {"type": "json_object"},
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _anthropic(model, prompt, thinking_budget):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"},
        json={"model": model, "max_tokens": 2048, "temperature": TEMPERATURE,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])


def _ollama(model, prompt, thinking_budget):
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    r = requests.post(
        f"{base_url}/api/chat",
        json={"model": model, "stream": False, "format": "json",
              # Ollama's default context is 4096 tokens and silently cuts longer
              # prompts, which would hide part of the note. 8192 fits every note.
              "options": {"temperature": TEMPERATURE, "num_ctx": 8192, "num_predict": 2048},
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _mock(model, prompt, thinking_budget):
    """Fake model for testing the code path. NOT a real result.
    It lists dosed drugs from the note and 'misses' stop instructions in the
    plan some of the time, so the analysis has something to show."""
    from drugs import ALIAS, canonical, find_alias
    note = prompt.split("<<<", 1)[1]
    seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    if prompt.startswith("Read the clinical note"):  # direct stop probe
        stopped = re.search(r"\b(Discontinue|Stop taking|Hold|D/C)\b", note)
        return json.dumps({"answer": "no" if stopped else "yes", "evidence": ""})

    meds = {}
    for alias, generic in ALIAS.items():
        for m in find_alias(alias, note):
            dose = re.search(r"\d+(\.\d+)?\s*mg", note[m.end(): m.end() + 30])
            if dose and generic not in meds:
                meds[generic] = {"name": note[m.start(): m.end()], "dose": dose.group(0), "frequency": ""}
    for line in note.splitlines():
        drug = canonical(line)
        if drug in meds and re.search(r"\b(Discontinue|Stop taking|Hold)\b", line) and rng.random() < 0.6:
            meds.pop(drug)
    return json.dumps({"medications": list(meds.values())})


PROVIDERS = {"gemini": _gemini, "openai": _openai, "anthropic": _anthropic,
             "ollama": _ollama, "mock": _mock}


# ------------------------------------------------------- cache + retries --

def _cache_path(provider, model, thinking_budget):
    tag = f"{provider}__{fname(model)}" + ("" if thinking_budget is None else f"__think{thinking_budget}")
    return CACHE_DIR / f"{tag}.jsonl"


def _load_cache(path):
    cache = {}
    if path.exists():
        for line in path.open():
            row = json.loads(line)
            cache[row["key"]] = row["response"]
    return cache


_CACHES = {}
_LOCK = threading.Lock()  # several worker threads may write the cache


def call_model(prompt, provider, model, thinking_budget=None, min_interval=0.0):
    """Return the model's text response for a prompt (cached)."""
    path = _cache_path(provider, model, thinking_budget)
    cache = _CACHES.setdefault(path, _load_cache(path))
    key = hashlib.sha256(prompt.encode()).hexdigest()
    if key in cache:
        return cache[key]

    for attempt in range(MAX_RETRIES):
        try:
            response = PROVIDERS[provider](model, prompt, thinking_budget)
            break
        except APIStatusError as err:
            status = err.status_code
            if status in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES - 1:
                wait = min(60, 5 * 2 ** attempt)
                print(f"    HTTP {status}, retrying in {wait}s ...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"{provider} API error {status}") from err
        except APIConnectionError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(5)
        except requests.HTTPError as err:
            status = err.response.status_code
            if status in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES - 1:
                wait = min(60, 5 * 2 ** attempt)
                print(f"    HTTP {status}, retrying in {wait}s ...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"{provider} API error {status}: {err.response.text[:300]}")
        except requests.RequestException:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(5)

    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps({"key": key, "response": response}) + "\n")
        cache[key] = response
    if min_interval:
        time.sleep(min_interval)  # stay under free-tier requests-per-minute
    return response
