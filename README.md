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

## Classroom use (75 min)
1. Set the role and explain decisions (blue) vs scenario inputs.
2. Work through 3–4 topics: predict the best decision → run the defaults → change one decision → run again → open Get AI advice.
3. Stress-test by changing a scenario input.
4. Debrief with the Session report.

See the in-app **Instructor guide** for learning objectives and discussion prompts.

## Rebuilding the PDF
`python3 docs/build_pdf.py` (needs `reportlab`).
