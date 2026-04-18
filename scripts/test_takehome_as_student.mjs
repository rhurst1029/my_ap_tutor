/**
 * scripts/test_takehome_as_student.mjs
 * Playwright end-to-end test: pretend to be Bella taking Session 6 take-home.
 * Captures screenshots, network errors, console errors, and test-run outputs.
 *
 * Run: node scripts/test_takehome_as_student.mjs
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPORT_DIR = path.join(__dirname, '..', 'data', 'students', 'bella_data',
                             'take_home_session_6', '_student_journey_report');
fs.mkdirSync(REPORT_DIR, { recursive: true });

const URL_BASE = 'http://localhost:5173/?takehome=bella_data/take_home_session_6';
const findings = [];
let screenshotCount = 0;

async function shoot(page, label) {
  screenshotCount++;
  const file = path.join(REPORT_DIR, `${String(screenshotCount).padStart(2, '0')}_${label}.png`);
  await page.screenshot({ path: file, fullPage: false });
  return file;
}

function log(level, message, detail = null) {
  const entry = { ts: new Date().toISOString(), level, message, detail };
  findings.push(entry);
  console.log(`[${level.toUpperCase()}] ${message}` + (detail ? ` — ${JSON.stringify(detail).slice(0, 200)}` : ''));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Capture console + network errors
  page.on('console', msg => {
    if (msg.type() === 'error') log('console_error', msg.text());
  });
  page.on('pageerror', err => log('page_error', err.message));
  page.on('requestfailed', req => {
    log('request_failed', `${req.method()} ${req.url()}`, { failure: req.failure()?.errorText });
  });

  // ── 1. Load the page ─────────────────────────────────────────────────────
  log('step', 'Loading take-home URL', URL_BASE);
  await page.goto(URL_BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await shoot(page, 'initial_load');

  // Verify sidebar loaded 15 questions
  const sidebarItems = await page.locator('.takehome-nav-item').count();
  log('check', `Sidebar question count: ${sidebarItems}`, { expected: 15 });
  if (sidebarItems !== 15) log('fail', `Expected 15 questions in sidebar, got ${sidebarItems}`);

  // Verify title and student
  const title = await page.locator('.takehome-sidebar-header h2').textContent();
  const student = await page.locator('.takehome-student').textContent();
  log('check', `Title: "${title}", Student: "${student}"`);

  // ── 2. Inspect Q1 default state ──────────────────────────────────────────
  const currentQTitle = await page.locator('.takehome-header h3').textContent();
  log('check', `Default question: ${currentQTitle}`);

  // Toolbar buttons
  const toolbarButtons = await page.locator('.editor-toolbar button').allTextContents();
  log('check', `Toolbar buttons: ${JSON.stringify(toolbarButtons)}`);

  // Verify right-panel tabs are GONE (user's UI fix request)
  const oldTabs = await page.locator('.panel-tabs').count();
  if (oldTabs > 0) log('fail', 'Old .panel-tabs still present (should be removed)');
  else log('pass', 'Right-panel tabs removed — toolbar-only controls');

  // Verify all 4 panel buttons in toolbar
  for (const expected of ['Run Code', 'Tests', 'Visualize', 'Info', 'Reset']) {
    const hit = toolbarButtons.some(t => t.includes(expected));
    log(hit ? 'pass' : 'fail', `Toolbar contains "${expected}" button`);
  }

  // ── 3. Write a SOLUTION for Q1 (multiplication table) ────────────────────
  log('step', 'Bella writes a solution for Q1 (nested loops — printTable)');
  const q1Solution = `public class Q1 {
    public static void printTable(int n) {
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= n; j++) {
                System.out.print(i * j + " ");
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        printTable(3);
    }
}`;
  // Use Monaco API directly to avoid auto-complete mangling the code
  await page.evaluate((code) => {
    // eslint-disable-next-line
    const ed = window.monaco?.editor?.getEditors?.()[0];
    if (ed) ed.setValue(code);
  }, q1Solution);
  await page.waitForTimeout(500);
  await shoot(page, 'q1_code_written');

  // ── 4. Run Code ──────────────────────────────────────────────────────────
  log('step', 'Clicking Run Code');
  await page.locator('.btn-run-code').click();
  await page.waitForTimeout(3000);
  const stdout = await page.locator('.terminal-stdout').first().textContent().catch(() => '');
  const stderr = await page.locator('.terminal-stderr').first().textContent().catch(() => '');
  log('check', 'Run Code output', { stdout: stdout?.slice(0, 200), stderr: stderr?.slice(0, 200) });
  await shoot(page, 'q1_run_code_output');

  // ── 5. Run Tests for Q1A (printLowerTriangle mutation) ───────────────────
  log('step', 'Switching to Q1A variant and running tests');
  const q1aSolution = `public class Q1 {
    public static void printLowerTriangle(int n) {
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= n; j++) {
                if (j <= i) {
                    System.out.print(i * j + " ");
                }
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        printLowerTriangle(3);
    }
}`;
  await page.evaluate((code) => {
    // eslint-disable-next-line
    const ed = window.monaco?.editor?.getEditors?.()[0];
    if (ed) ed.setValue(code);
  }, q1aSolution);
  await page.waitForTimeout(500);
  await shoot(page, 'q1a_code_written');

  log('step', 'Clicking Tests button (runs all test cases)');
  // Tests button is 2nd child
  const testsBtn = page.locator('.editor-toolbar button').nth(1);
  await testsBtn.click();
  await page.waitForTimeout(8000); // test cases need time to compile+run
  await shoot(page, 'q1a_tests_run');

  const testCases = await page.locator('.test-case').count();
  log('check', `Test cases rendered: ${testCases}`);
  const passBadges = await page.locator('.tc-badge.pass').count();
  const failBadges = await page.locator('.tc-badge.fail').count();
  log('check', `Test results: ${passBadges} passed, ${failBadges} failed`);

  if (failBadges > 0) {
    const actuals = await page.locator('.tc-actual code').allTextContents();
    log('detail', 'Failed test actual outputs', actuals);
  }

  // ── 6. Visualize button ──────────────────────────────────────────────────
  log('step', 'Clicking Visualize button');
  const visBtn = page.locator('.editor-toolbar button.btn-visualize');
  await visBtn.click();
  await page.waitForTimeout(2000);
  await shoot(page, 'visualizer_opened');

  const iframe = await page.locator('.visualizer-frame').count();
  log(iframe > 0 ? 'pass' : 'fail', `Visualizer iframe present: ${iframe > 0}`);

  // ── 7. Info button ───────────────────────────────────────────────────────
  log('step', 'Clicking Info button');
  const infoBtn = page.locator('.editor-toolbar button').nth(3);
  await infoBtn.click();
  await page.waitForTimeout(500);
  await shoot(page, 'info_panel');

  const infoHeaders = await page.locator('.panel-info h4').allTextContents();
  log('check', `Info panel sections: ${JSON.stringify(infoHeaders)}`);

  // ── 8. Navigate to Q2 ────────────────────────────────────────────────────
  log('step', 'Navigating to Q2 (nested loop count)');
  await page.locator('.takehome-nav-item').nth(1).click();
  await page.waitForTimeout(1500);
  const q2Title = await page.locator('.takehome-header h3').textContent();
  log('check', `Loaded: ${q2Title}`);
  await shoot(page, 'q2_loaded');

  // ── 9. Reset button ──────────────────────────────────────────────────────
  log('step', 'Testing Reset button — write garbage, then reset');
  await page.evaluate(() => {
    // eslint-disable-next-line
    const ed = window.monaco?.editor?.getEditors?.()[0];
    if (ed) ed.setValue('// garbage');
  });
  await page.waitForTimeout(300);
  await page.locator('.btn-reset').click();
  await page.waitForTimeout(500);
  const resetContent = await page.locator('.view-lines').first().textContent().catch(() => '');
  log('check', `After reset, code starts with: "${resetContent?.slice(0, 60)}"`);
  await shoot(page, 'after_reset');

  // ── 10. Bounce through all 15 questions quickly ──────────────────────────
  log('step', 'Quickly clicking through all 15 questions');
  for (let i = 0; i < 15; i++) {
    await page.locator('.takehome-nav-item').nth(i).click();
    await page.waitForTimeout(400);
    const t = await page.locator('.takehome-header h3').textContent();
    log('nav', `Q${i + 1}: ${t}`);
  }
  await shoot(page, 'final_q15');

  await browser.close();

  // Write report
  const reportPath = path.join(REPORT_DIR, 'findings.json');
  fs.writeFileSync(reportPath, JSON.stringify(findings, null, 2));
  console.log(`\nReport: ${reportPath}`);
  console.log(`Screenshots: ${REPORT_DIR}`);

  const failures = findings.filter(f => f.level === 'fail');
  const passes = findings.filter(f => f.level === 'pass');
  console.log(`\n=== SUMMARY ===`);
  console.log(`Passes: ${passes.length}, Failures: ${failures.length}`);
  if (failures.length) {
    console.log('\nFAILURES:');
    failures.forEach(f => console.log(`  - ${f.message}`));
  }
})().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
