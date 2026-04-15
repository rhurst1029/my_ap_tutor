/**
 * simulate_student.js
 * Playwright script that simulates a test student taking the ap_csa_assessment.
 * Drives the real frontend UI at http://localhost:5173, submitting answers via
 * the normal quiz flow so responses are saved through the API and report
 * generation is triggered as a background task.
 *
 * Usage:
 *   node testing/simulate_student.js [studentName]
 *   node testing/simulate_student.js TestStudent
 *
 * Expected output:
 *   Session saved. Report generation triggered in background.
 *   Student data written to data/students/teststudent_data/
 */

const { chromium } = require('playwright');

// ── Student config ─────────────────────────────────────────────────────────
const STUDENT_NAME = process.argv[2] || 'TestStudent';
const FRONTEND_URL = 'http://localhost:5173';

// ── Simulated answers per question ─────────────────────────────────────────
// Intentionally wrong on some to give the report meaningful weak areas.
// Q1 strings(correct=A)  → B  wrong
// Q2 operators(correct=B)→ A  wrong
// Q3 conditionals(A)     → A  correct
// Q4 loops(C)            → C  correct
// Q5 loops(C)            → B  wrong
// Q6 classes(B)          → B  correct
// Q7 classes(C)          → C  correct
// Q8 arrays(B)           → C  wrong
// Q9 arraylist(A)        → A  correct
// Q10 2d_arrays(A)       → B  wrong
// Score: 5/10 — weak in strings, operators, loops, arrays, 2d_arrays
const ANSWERS = ['B', 'A', 'A', 'C', 'B', 'B', 'C', 'C', 'A', 'B'];

// Guiding question responses (brief, plausible student thoughts)
const GUIDING_TEXTS = [
  ["I think index 0 is 'c', so 3 is maybe 'p'?", "I think b is not included", "Index 5 might be 'u'"],
  ["Both are int so it stays int I think", "Maybe cast one to double", "It would be 3.5 then"],
  ["NOT of true&&false is NOT false which is true, OR with true is true", "true || true is true", ""],
  ["The loop runs while k < 5, printing each k", "k starts at 0", "it prints 0 1 2 3 4"],
  ["The loop multiplies each time", "I think it doubles each time", "n goes 1 2 4 8 16?"],
  ["getBalance returns the field", "The constructor sets it to 500", "So output is 500.0"],
  ["speak() is called on the Dog object", "Dog inherits from Animal", "Dog overrides speak"],
  ["arr[0] is 5, arr[2] is 15, sum is 20?", "Need to check all indices", "Maybe I missed one"],
  ["remove(0) removes first element", "Then get(0) returns new first", "That would be 20"],
  ["Row 0 col 1 is 2, row 1 col 0 is 3?", "Matrix access is [row][col]", "grid[1][0] should be 3"],
];

async function run() {
  console.log(`\n🎓 Simulating student: ${STUDENT_NAME}`);
  console.log(`   Frontend: ${FRONTEND_URL}`);
  console.log(`   Answers:  ${ANSWERS.join(', ')}\n`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // ── 1. Navigate to the app ───────────────────────────────────────────────
  await page.goto(FRONTEND_URL);
  await page.waitForSelector('input[placeholder="Enter your first name"]');
  console.log('✓ App loaded');

  // ── 2. Enter student name ────────────────────────────────────────────────
  await page.fill('input[placeholder="Enter your first name"]', STUDENT_NAME);
  await page.click('button:has-text("Continue")');
  console.log(`✓ Name entered: ${STUDENT_NAME}`);

  // ── 3. Wait for history panel and start the test ─────────────────────────
  await page.waitForSelector('.history-panel');
  const startBtn = page.locator('.btn-primary').first();
  await startBtn.click();
  console.log('✓ Test started');

  // ── 4. Wait for TestRunner to initialise ─────────────────────────────────
  await page.waitForSelector('.test-runner', { timeout: 10000 });
  await page.waitForSelector('.question-card', { timeout: 10000 });
  console.log('✓ TestRunner loaded\n');

  // ── 5. Answer each question ───────────────────────────────────────────────
  for (let i = 0; i < ANSWERS.length; i++) {
    const answer = ANSWERS[i];
    const guiding = GUIDING_TEXTS[i] || [];

    // Wait for the question counter to confirm we're on the right question
    await page.waitForFunction(
      (idx) => {
        const el = document.querySelector('.question-counter');
        return el && el.textContent.includes(`Question ${idx + 1}`);
      },
      i,
      { timeout: 5000 }
    );

    console.log(`  Q${i + 1}: selecting ${answer}…`);

    // Select the radio option — click the label containing the answer key span
    const optionLabel = page.locator(`.option:has(.option-key:text-is("${answer}"))`).first();
    await optionLabel.click();

    // Fill guiding question textareas (optional but realistic)
    const textareas = page.locator('.guiding-question textarea');
    const count = await textareas.count();
    for (let g = 0; g < count && g < guiding.length; g++) {
      if (guiding[g]) {
        await textareas.nth(g).fill(guiding[g]);
      }
    }

    // Submit
    await page.click('button.submit-btn');
    console.log(`  Q${i + 1}: submitted ✓`);

    // Wait for feedback to appear
    await page.waitForSelector('.feedback', { timeout: 3000 }).catch(() => {});

    // Wait for next question transition (800ms in TestRunner + buffer)
    if (i < ANSWERS.length - 1) {
      await page.waitForFunction(
        (idx) => {
          const el = document.querySelector('.question-counter');
          return el && el.textContent.includes(`Question ${idx + 2}`);
        },
        i,
        { timeout: 5000 }
      );
    }
  }

  // ── 6. Wait for completion screen ────────────────────────────────────────
  await page.waitForSelector('.completion-screen, .results-screen, h2', { timeout: 10000 });
  console.log('\n✓ All questions answered — completion screen reached');

  // Give the /save API call a moment to complete and trigger background task
  await page.waitForTimeout(2000);

  const bodyText = await page.locator('body').innerText();
  console.log('\n── Completion screen content ──────────────────────────────');
  console.log(bodyText.slice(0, 500));
  console.log('───────────────────────────────────────────────────────────\n');

  await browser.close();
  console.log('✓ Browser closed. Session saved via API.');
  console.log(`  Report generation triggered in background.`);
  console.log(`  Check: data/students/${STUDENT_NAME.toLowerCase()}_data/\n`);
}

run().catch(err => {
  console.error('Simulation failed:', err.message);
  process.exit(1);
});
