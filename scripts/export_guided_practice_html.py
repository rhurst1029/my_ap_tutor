#!/usr/bin/env python3
"""Export the guided-practice session as a single self-contained HTML file.

The exported file runs entirely offline — no backend, no build step, no
internet. Bella can double-click it in any browser and work through the
2-hour session: timed stages, interactive guiding-question MCQs, code
textareas for the FRQs, reveal-the-reference-solution, and a self-check
test-case list. All her progress (place, checkboxes, code, writing) is
saved to localStorage so she can close and reopen.

What it canNOT do: compile/run Java (that needs the backend). Instead the
FRQ workflow is "write your solution, then reveal the reference to compare,
and self-check against the listed test cases." For real execution she still
has the standalone Q{N}.java IntelliJ files.

Usage:
    python3 scripts/export_guided_practice_html.py
    # writes data/students/bella_data/bella_guided_practice.html

Source of FRQ content: data/tests/generated/bella_data_quiz_8.json
Source of the 7-stage plan: mirrors frontend/src/components/GuidedPractice/guidedPlan.ts
"""
import json
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUIZ_PATH = ROOT / "data" / "tests" / "generated" / "bella_data_quiz_8.json"
OUT_PATH = ROOT / "data" / "students" / "bella_data" / "bella_guided_practice.html"

# --- The 7-stage plan (mirrors guidedPlan.ts) -----------------------------
PLAN = [
    {
        "id": "reanchor", "title": "Re-anchor + Energy Check",
        "timeLabel": "0:00-0:10", "durationMin": 10, "kind": "instruction",
        "purpose": "Set the frame before anything else.",
        "body": [
            'Say it out loud: "Today is not about learning new things. It\'s about proving to yourself you already know this."',
            "Quick energy check - where are you at? Energy, pain, focus (1-10 is fine). Adapt pace accordingly.",
            "Name today's shape: warm-up -> mixed FRQ practice -> break -> strategy -> calm close-out. No surprises.",
        ],
        "checklist": [
            "Frame stated out loud",
            "Energy / pain / focus checked",
            "Today's structure previewed",
        ],
    },
    {
        "id": "warmup", "title": "Warm-up Retrieval",
        "timeLabel": "0:10-0:25", "durationMin": 15, "kind": "warmup",
        "purpose": "Rapid, low-stakes recall on your STRONG areas - build the confidence floor.",
        "body": [
            "Keep it fast and light. These are things you already know - the point is to let yourself FEEL that.",
            "Rapid-fire, no scoring, no pressure. If you stall, look it up and move on.",
        ],
        "checklist": [
            "Recursion trace - e.g. factorial / Fibonacci by hand",
            "ArrayList API - add, get, set, size, remove(index)",
            "Enhanced for-loop - the variable IS the value, not the index",
            ".length vs .size() vs .length() - array / ArrayList / String",
            "Integer division & casting - 7 / 2 vs (double) 7 / 2",
        ],
    },
    {
        "id": "frq-rehearsal", "title": "Interleaved FRQ Rehearsal",
        "timeLabel": "0:25-1:10", "durationMin": 45, "kind": "frq",
        "purpose": 'Mixed FRQ types - rehearse the "which pattern is this?" decision the real exam tests.',
        "body": [
            "Work through the 4 FRQs below. The types are deliberately mixed - do NOT reorder them into blocks.",
            'Before you write any code, say out loud: "Which pattern is this?"',
            "Time-box each problem. If you stall, fall back on the scaffold (counter -> loop -> condition -> return) and move on.",
            "Lean into the 2D-array problem - that is your slowest area. Extra reps here are the highest-value minutes of the session.",
            "Write your solution in the box, then reveal the reference to compare. Walk the test cases to self-check.",
        ],
        "checklist": [
            'You narrated "which pattern is this" before coding each one',
            "Each problem time-boxed (didn't rabbit-hole)",
            "Extra attention paid to the 2D-array FRQ",
        ],
    },
    {
        "id": "break", "title": "Break",
        "timeLabel": "1:10-1:20", "durationMin": 10, "kind": "break",
        "purpose": "Rest matters. Don't grind two hours straight - fatigue erodes everything after this.",
        "body": [
            "Step away from the screen. Stretch, water, breathe.",
            "No quizzing during the break. The break IS the intervention.",
        ],
        "checklist": [],
    },
    {
        "id": "strategy", "title": "Test-day Strategy Rehearsal",
        "timeLabel": "1:20-1:45", "durationMin": 25, "kind": "instruction",
        "purpose": "Rehearse the test-day procedures - concrete and practiced, not abstract.",
        "body": [
            "Walk each one as a thing you DO, not a thing you know. Say the steps back out loud.",
        ],
        "checklist": [
            "3-pass MCQ approach - easy pass, then medium, then hard",
            "Skip-and-return discipline - mark it, move on, come back",
            "FRQ scaffold - counter -> loop -> condition -> return",
            "Use the provided helper methods - graders deduct for re-implementing them",
            "Recursion MCQs - if you can't trace it in ~30s, mark and skip",
        ],
    },
    {
        "id": "psych-tools", "title": "Psychological Tools",
        "timeLabel": "1:45-1:55", "durationMin": 10, "kind": "writing",
        "purpose": "Practice the two evidence-backed test-day tools so they're familiar tomorrow.",
        "body": [
            'Arousal reappraisal: the reframe is "The knot in my stomach means my body is getting ready. That\'s fuel, not a warning." Say it in your own words.',
            "Expressive writing: 10 minutes of writing about test worries before the exam frees up working memory (Ramirez & Beilock 2011). Tomorrow morning you do the full 10 minutes - right now, do a quick 3-minute version in the box below so the technique is familiar.",
        ],
        "writingPrompt": "Practice run (~3 min): write whatever you're feeling about tomorrow's exam - the worries, the what-ifs, all of it. No one grades this. Getting it onto the page is the whole point.",
        "checklist": [
            "Arousal-reappraisal reframe said in your own words",
            "3-minute expressive-writing practice done",
            "Plan confirmed: full 10-minute version tomorrow morning before the exam",
        ],
    },
    {
        "id": "closeout", "title": "Close-out + Rest Prescription",
        "timeLabel": "1:55-2:00", "durationMin": 5, "kind": "instruction",
        "purpose": "End calm and clear.",
        "body": [
            'Say it plainly: "You\'re prepared."',
            "Tonight: light review only - read your notes once, no new problems. Normal bedtime.",
            "Tomorrow: eat breakfast, hydrate, light morning movement, bring your ice pack, get there early.",
        ],
        "checklist": [
            '"You\'re prepared" - believe it',
            "Tonight's rest plan set (light review, normal bedtime)",
            "Tomorrow's logistics ready (breakfast, ice pack, arrive early)",
        ],
    },
]


