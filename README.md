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

### Optional live AI agent (chat)
The **Ask the AI agent** box lets students ask for suggestions in plain language. Paste a Claude API key under *Live LLM settings* (the default model is Claude Opus 5.5; Sonnet 5.5 and Haiku 5.5 are also offered). The browser then calls the Claude API directly and runs a tool-use loop with four tools:

| Tool | What it does |
|---|---|
| `get_current_state` | inputs, latest run KPIs, diagnosis, rule-based best option |
| `run_simulation` | sandbox what-if on the real engine (never changes the student's inputs) |
| `optimize` | rule-based grid/exhaustive search, optionally under a changed scenario |
| `propose_settings` | shows an *Apply suggested settings* button; the student decides |

The agent is told to quote only numbers returned by these tools. The key stays in the browser and goes only to `api.anthropic.com`; it is saved only if you tick *Remember*. Without a key, the rule-based agent answers, so the basic demo needs no paid API.

## Classroom use (75 min)
1. Set the role and explain decisions (blue) vs scenario inputs.
2. Work through 3–4 topics: predict the best decision → run the defaults → change one decision → run again → open Get AI advice.
3. Stress-test by changing a scenario input.
4. Debrief with the Session report.

See the in-app **Instructor guide** for learning objectives and discussion prompts.

## Rebuilding the PDF
`python3 docs/build_pdf.py` (needs `reportlab`).
