// The 2-hour day-before-exam session plan, as a guided-practice flow.
// Derived from data/students/bella_data/may_fourteenth_session_plan.md.
// Bella-specific for v1 — the source plan references her gaps and context directly.

export type StageKind = 'instruction' | 'warmup' | 'frq' | 'break' | 'writing';

export interface GuidedStage {
  id: string;
  title: string;
  timeLabel: string;      // human-readable slot, e.g. "0:00–0:10"
  durationMin: number;    // countdown budget in minutes
  kind: StageKind;
  purpose: string;        // the one-line "why" / framing
  body: string[];         // instruction lines shown to tutor + student
  checklist?: string[];   // optional tickable sub-steps
  testId?: string;        // for kind === 'frq': which test to embed
  writingPrompt?: string; // for kind === 'writing': the textarea prompt
}

export const GUIDED_PLAN: GuidedStage[] = [
  {
    id: 'reanchor',
    title: 'Re-anchor + Energy Check',
    timeLabel: '0:00–0:10',
    durationMin: 10,
    kind: 'instruction',
    purpose: 'Set the frame before anything else.',
    body: [
      'Say it out loud: "Today is not about learning new things. It\'s about proving to yourself you already know this."',
      'Quick energy check — where is she at? Energy, pain, focus (1–10 is fine). Adapt pace accordingly.',
      'Name today\'s shape: warm-up → mixed FRQ practice → break → strategy → calm close-out. No surprises.',
    ],
    checklist: [
      'Frame stated out loud',
      'Energy / pain / focus checked',
      'Today\'s structure previewed',
    ],
  },
  {
    id: 'warmup',
    title: 'Warm-up Retrieval',
    timeLabel: '0:10–0:25',
    durationMin: 15,
    kind: 'warmup',
    purpose: 'Rapid, low-stakes recall on her STRONG areas — build the confidence floor.',
    body: [
      'Keep it fast and light. These are things she already knows — the point is to let her FEEL that.',
      'Rapid-fire, no scoring, no pressure. If she stalls, give it and move on.',
    ],
    checklist: [
      'Recursion trace — e.g. factorial / Fibonacci by hand',
      'ArrayList API — add, get, set, size, remove(index)',
      'Enhanced for-loop — the variable IS the value, not the index',
      '.length vs .size() vs .length() — array / ArrayList / String',
      'Integer division & casting — 7 / 2 vs (double) 7 / 2',
    ],
  },
  {
    id: 'frq-rehearsal',
    title: 'Interleaved FRQ Rehearsal',
    timeLabel: '0:25–1:10',
    durationMin: 45,
    kind: 'frq',
    purpose: 'Mixed FRQ types — rehearse the "which pattern is this?" decision the real exam tests.',
    body: [
      'Work through the embedded FRQ drill below. The types are deliberately mixed — do NOT reorder them into blocks.',
      'Before she writes any code, have her say out loud: "Which pattern is this?"',
      'Time-box each problem. If she stalls, narrate the scaffold (counter → loop → condition → return) and move on.',
      'Lean into the 2D-array problem — that is her slowest area. Extra reps here are the highest-value minutes of the session.',
    ],
    testId: 'bella_data_quiz_8',
    checklist: [
      'She narrated "which pattern is this" before coding each one',
      'Each problem time-boxed (didn\'t rabbit-hole)',
      'Extra attention paid to the 2D-array FRQ',
    ],
  },
  {
    id: 'break',
    title: 'Break',
    timeLabel: '1:10–1:20',
    durationMin: 10,
    kind: 'break',
    purpose: 'Rest matters. Don\'t grind two hours straight — fatigue erodes everything after this.',
    body: [
      'Step away from the screen. Stretch, water, breathe.',
      'No quizzing during the break. The break IS the intervention.',
    ],
  },
  {
    id: 'strategy',
    title: 'Test-day Strategy Rehearsal',
    timeLabel: '1:20–1:45',
    durationMin: 25,
    kind: 'instruction',
    purpose: 'Rehearse the test-day procedures — concrete and practiced, not abstract.',
    body: [
      'Walk each one as a thing she DOES, not a thing she knows. Have her say the steps back.',
    ],
    checklist: [
      '3-pass MCQ approach — easy pass, then medium, then hard',
      'Skip-and-return discipline — mark it, move on, come back',
      'FRQ scaffold — counter → loop → condition → return',
      'Use the provided helper methods — graders deduct for re-implementing them',
      'Recursion MCQs — if you can\'t trace it in ~30s, mark and skip',
    ],
  },
  {
    id: 'psych-tools',
    title: 'Psychological Tools',
    timeLabel: '1:45–1:55',
    durationMin: 10,
    kind: 'writing',
    purpose: 'Teach and practice the two evidence-backed test-day tools so they\'re familiar tomorrow.',
    body: [
      'Arousal reappraisal: teach the reframe — "The knot in my stomach means my body is getting ready. That\'s fuel, not a warning." Have her repeat it in her own words.',
      'Expressive writing: explain that 10 minutes of writing about test worries before the exam frees up working memory (Ramirez & Beilock 2011). Tomorrow morning she does the full 10 minutes — right now, do a quick 3-minute version in the box below so the technique is familiar.',
    ],
    writingPrompt:
      'Practice run (~3 min): write whatever you\'re feeling about tomorrow\'s exam — the worries, the what-ifs, all of it. No one grades this. Getting it onto the page is the whole point.',
    checklist: [
      'Arousal-reappraisal reframe taught + repeated back in her words',
      '3-minute expressive-writing practice done',
      'Plan confirmed: full 10-minute version tomorrow morning before the exam',
    ],
  },
  {
    id: 'closeout',
    title: 'Close-out + Rest Prescription',
    timeLabel: '1:55–2:00',
    durationMin: 5,
    kind: 'instruction',
    purpose: 'End calm and clear. The hand-off itself is an arousal-reappraisal cue.',
    body: [
      'Say it plainly: "You\'re prepared."',
      'Tonight: light review only — read your notes once, no new problems. Normal bedtime.',
      'Tomorrow: eat breakfast, hydrate, light morning movement, bring your ice pack, get there early.',
      'Project calm-confidence — not worry. That models the challenge appraisal for her.',
    ],
    checklist: [
      '"You\'re prepared" said out loud',
      'Tonight\'s rest prescription given (light review, normal bedtime)',
      'Tomorrow\'s logistics covered (breakfast, ice pack, arrive early)',
    ],
  },
];