def load_frqs():
    """Pull the 4 FRQs out of bella_data_quiz_8.json into a lean shape."""
    quiz = json.loads(QUIZ_PATH.read_text())
    frqs = []
    for q in quiz["questions"]:
        if q.get("type") != "frq":
            continue
        part = q["parts"][0]
        frqs.append({
            "id": q["id"],
            "topic_tags": q.get("topic_tags", []),
            "unit": q.get("unit"),
            "prompt": q["prompt"],
            "guiding_questions": q.get("guiding_questions", []),
            "explanation": q.get("explanation", ""),
            "starter_code": part.get("starter_code", ""),
            "test_cases": part.get("test_cases", []),
        })
    return frqs, quiz.get("title", "FRQ Drill")


# --- HTML template --------------------------------------------------------
# The {{DATA}} marker is replaced with the embedded JSON. Everything else is
# literal — no f-string, so JS braces stay untouched.
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bella - Guided Practice Session</title>
<style>
  :root {
    --bg: #f6f7f9; --surface: #ffffff; --ink: #1f2330; --muted: #6b7280;
    --line: #e1e4ea; --accent: #2851a3; --accent-soft: #eef2fb;
    --good: #1b8a4b; --bad: #c0392b; --warn: #b9770e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.55; padding: 1.5rem;
  }
  .wrap { max-width: 880px; margin: 0 auto; }

  header.bar {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1.1rem;
  }
  .bar-top {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--muted); margin-bottom: 0.6rem;
  }
  .progress { height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden; margin-bottom: 0.9rem; }
  .progress > div { height: 100%; background: var(--accent); transition: width .3s; }
  .bar-main { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
  .bar-main h1 { font-size: 1.3rem; }
  .timelabel { font-size: 0.85rem; color: var(--muted); }
  .timer { text-align: right; flex-shrink: 0; }
  .clock { font-size: 1.9rem; font-weight: 700; font-variant-numeric: tabular-nums; }
  .clock.up { color: var(--warn); }
  .timer-ctrls { display: flex; gap: 0.35rem; justify-content: flex-end; margin-top: 0.3rem; }
  button {
    font: inherit; cursor: pointer; border-radius: 7px;
    border: 1px solid var(--line); background: var(--surface); color: var(--ink);
    padding: 0.4rem 0.8rem;
  }
  button:hover:not(:disabled) { border-color: var(--accent); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .timer-ctrls button { padding: 0.2rem 0.55rem; font-size: 0.75rem; }
  button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
  button.primary:hover:not(:disabled) { background: #1d3c7d; }

  .card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 1.25rem; margin-bottom: 1.1rem;
  }
  .purpose { font-weight: 600; margin-bottom: 0.8rem; }
  ul.steps { list-style: none; }
  ul.steps li { position: relative; padding-left: 1.15rem; margin-bottom: 0.5rem; }
  ul.steps li::before { content: "\2192"; position: absolute; left: 0; color: var(--accent); }

  .checklist { margin-top: 1rem; padding-top: 0.85rem; border-top: 1px solid var(--line); }
  .checklist .lbl { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin-bottom: 0.5rem; }
  .check { display: flex; gap: 0.55rem; align-items: flex-start; padding: 0.3rem 0; cursor: pointer; }
  .check input { margin-top: 0.25rem; }
  .check.done span { color: var(--muted); text-decoration: line-through; }

  .break-note { text-align: center; color: var(--muted); padding: 1.5rem; font-size: 1.05rem; }

  textarea {
    width: 100%; font: 0.9rem/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    border: 1px solid var(--line); border-radius: 8px; padding: 0.7rem;
    background: #fbfbfd; color: var(--ink); resize: vertical;
  }
  textarea:focus { outline: none; border-color: var(--accent); }
  .writing-prompt { display: block; font-size: 0.9rem; color: var(--muted); margin-bottom: 0.5rem; }

  /* FRQ blocks */
  .frq { border: 1px solid var(--line); border-radius: 9px; margin-bottom: 1rem; overflow: hidden; }
  .frq-head {
    background: var(--accent-soft); padding: 0.6rem 0.9rem; cursor: pointer;
    display: flex; justify-content: space-between; align-items: center; gap: 0.6rem;
  }
  .frq-head h3 { font-size: 0.98rem; }
  .frq-tags { font-size: 0.72rem; color: var(--muted); }
  .frq-toggle { font-size: 0.8rem; color: var(--accent); }
  .frq-body { padding: 0.9rem; display: none; }
  .frq.open .frq-body { display: block; }
  .prompt {
    white-space: pre-wrap; font-size: 0.9rem; background: #fbfbfd;
    border: 1px solid var(--line); border-radius: 7px; padding: 0.75rem;
    margin-bottom: 0.9rem;
  }
  .section-lbl { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 0.9rem 0 0.4rem; }

  .gq { border: 1px solid var(--line); border-radius: 7px; padding: 0.6rem 0.75rem; margin-bottom: 0.55rem; }
  .gq-text { font-size: 0.9rem; margin-bottom: 0.4rem; }
  .gq-opt { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.25rem 0; cursor: pointer; font-size: 0.88rem; }
  .gq-opt.correct { color: var(--good); font-weight: 600; }
  .gq-opt.wrong { color: var(--bad); }
  .gq-verdict { font-size: 0.82rem; margin-top: 0.35rem; }
  .gq-verdict.ok { color: var(--good); }
  .gq-verdict.no { color: var(--bad); }

  .reveal-box {
    display: none; white-space: pre-wrap; font-size: 0.86rem;
    background: #f4f7f4; border: 1px solid #cfe4d4; border-radius: 7px;
    padding: 0.75rem; margin-top: 0.5rem;
  }
  .reveal-box.show { display: block; }
  .tc { font-size: 0.85rem; padding: 0.25rem 0; display: flex; gap: 0.5rem; align-items: flex-start; cursor: pointer; }
  .tc input { margin-top: 0.2rem; }
  .tc.done .tc-text { color: var(--muted); text-decoration: line-through; }
  code { background: #eef0f3; padding: 0.05rem 0.3rem; border-radius: 4px; font-size: 0.86em; }

  .nav { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
  .dots { display: flex; gap: 0.35rem; }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--line); }
  .dot.past { background: var(--accent); opacity: 0.45; }
  .dot.active { background: var(--accent); }

  .note { font-size: 0.8rem; color: var(--muted); margin-top: 0.6rem; }
  .footer { text-align: center; font-size: 0.78rem; color: var(--muted); margin-top: 1.5rem; }
</style>
</head>
<body>
<div class="wrap">
  <header class="bar">
    <div class="bar-top">
      <span id="kicker">Guided Practice</span>
      <button id="resetAll" style="font-size:0.7rem;padding:0.15rem 0.5rem;">Reset all progress</button>
    </div>
    <div class="progress"><div id="progressFill"></div></div>
    <div class="bar-main">
      <div>
        <h1 id="stageTitle"></h1>
        <span class="timelabel" id="stageTime"></span>
      </div>
      <div class="timer">
        <span class="clock" id="clock"></span>
        <div class="timer-ctrls">
          <button id="tPause"></button>
          <button id="tReset">Reset</button>
        </div>
      </div>
    </div>
  </header>

  <div class="card" id="stageCard"></div>

  <div class="nav">
    <button id="prev">&larr; Previous</button>
    <span class="dots" id="dots"></span>
    <button id="next" class="primary">Next &rarr;</button>
  </div>

  <div class="footer">
    Self-contained offline study file &mdash; your progress saves automatically in this browser.
  </div>
</div>

<script>
const DATA = {{DATA}};
const PLAN = DATA.plan;
const FRQS = DATA.frqs;
const LS = {
  get: (k, d) => { try { const v = localStorage.getItem('bgp:' + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
  set: (k, v) => { try { localStorage.setItem('bgp:' + k, JSON.stringify(v)); } catch (e) {} },
  clearAll: () => { Object.keys(localStorage).filter(k => k.startsWith('bgp:')).forEach(k => localStorage.removeItem(k)); },
};

let stageIndex = LS.get('stage', 0);
if (stageIndex < 0 || stageIndex >= PLAN.length) stageIndex = 0;
let secondsLeft = PLAN[stageIndex].durationMin * 60;
let timerRunning = true;
let tick = null;

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function fmt(s) {
  const m = Math.floor(s / 60), ss = s % 60;
  return m + ':' + String(ss).padStart(2, '0');
}

function startTimer() {
  if (tick) clearInterval(tick);
  tick = setInterval(() => {
    if (!timerRunning) return;
    secondsLeft = Math.max(0, secondsLeft - 1);
    paintClock();
  }, 1000);
}
function paintClock() {
  const up = secondsLeft === 0;
  const c = document.getElementById('clock');
  c.textContent = up ? "Time's up" : fmt(secondsLeft);
  c.classList.toggle('up', up);
}

function renderFRQ(frq) {
  const open = LS.get('frqopen:' + frq.id, frq.id === FRQS[0].id);
  let gq = '';
  frq.guiding_questions.forEach(q => {
    const saved = LS.get('mcq:' + frq.id + ':' + q.id, null);
    let opts = '';
    Object.keys(q.options).forEach(key => {
      let cls = 'gq-opt';
      if (saved !== null) {
        if (key === q.answer_key) cls += ' correct';
        else if (key === saved) cls += ' wrong';
      }
      opts += '<label class="' + cls + '">' +
        '<input type="radio" name="' + frq.id + '_' + q.id + '" value="' + key + '"' +
        (saved === key ? ' checked' : '') + (saved !== null ? ' disabled' : '') +
        ' data-frq="' + frq.id + '" data-gq="' + q.id + '" data-ans="' + q.answer_key + '">' +
        '<span>' + esc(key) + '. ' + esc(q.options[key]) + '</span></label>';
    });
    let verdict = '';
    if (saved !== null) {
      const ok = saved === q.answer_key;
      verdict = '<div class="gq-verdict ' + (ok ? 'ok' : 'no') + '">' +
        (ok ? '✓ Correct' : '✗ Not quite — the answer is ' + esc(q.answer_key)) + '</div>';
    }
    gq += '<div class="gq"><div class="gq-text">' + esc(q.text) + '</div>' + opts + verdict + '</div>';
  });

  let tcs = '';
  frq.test_cases.forEach((tc, i) => {
    const k = 'tc:' + frq.id + ':' + i;
    const done = LS.get(k, false);
    tcs += '<label class="tc ' + (done ? 'done' : '') + '">' +
      '<input type="checkbox" data-tc="' + k + '"' + (done ? ' checked' : '') + '>' +
      '<span class="tc-text">' + esc(tc.description) +
      (tc.expected_output ? ' &mdash; expects <code>' + esc(tc.expected_output) + '</code>' : '') +
      '</span></label>';
  });

  const code = LS.get('code:' + frq.id, frq.starter_code);
  const revealed = LS.get('reveal:' + frq.id, false);

  return '<div class="frq ' + (open ? 'open' : '') + '" data-frqwrap="' + frq.id + '">' +
    '<div class="frq-head" data-frqhead="' + frq.id + '">' +
      '<div><h3>' + esc(frq.id.toUpperCase()) + ' &mdash; ' + esc(frq.topic_tags.join(', ')) +
        '</h3><span class="frq-tags">Unit ' + esc(frq.unit) + '</span></div>' +
      '<span class="frq-toggle">' + (open ? 'Hide' : 'Open') + '</span>' +
    '</div>' +
    '<div class="frq-body">' +
      '<div class="prompt">' + esc(frq.prompt) + '</div>' +
      '<div class="section-lbl">Guiding questions</div>' + gq +
      '<div class="section-lbl">Your solution</div>' +
      '<textarea rows="14" data-code="' + frq.id + '">' + esc(code) + '</textarea>' +
      '<div class="section-lbl">Self-check &mdash; test cases</div>' + tcs +
      '<div style="margin-top:0.7rem;">' +
        '<button data-reveal="' + frq.id + '">' + (revealed ? 'Hide' : 'Reveal') + ' reference solution</button>' +
        '<div class="reveal-box ' + (revealed ? 'show' : '') + '" data-revealbox="' + frq.id + '">' +
          esc(frq.explanation) + '</div>' +
      '</div>' +
    '</div>' +
  '</div>';
}

function render() {
  const stage = PLAN[stageIndex];
  document.getElementById('kicker').textContent =
    'Guided Practice · Bella · Stage ' + (stageIndex + 1) + ' of ' + PLAN.length;
  document.getElementById('stageTitle').textContent = stage.title;
  document.getElementById('stageTime').textContent = stage.timeLabel;
  document.getElementById('progressFill').style.width = (stageIndex / PLAN.length * 100) + '%';
  paintClock();
  document.getElementById('tPause').textContent = timerRunning ? 'Pause' : 'Resume';

  // dots
  document.getElementById('dots').innerHTML = PLAN.map((s, i) =>
    '<span class="dot ' + (i === stageIndex ? 'active' : (i < stageIndex ? 'past' : '')) + '"></span>'
  ).join('');

  // body
  let html = '<div class="purpose">' + esc(stage.purpose) + '</div>';
  html += '<ul class="steps">' + stage.body.map(b => '<li>' + esc(b) + '</li>').join('') + '</ul>';

  if (stage.kind === 'frq') {
    html += FRQS.map(renderFRQ).join('');
    html += '<p class="note">No Java compiler in this file — write your solution, reveal the reference to compare, ' +
      'and walk the test cases as a self-check. For real execution use the standalone Q{N}.java files in IntelliJ.</p>';
  }
  if (stage.kind === 'writing') {
    const w = LS.get('writing:' + stage.id, '');
    html += '<div style="margin-top:1rem;">' +
      '<label class="writing-prompt">' + esc(stage.writingPrompt) + '</label>' +
      '<textarea rows="8" data-writing="' + stage.id + '" placeholder="Start writing here...">' + esc(w) + '</textarea>' +
    '</div>';
  }
  if (stage.kind === 'break') {
    html += '<div class="break-note">Take the full break. Come back refreshed.</div>';
  }
  if (stage.checklist && stage.checklist.length) {
    html += '<div class="checklist"><div class="lbl">Checklist</div>' +
      stage.checklist.map((item, i) => {
        const k = 'check:' + stage.id + ':' + i;
        const done = LS.get(k, false);
        return '<label class="check ' + (done ? 'done' : '') + '">' +
          '<input type="checkbox" data-check="' + k + '"' + (done ? ' checked' : '') + '>' +
          '<span>' + esc(item) + '</span></label>';
      }).join('') + '</div>';
  }
  document.getElementById('stageCard').innerHTML = html;

  document.getElementById('prev').disabled = stageIndex === 0;
  const next = document.getElementById('next');
  next.innerHTML = stageIndex === PLAN.length - 1 ? 'Finish &check;' : 'Next &rarr;';
  wireBody();
}

function goStage(idx) {
  stageIndex = Math.max(0, Math.min(PLAN.length - 1, idx));
  LS.set('stage', stageIndex);
  secondsLeft = PLAN[stageIndex].durationMin * 60;
  timerRunning = true;
  render();
}

function wireBody() {
  // checklist
  document.querySelectorAll('[data-check]').forEach(el => {
    el.addEventListener('change', () => {
      LS.set(el.dataset.check, el.checked);
      el.closest('.check').classList.toggle('done', el.checked);
    });
  });
  // test-case self-check
  document.querySelectorAll('[data-tc]').forEach(el => {
    el.addEventListener('change', () => {
      LS.set(el.dataset.tc, el.checked);
      el.closest('.tc').classList.toggle('done', el.checked);
    });
  });
  // writing textarea
  document.querySelectorAll('[data-writing]').forEach(el => {
    el.addEventListener('input', () => LS.set('writing:' + el.dataset.writing, el.value));
  });
  // code textareas
  document.querySelectorAll('[data-code]').forEach(el => {
    el.addEventListener('input', () => LS.set('code:' + el.dataset.code, el.value));
  });
  // FRQ collapse/expand
  document.querySelectorAll('[data-frqhead]').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.frqhead;
      const wrap = document.querySelector('[data-frqwrap="' + id + '"]');
      const open = !wrap.classList.contains('open');
      wrap.classList.toggle('open', open);
      el.querySelector('.frq-toggle').textContent = open ? 'Hide' : 'Open';
      LS.set('frqopen:' + id, open);
    });
  });
  // guiding-question MCQs
  document.querySelectorAll('.gq input[type=radio]').forEach(el => {
    el.addEventListener('change', () => {
      LS.set('mcq:' + el.dataset.frq + ':' + el.dataset.gq, el.value);
      render();
    });
  });
  // reveal reference solution
  document.querySelectorAll('[data-reveal]').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.reveal;
      const box = document.querySelector('[data-revealbox="' + id + '"]');
      const show = !box.classList.contains('show');
      box.classList.toggle('show', show);
      el.textContent = (show ? 'Hide' : 'Reveal') + ' reference solution';
      LS.set('reveal:' + id, show);
    });
  });
}

