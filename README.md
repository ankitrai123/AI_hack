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
| 7 | Process Time Analytics | batch size, SMED, cellular layout, poka-yoke (time study sets assembly time) | min daily cost of lead time + lost output + improvements |

Each topic has adjustable inputs with working defaults, **Run / Run again**, **Reset topic**, KPI cards, a chart, a before/after table, a decision history, and a concept and formulas panel.

**Case data.** Every topic opens with a **Case data** section: a written brief plus numbered exhibits holding every number needed to solve the case, with **Download case data (CSV)** for Excel. Examples: process times and market data (bottleneck); supply and cost data plus **90 days of demand history** (inventory); the job table (scheduling); quality, cost and prevention-effectiveness data (quality); planning data and a **40-customer observation log** (queues); supplier, demand and disruption data (supply chain); the process route and a **10-cycle time-study sheet** (process time). The exhibits update with the scenario, including Scenario Agent cases and campaign rounds. The inventory case gives past demand from the same process rather than the future days, so students must estimate demand and its variability. The actual simulated demand is added as an exhibit after the run, for the debrief. In campaigns, outcomes hidden until the round is played (the supply disruption) stay hidden in the case data.

### Campaign mode (quarters or years)
Every topic can also be played as a **multi-round campaign**: quarterly (4 or 8 quarters) or yearly (3 or 5 years). Each round has a briefing with new conditions: growth, Q4 seasonal peaks, inflation, a new product launch, a lead-time shock, a recall, a new operator re-rated by time study, or a supplier shutdown that is revealed only after you commit your plan. Decisions carry over; scenario inputs are set by the round. Each round is played once, and its result is scaled to the period (e.g. profit per shift × 63 shifts per quarter or × 250 per year). The campaign total is compared with the AI's best plan for each round (with hindsight), shown as a round-by-round table, a chart, a final summary, and a section in the session report. In the class room, official campaign rounds count for the leaderboard.

| Topic | Value per round |
|---|---|
| Bottleneck | profit per shift × 63 (quarter) / 250 (year) |
| Inventory | cost per 90-day run × 1 / 4 |
| Scheduling | penalty per weekly schedule × 13 / 52 |
| Quality | cost of quality per weekly batch × 13 / 52 |
| Queues | cost per hour × 504 / 2,000 |
| Supply chain | cost per 60-day window × 1.5 / 6 |
| Process time | cost per day × 63 / 250 |

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

### Scenario Agent (one agent for every topic)
Each topic has a **Scenario Agent** panel. Type an optional brief (e.g. *"monsoon floods hit a pharma plant in Vizag"*) and click **Generate case with AI**. The agent writes a case (title, short story, new scenario values) using whichever LLM is connected. Every value is checked against the input's valid range, unknown inputs are dropped, and decision inputs can never be changed. In **Campaign** setup, choose *Rounds: written by the Scenario Agent* to get a whole campaign (briefing and conditions per round) built around your theme. For the supply-chain topic the disruption stays hidden until the round is played. Without an LLM, **Random case** makes rule-based variations. Generated cases count as practice in a class room.

### Ollama (free, local LLM)
Click **Use Ollama (free)** in the Scenario Agent panel, or **🦙 Use Ollama** in Live LLM settings. OpsLab selects the Ollama provider, finds your installed models and picks a good chat model. Setup: install from ollama.com, run `ollama pull llama3.1`, then `OLLAMA_ORIGINS="*" ollama serve`. When students open OpsLab from the class server, Ollama requests go through the server, so **one Ollama on the professor's laptop serves the whole class**; `OLLAMA_ORIGINS` isn't needed then.

### Optional class room (professor dashboard, roll numbers)
Run OpsLab as a class with one command on the professor's laptop (Node 18+, nothing to install):
```
node tools/opslab-server.mjs      # prints "Students open: http://<laptop-ip>:8787"
```
1. **Professor:** open the printed address → **Class room** → *Create room*. Optionally paste the class roll-number list so only listed students can join. Share the 6-character room code. Keep the professor key to reopen the dashboard on another device.
2. **Students:** open the same address (same Wi-Fi or hotspot) → **Class room** → enter the room code and roll number. Every run is then submitted automatically.
3. **Dashboard:** each student's best % of optimum per topic, a leaderboard (score out of 7, one point per topic), class averages (first run vs best run), the most common mistakes per topic, who hasn't joined, *Reset device*, *Close room*, and **CSV export** for grading. It refreshes every 10 s.

Fair play: the server **re-computes every run** from the student's decisions with the same engine, so results can't be faked. Only runs on the standard scenario count for the leaderboard (changed-scenario runs show as practice). Each roll number is tied to one device until the professor resets it. Runs made while the server is unreachable are queued and can be sent later. Data is saved in `opslab-rooms.json` with atomic writes and a `.bak` copy of the previous version, and is flushed when the server stops, so Ctrl+C never loses class data. The server also includes the LLM proxy, so NVIDIA works without running `llm-proxy.mjs` separately: set the proxy URL to the server address.

## Classroom use (75 min)
1. Set the role and explain decisions (blue) vs scenario inputs.
2. Work through 3–4 topics: predict the best decision → run the defaults → change one decision → run again → open Get AI advice.
3. Stress-test by changing a scenario input.
4. Debrief with the Session report.

See the in-app **Instructor guide** for learning objectives and discussion prompts.

## Rebuilding the PDF
`python3 docs/build_pdf.py` (needs `reportlab`).
