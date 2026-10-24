# OpsLab: AI-Powered Operations Management Simulator

A classroom simulator for MBA Operations Management / Operations Analytics, delivered as **one self-contained HTML file** (`opslab.html`). It needs no install, login, backend or API key. Open it in a browser; it also works offline.

**Documentation:** [`docs/OpsLab_Documentation.pdf`](docs/OpsLab_Documentation.pdf) covers the problem, solution, topics, formulas, agent workflow, technologies, usage and the instructor guide.

## Topics (one scenario each)
| # | Topic | Your decisions | Objective |
|---|-------|----------------|-----------|
| 1 | Bottleneck & Capacity | machines per station | max shift profit |
| 2 | Inventory Management | reorder point, order quantity | min holding + ordering + stockout cost |
| 3 | Production Scheduling | dispatching rule / custom sequence | min late penalty |
| 4 | Quality Management | inspection coverage, prevention spend | min cost of quality |
| 5 | Queue Management | number of servers | min cost, meeting a service-level target |
| 6 | Supply Chain Disruption | dual-sourcing share, buffer stock, contingency plan | min disruption cost |

Each topic has adjustable inputs with working defaults, **Run / Run again**, **Reset topic**, KPI cards, a chart, a before/after table, a decision history, and a concept and formulas panel.

## AI Operations Agent
A **rule-based, deterministic** agent (no LLM; labelled in the UI). After every run it tracks your decisions, diagnoses inefficiencies, tests alternatives with the same engine (heuristics plus exhaustive or grid search), ranks them, recommends the best one and explains the trade-offs. It never interrupts: detailed advice appears only when you press **Get AI advice**. The **Session report** lists decisions, mistakes, improvements and lessons, and can be printed or saved as PDF.

### Optional live AI agent (chat), with any LLM provider
The **Ask the AI agent** box lets students ask for suggestions in plain language. Under *Live LLM settings*, pick a provider, a model and a key:

| Provider | API format | Direct from browser? |
|---|---|---|
| Anthropic Claude (default `claude-opus-5-5`) | Claude Messages API | yes |
| **NVIDIA NIM** (build.nvidia.com, e.g. `nvidia/nemotron-3.5-super-vl-120b-a12b`) | OpenAI-compatible | no, use the local proxy (below) |
| OpenAI, Groq, OpenRouter, Google Gemini | OpenAI-compatible | usually yes; use the proxy if the browser is blocked |
| Ollama (local, free, no key) | OpenAI-compatible | yes, start with `OLLAMA_ORIGINS="*" ollama serve` |
| Any other OpenAI-compatible endpoint (vLLM, self-hosted NIM, Together, Mistral…) | OpenAI-compatible | set the base URL |

Model names change often (providers retire models). Click **Load models** to fetch the provider's current list, then pick one, or type any model id.

The agent runs a tool-calling loop over four tools that call the real simulation engine:

| Tool | What it does |
|---|---|
| `get_current_state` | inputs, latest run KPIs, diagnosis, rule-based best option |
| `run_simulation` | sandbox what-if on the real engine (never changes the student's inputs) |
| `optimize` | rule-based grid/exhaustive search, optionally under a changed scenario |
| `propose_settings` | shows an *Apply suggested settings* button; the student decides |

The agent is told to quote only numbers returned by these tools. If a model can't do tool calling, OpsLab detects this and switches that chat to *grounded mode*: it sends the pre-computed simulator data with the question and has the model explain it. Without any LLM connected, the rule-based agent answers, so the basic demo needs no paid API.

**Local proxy (only for providers that block browser calls, such as NVIDIA):**
```
node tools/llm-proxy.mjs        # Node 18+, no install; listens on http://localhost:8787
```
Then tick *Use local proxy* in Live LLM settings. The proxy listens on localhost only and forwards only to an allowlist of provider hosts (add more with `EXTRA_HOSTS=host`).

Keys stay in the browser (or go through your own local proxy) and are sent only to the chosen provider. They are saved only if you tick *Remember keys*.

## Classroom use (75 min)
1. Set the role and explain decisions (blue) vs scenario inputs.
2. Work through 3–4 topics: predict the best decision → run the defaults → change one decision → run again → open Get AI advice.
3. Stress-test by changing a scenario input.
4. Debrief with the Session report.

See the in-app **Instructor guide** for learning objectives and discussion prompts.

## Rebuilding the PDF
`python3 docs/build_pdf.py` (needs `reportlab`).