// header controls
document.getElementById('prev').addEventListener('click', () => goStage(stageIndex - 1));
document.getElementById('next').addEventListener('click', () => goStage(stageIndex + 1));
document.getElementById('tPause').addEventListener('click', () => {
  timerRunning = !timerRunning;
  document.getElementById('tPause').textContent = timerRunning ? 'Pause' : 'Resume';
});
document.getElementById('tReset').addEventListener('click', () => {
  secondsLeft = PLAN[stageIndex].durationMin * 60;
  timerRunning = true;
  document.getElementById('tPause').textContent = 'Pause';
  paintClock();
});
document.getElementById('resetAll').addEventListener('click', () => {
  if (confirm('Clear all saved progress (place, checkboxes, code, writing)?')) {
    LS.clearAll();
    goStage(0);
  }
});

startTimer();
render();
</script>
</body>
</html>
"""


def main():
    frqs, quiz_title = load_frqs()
    payload = {"plan": PLAN, "frqs": frqs, "quizTitle": quiz_title}
    # json.dumps is safe to inline in a <script> as long as we guard </script>.
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    out = HTML_TEMPLATE.replace("{{DATA}}", data_json)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(out, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
    print(f"  {len(PLAN)} stages, {len(frqs)} FRQs embedded")


if __name__ == "__main__":
    main()
