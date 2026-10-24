"""Builds docs/OpsLab_Documentation.pdf (run: python3 docs/build_pdf.py)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('Sans', D + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Sans-B', D + 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Mono', D + 'DejaVuSansMono.ttf'))
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans-B', italic='Sans', boldItalic='Sans-B')

HERE = os.path.dirname(os.path.abspath(__file__))
ACC = colors.HexColor('#4338ca'); INK = colors.HexColor('#141b2d'); MUTED = colors.HexColor('#5a6377'); LINE = colors.HexColor('#e2e6ee'); SOFT = colors.HexColor('#eef0ff')
st = {
    'title': ParagraphStyle('t', fontName='Sans-B', fontSize=24, leading=29, textColor=INK),
    'sub': ParagraphStyle('s', fontName='Sans', fontSize=12, leading=16, textColor=MUTED),
    'h1': ParagraphStyle('h1', fontName='Sans-B', fontSize=15, leading=19, textColor=ACC, spaceBefore=10, spaceAfter=5),
    'h2': ParagraphStyle('h2', fontName='Sans-B', fontSize=11.5, leading=15, textColor=INK, spaceBefore=7, spaceAfter=3),
    'p': ParagraphStyle('p', fontName='Sans', fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=4),
    'b': ParagraphStyle('b', fontName='Sans', fontSize=9.5, leading=13.5, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=1.5),
    'cell': ParagraphStyle('c', fontName='Sans', fontSize=8.3, leading=11, textColor=INK),
    'cellb': ParagraphStyle('cb', fontName='Sans-B', fontSize=8.3, leading=11, textColor=INK),
    'mono': ParagraphStyle('m', fontName='Mono', fontSize=8, leading=11, textColor=INK),
    'cap': ParagraphStyle('cap', fontName='Sans', fontSize=8, leading=10, textColor=MUTED, spaceAfter=6),
}
P = lambda t, s='p': Paragraph(t, st[s])
def bullets(items): return [Paragraph(i, st['b'], bulletText='•') for i in items]
def table(rows, widths, header=True, mono_cols=()):
    data = [[Paragraph(str(c), st['cellb'] if (header and r == 0) else (st['mono'] if j in mono_cols and r > 0 else st['cell'])) for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, LINE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), SOFT if header else colors.white), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    return t
def img(name, width):
    from PIL import Image as PI
    w, h = PI.open(os.path.join(HERE, 'img', name)).size
    return Image(os.path.join(HERE, 'img', name), width=width, height=width * h / w)

W = A4[0] - 36 * mm
s = []
s += [Spacer(1, 30 * mm), P('OpsLab', 'title'), P('AI-Powered Operations Management Simulator', 'sub'), Spacer(1, 4),
      P('Project documentation · MBA Operations Management / Operations Analytics', 'sub'), Spacer(1, 10 * mm)]
s += [img('overview.png', W), P('Inventory Management topic after a run, with the AI Operations Agent’s advice open (right).', 'cap')]
s += [Spacer(1, 4 * mm), table([
    ['Deliverable', 'File'],
    ['Interactive simulator (single self-contained page)', 'opslab.html'],
    ['This document', 'docs/OpsLab_Documentation.pdf'],
    ['Quick start and instructor notes', 'README.md']], [W * 0.6, W * 0.4])]
s.append(PageBreak())

s += [P('1. Problem', 'h1'),
      P('Operations concepts such as bottlenecks, safety stock, dispatching rules, cost of quality, queueing and supply-chain resilience are usually taught with static formulas and spreadsheet exercises. Students rarely get to <b>make a decision, see the consequences, and compare their choice with a better one</b> in the same session. Commercial simulation games are expensive, need accounts, and are hard to run live in a 75-minute class.'),
      P('2. Solution', 'h1'),
      P('OpsLab is a small virtual factory in one HTML file. The student acts as an operations manager: they set the decisions for each topic, press <b>Run simulation</b>, and get KPIs, a chart, a before/after comparison and a decision history. A <b>rule-based AI Operations Agent</b> monitors every run without interrupting. After each run it diagnoses inefficiencies, tests feasible alternatives with the same simulation engine, recommends the best one and explains the trade-offs. The <b>Session report</b> summarizes decisions, mistakes, improvements and lessons learned.'),
      P('Design principles', 'h2')]
s += bullets(['<b>Every number is computed.</b> All KPIs come from deterministic formulas or a seeded simulation. Nothing is hard-coded or made up.',
              '<b>Decisions vs scenario.</b> Inputs are split into decisions (blue, what the manager controls) and scenario parameters (the environment). The agent optimizes only decisions.',
              '<b>Fair comparisons.</b> Alternatives are evaluated on the same scenario and the same random demand stream (common random numbers).',
              '<b>No interruptions.</b> The agent reports after each run. Detailed advice appears only on request (<i>Get AI advice</i>).',
              '<b>Zero setup.</b> No login, backend, internet connection or paid API. Open the file in any modern browser.'])

s += [P('3. Topics, models and formulas', 'h1'),
      P('Each topic has adjustable inputs with sensible defaults, a Run / Run again button, a Reset button, 8 KPI cards, a chart (yours vs the AI recommendation), a before/after table and a decision history.')]
topics = [
 ('3.1 Bottleneck & Capacity', 'Three stations (Cutting 4 min, Assembly 7 min, Packing 5 min per unit), demand 100 units per 480-min shift. Decision: parallel machines per station (1–4). Objective: maximize shift profit.',
  [['Capacity', 'Cap_i = machines_i × shift ÷ time_i'], ['Throughput', 'TH = min(min Cap_i, Demand)'], ['Utilization', 'U_i = TH ÷ Cap_i'], ['Cycle time', 'CT = max(time_i ÷ machines_i)'], ['Line efficiency', 'Σ time_i ÷ (Σ machines_i × CT)'], ['Profit', 'TH × margin − Σ machines × machine cost']],
  'Default 1/1/1 earns $1,340 (Assembly is the bottleneck at 68 units). The agent finds 1/2/1: $1,920. Adding a Packing machine as well meets all demand but earns less ($1,900).'),
 ('3.2 Inventory Management', 'Continuous-review (ROP, Q) policy, simulated day by day for 90 days with normally distributed demand (mean 20, s.d. 6) from a seeded generator, 5-day lead time and lost sales. Decisions: reorder point and order quantity. Objective: minimize holding + ordering + stockout cost.',
  [['EOQ', '√(2DS ÷ H)'], ['Safety stock', 'z × σ_d × √L'], ['Reorder point', 'd̄ × L + SS'], ['Total cost', 'Σ H × on-hand + orders × S + short units × p'], ['Fill rate', 'units sold ÷ units demanded']],
  'Default ROP 80 / Q 100 costs $5,155 (fill rate 87.7%). The textbook policy (EOQ 219, ROP 122) costs $2,209. The agent’s grid search over 1,500+ policies finds ROP 104 / Q 270: $2,060.'),
 ('3.3 Production Scheduling', 'Six jobs on a single machine with editable processing times and due dates. Decision: rule (FCFS, SPT, EDD, CR, Slack, LPT) or a custom sequence. Objective: minimize late penalty ($/job-day), with average flow time as the tie-breaker.',
  [['Completion', 'C_j = Σ processing times up to job j'], ['Tardiness', 'T_j = max(0, C_j − d_j)'], ['Avg jobs in system', 'Σ F_j ÷ makespan'], ['Penalty', 'Σ T_j × penalty']],
  'FCFS: 4 late jobs, $22,000. EDD: $4,500. The agent enumerates all 720 sequences and finds F-B-D-A-E-C: $4,000. It also tests Moore–Hodgson (fewest late jobs).'),
 ('3.4 Quality Management', 'A 5,000-unit batch with a 6% base defect rate. Decisions: inspection coverage (%) and prevention spend. Prevention reduces defects exponentially toward a process floor. Objective: minimize total cost of quality (COQ).',
  [['Defect rate', 'p = p_min + (p₀ − p_min)·e^(−Prev/1000)'], ['Caught', 'N·p × coverage × detection'], ['Escaped', 'N·p − caught'], ['COQ', 'prevention + appraisal + rework + scrap + external failure'], ['Sigma level', 'z(1 − DPMO/10⁶) + 1.5']],
  'Default (100% inspection, no prevention) has a COQ of $10,220. The agent finds $3,500 of prevention with no inspection: $7,497. This illustrates “you cannot inspect quality in”.'),
 ('3.5 Queue Management', 'M/M/c service desk: 50 arrivals/hour, 4-minute mean service. Decision: number of servers. Objective: minimize wages + waiting cost, subject to a service-level target (80% of customers wait less than 2 min).',
  [['Utilization', 'ρ = λ ÷ (cμ)'], ['Erlang C', 'P_w = [aᶜ/c!·1/(1−ρ)] ÷ [Σ aᵏ/k! + aᶜ/c!·1/(1−ρ)]'], ['Queue', 'L_q = P_w·ρ/(1−ρ),  W_q = L_q/λ'], ['Service level', '1 − P_w·e^(−(cμ−λ)T)']],
  '4 servers: $252/h and only 53% served within 2 min. 5 servers: $176/h and 86%, which meets the target. Unstable choices (ρ ≥ 1) are flagged as infinite queues.'),
 ('3.6 Supply Chain Disruption', '60-day daily simulation with a base-stock policy. The primary supplier shuts down on days 10–24. Decisions: backup supplier share (dual sourcing), buffer stock (days), contingency plan on/off and response time. Objective: minimize backup premium + holding + lost margin.',
  [['Order-up-to', 'S = d × L_eff + SS'], ['Daily order', 'max(0, S − inventory position)'], ['Stuck orders', 'arrive at end of outage + L₁'], ['Emergency cap', 'β·d + spare backup capacity'], ['Cost', 'premium × backup units + holding + lost units × margin']],
  'Default (single source, 3-day buffer, no plan) costs $20,976 with 480 units lost. The agent tests 1,716 combinations and finds 10% dual sourcing, a 5-day buffer and a 1-day contingency switch: $5,524, 100% fill rate.'),
]
for name, desc, f, res in topics:
    s.append(KeepTogether([P(name, 'h2'), P(desc), table([['Quantity', 'Formula']] + f, [W * 0.28, W * 0.72], mono_cols=(1,)), Spacer(1, 3), P('<b>Default vs agent:</b> ' + res)]))

s += [P('4. AI Operations Agent workflow', 'h1'),
      P('The agent is a <b>deterministic, rule-based expert system</b> that runs in the browser and is labelled “Rule-based AI agent · no LLM” in the interface. No live LLM is used, so results are reproducible and never made up. After each run:')]
s += [table([['Step', 'What the agent does'],
    ['1. Track', 'Logs the run, the decisions changed since the previous run (scenario changes marked ⚑) and the movement of the main KPI.'],
    ['2. Diagnose', 'Applies operations rules, e.g. ROP below lead-time demand, utilization above 85%, external failure above 40% of COQ, a long job blocking an urgent one, no contingency plan. Some rules test the next-smaller option first, so the agent never flags a choice that is already optimal.'],
    ['3. Generate', 'Builds feasible alternatives: textbook heuristics (EOQ + 95% ROP, SPT/EDD/CR, Moore–Hodgson, staff-to-demand) plus an exhaustive or grid search over the decision space (30 to 1,700 options per topic).'],
    ['4. Evaluate', 'Runs every alternative through the same simulation engine and scenario.'],
    ['5. Compare', 'Ranks on the topic objective (profit, cost or penalty), respecting constraints such as the service-level target. Lists what the best option gains and what it gives up (cost, output, delays, service).'],
    ['6. Recommend', 'Shows the share of the best option achieved, the recommendation, a trade-off explanation and topic lessons. “Apply recommendation” copies its decisions into the inputs; the student still presses Run.'],
    ['7. Report', 'The Session report compiles, per topic: decisions made, mistakes found (with run numbers), improvements and setbacks, share of best achieved, and lessons learned. It can be printed or saved as PDF.']],
    [W * 0.16, W * 0.84])]
_side = Table([[img('agent.png', W * 0.36), [P('Agent panel', 'h2'), P('Right-hand panel after a Supply Chain run: score versus the best option found, decision tracking, diagnosis, and the recommendation with gains and give-ups. <i>Get AI advice</i> adds the ranked table of alternatives tested, the trade-off explanation and lessons.'),
      P('This panel needs no API key. The optional live LLM chat below the panel builds on the same engine and optimizer.'),
      Spacer(1, 6), img('quality.png', W * 0.58), P('Quality topic: cost-of-quality breakdown, your plan vs the AI recommendation.', 'cap')]]], colWidths=[W * 0.38, W * 0.62])
_side.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
s += [Spacer(1, 4), _side]
s += [P('Optional live AI agent (LLM chat)', 'h2'),
      P('The <b>Ask the AI agent</b> chat box adds a live LLM agent that works with many providers. It answers free-form questions such as “Should I add a machine at B?” or “What if demand rises 30%?” with a tool-calling loop of up to 8 steps. No backend is needed.'),
      table([['Provider', 'API format', 'Notes'],
             ['Anthropic Claude', 'Claude Messages API', 'Default claude-opus-5-5; direct from browser'],
             ['NVIDIA NIM (build.nvidia.com)', 'OpenAI-compatible', 'e.g. nvidia/nemotron-3.5-super-vl-120b-a12b; needs the local proxy (CORS)'],
             ['OpenAI, Groq, OpenRouter, Google Gemini', 'OpenAI-compatible', 'Usually direct; use the proxy if the browser is blocked'],
             ['Ollama (local)', 'OpenAI-compatible', 'Free, no key; start with OLLAMA_ORIGINS="*" ollama serve'],
             ['Any other endpoint', 'OpenAI-compatible', 'vLLM, self-hosted NIM, Together, Mistral…: set the base URL']], [W * 0.3, W * 0.22, W * 0.48]),
      Spacer(1, 3),
      table([['Tool', 'Purpose'],
             ['get_current_state', 'Inputs with ranges and roles, the latest run’s KPIs and diagnosis, and the rule-based best option.'],
             ['run_simulation', 'Sandbox what-if on the deterministic engine. It never changes the student’s inputs or history.'],
             ['optimize', 'Runs the rule-based optimizer, optionally under changed scenario inputs, to check robustness.'],
             ['propose_settings', 'Shows an “Apply suggested settings” button. The student decides whether to apply and run.']], [W * 0.25, W * 0.75], mono_cols=()),
      Spacer(1, 3),
      P('Guardrails: the system prompt requires that every number comes from a tool result; invalid inputs come back as tool errors; scenario-only and decision-only checks apply; it handles errors (bad key, wrong model, rate limit, blocked browser call). Models without tool calling are detected automatically and switched to grounded mode, where OpsLab sends the pre-computed simulator data with the question. Keys stay in the browser, or pass through the user’s own local proxy (tools/llm-proxy.mjs: localhost only, allowlisted hosts). Without an LLM, the rule-based agent answers, so the basic demo needs no paid API.')]

s += [P('Optional class room', 'h2'),
      P('One command on the professor’s laptop, <b>node tools/opslab-server.mjs</b> (Node 18+, no dependencies), turns OpsLab into a class activity on the local network. The professor creates a room (optionally restricted to a pasted roll-number list) and shares a 6-character code. Students open the printed address, join with the code and their roll number, and every run is submitted automatically.'),
      table([['Feature', 'How it works'],
             ['Live dashboard', 'Best % of optimum per student and topic, leaderboard (score out of 6), class first-run vs best-run averages, most common mistakes per topic, students not yet joined; refreshes every 10 s.'],
             ['Fair results', 'The server loads the simulation engine from opslab.html and re-computes every run from the submitted decisions; out-of-range inputs are rejected. Only standard-scenario runs count for the leaderboard.'],
             ['Identity', 'One device per roll number (token-based); the professor can reset a device. Roll numbers outside the class list are refused.'],
             ['Robustness', 'Runs made while the server is unreachable are queued and sent later; data is saved to opslab-rooms.json; rooms can be closed and reopened.'],
             ['Grading', 'CSV export with rank, roll, name, score, best % and runs per topic, including students who never joined.']], [W * 0.2, W * 0.8])]
s += [P('5. Technologies', 'h1')]
s += bullets(['One HTML5 file (about 2,100 lines) with embedded CSS and vanilla JavaScript. No frameworks, libraries, CDNs or network calls.',
              'Charts are hand-built inline SVG (grouped bars, lines, Gantt, stacked bars) with hover tooltips.',
              'Seeded PRNG (mulberry32) + Box–Muller for reproducible demand; Acklam inverse-normal for sigma levels; exact Erlang C.',
              'Responsive CSS grid (desktop three-column, tablet two-column, phone single column) with light and dark themes and print styles for the report.',
              'Optional live agent: two adapters, Claude Messages API (default Claude Opus 5.5) and OpenAI-compatible chat completions (NVIDIA NIM, OpenAI, Groq, OpenRouter, Gemini, Ollama, custom), sharing one client-side tool-calling loop over four simulator tools. An optional zero-dependency Node proxy (tools/llm-proxy.mjs) handles providers that block browser calls.',
              'Optional class-room server: Node 18+ built-ins only (http, vm, crypto); serves the page, hosts rooms, re-computes runs with the engine extracted from opslab.html, and includes the LLM proxy.',
              'Validation: automated headless-browser tests (Playwright + Chromium).'])

s += [P('6. Usage instructions', 'h1')]
s += bullets(['Open <b>opslab.html</b> in Chrome, Edge, Firefox or Safari. It also works offline.',
              'Pick a topic in the left navigation. Open <i>Concept &amp; formulas</i> to review the theory.',
              'Change the blue <b>decision</b> inputs (sliders or number boxes). Grey <b>scenario</b> inputs change the environment.',
              'Press <b>Run simulation</b>. Read the KPI cards (▲/▼ vs the previous run), the chart and the before/after table.',
              'Read the agent’s report on the right. Press <b>Get AI advice</b> for the alternatives table, or <b>Apply recommendation</b> and then <b>Run again</b>.',
              '<b>Reset topic</b> restores defaults and clears that topic’s history. <b>Reset all</b> clears the whole session.',
              'Optional: open <b>Live LLM settings</b> in the <i>Ask the AI agent</i> box, choose a provider (Claude, NVIDIA, OpenAI, Groq, OpenRouter, Gemini, Ollama, or custom), enter the key, click <b>Load models</b> to pick a current model, and ask questions in plain language. For NVIDIA, first run <b>node tools/llm-proxy.mjs</b> and keep “Use local proxy” ticked. Without an LLM the rule-based agent answers.',
              'Optional class room: the professor runs <b>node tools/opslab-server.mjs</b>, opens the printed address, creates a room in <b>Class room</b>, and shares the code; students join with the code and their roll number.',
              'Open <b>Session report</b> at the end and use <b>Print / save as PDF</b>.'])

s += [P('7. Instructor guide', 'h1'), P('Learning objectives', 'h2')]
s += bullets(['Identify bottlenecks and justify capacity with throughput economics.', 'Set EOQ / ROP / safety-stock policies that balance holding, ordering and stockout costs.',
              'Compare dispatching rules on flow time, WIP and tardiness.', 'Apply the cost-of-quality framework (prevention vs appraisal vs failure).',
              'Staff service systems using utilization, Erlang C, Little’s Law and service targets.', 'Design supply-chain resilience (buffers, dual sourcing, contingency).',
              'Use what-if analysis and optimization to evaluate operational decisions.'])
s += [P('Suggested 75-minute session', 'h2'), table([['Minutes', 'Activity'],
    ['0–10', 'Set the role (students are operations managers). Show decisions vs scenario inputs.'],
    ['10–55', '3–4 topics, about 10 min each: review the concept, ask students to predict the best decision, run the defaults, let teams change one decision at a time, then open Get AI advice and discuss the trade-offs.'],
    ['55–70', 'Stress test: change a scenario input (demand +30%, longer disruption). Is the recommendation still best?'],
    ['70–75', 'Open the Session report, discuss the lessons, and print or save it for the record.']], [W * 0.15, W * 0.85])]
s += [P('Discussion prompts', 'h2')]
s += bullets(['Why does adding a Cutting machine change nothing? Where does the bottleneck move next?', 'Why does the agent’s ROP differ from the 95% textbook ROP?',
              'Why is the makespan identical for every sequence?', 'At what external failure cost does 100% inspection pay off?',
              'Why does the 5th server cut waiting far more than the 6th?', 'Set the disruption duration to 0. Which strategy wastes the most money?'])

s += [P('8. Validation', 'h1'), P('An automated Playwright test drives the real page in Chromium and checks:')]
s += bullets(['Every topic: Run, Run again (identical results, so deterministic), KPI cards free of NaN, chart and diagnosis rendered.',
              'Every input in every topic (56 inputs, including the job table, rule selector, custom sequence and checkbox) changes the results or the agent’s recommendation. Inputs that matter only in some situations (e.g. backup premium when no backup is used) say so in their help text.',
              'Get AI advice, Hide advice, Apply recommendation → Run again reaches 100% of the best option in every topic.',
              'Input validation: an invalid custom sequence is rejected with a message; out-of-range numbers are clamped; an unstable queue is diagnosed.',
              'Reset topic, Reset all, Session report, Instructor guide and theme toggle work; no JavaScript errors; no horizontal page scroll at 390 px phone width.',
              'Live agent, tested against a mocked Claude API: correct headers and body; all tool results returned in one message with matching ids; assistant content (including thinking blocks) passed back unchanged; the simulation tool returns engine numbers ($1,920); bad inputs return is_error; the sandbox leaves inputs untouched; Apply suggested settings works; a 401 error is shown and rolled back; chats are kept per topic; Remember/Forget key works; no network calls without a key.',
              'OpenAI-compatible path, tested end to end through the real local proxy against a fake NVIDIA-style server: request shape and Bearer auth; tool calls and tool messages with matching ids; JSON-string arguments parsed (invalid JSON reported to the model); <think> reasoning hidden; automatic grounded mode for a model that rejects tools; NVIDIA preset defaults; a clear message when the browser call is blocked; Ollama works without a key; the proxy rejects hosts outside its allowlist and answers CORS preflight.',
              'Class room, tested end to end with a real server and three browsers: room creation with a class list; joining from a file:// page and from the served page; automatic run submission; practice runs for changed scenarios; roll numbers outside the class list and duplicate devices refused; a forged result ignored (server re-computed 70%); dashboard, common mistakes, leaderboard order and CSV export; device reset; closed room; runs queued while the server was down and delivered after restart; state kept across page reloads.'])

def footer(c, d):
    c.saveState(); c.setFont('Sans', 7.5); c.setFillColor(MUTED)
    c.drawString(18 * mm, 10 * mm, 'OpsLab: AI-Powered Operations Management Simulator'); c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(d.page)); c.restoreState()
doc = SimpleDocTemplate(os.path.join(HERE, 'OpsLab_Documentation.pdf'), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                        title='OpsLab: AI-Powered Operations Management Simulator', author='OpsLab')
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print('ok')
