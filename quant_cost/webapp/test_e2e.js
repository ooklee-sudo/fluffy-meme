// End-to-end test of the Study 2 survey (browser + server). Run:  node quant_cost/webapp/test_e2e.js
// Needs Node and Playwright (npm i playwright; browsers installed).
const { chromium } = require("playwright");
const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const assert = require("assert");

const PORT = 8791;
const BASE = `http://127.0.0.1:${PORT}`;
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "s2data-"));
const server = spawn("python3", [path.join(__dirname, "server.py"), "--port", String(PORT), "--data-dir", dataDir], { stdio: "inherit" });
const pageErrors = [];

async function waitServer() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`${BASE}/api/ping`); if (r.ok) return; } catch (e) { /* retry */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("server did not start");
}
const waitStep = (page, s) => page.waitForFunction((x) => document.body.dataset.step === x, s, { timeout: 8000 });
const pick = (page, name, value) => page.check(`input[name="${name}"][value="${value}"]`);
const fillNum = (page, name, v) => page.fill(`input[name="${name}"]`, String(v));
const next = (page) => page.click("#next");

async function open(browser, pid, viewport) {
  const ctx = await browser.newContext(viewport ? { viewport } : {});
  const page = await ctx.newPage();
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  await page.goto(`${BASE}/?PROLIFIC_PID=${pid}&STUDY_ID=ST1&SESSION_ID=SE_${pid}`);
  return page;
}

async function runToEligibility(page, S) {
  await waitStep(page, "consent");
  await pick(page, "consent", 1); await next(page);
  await waitStep(page, "eligibility");
  for (const k of Object.keys(S)) await pick(page, k, S[k]);
  await next(page);
}

async function runFull(browser, pid, viewport) {
  const page = await open(browser, pid, viewport);
  await runToEligibility(page, { S1: 1, S2: 3, S3: 1, S4: 4, S5: 4, S6: 4, S7: 4, S8: 2 });
  await waitStep(page, "intro"); await next(page);
  await waitStep(page, "news");
  const newsText = await page.textContent("#app");
  await next(page);
  await waitStep(page, "general"); await fillNum(page, "GP", 5); await next(page);
  const seen = [];
  for (let k = 1; k <= 4; k++) {
    await waitStep(page, `scenario_${k}_a`);
    const txt = await page.textContent("#app");
    const lam = Number(/(\d+)% chance per year/.exec(txt)[1]);
    const smax = Number(/between 0 and (\d+)/.exec(txt)[1]);
    const perf2 = txt.includes("Cost per 1,000,000 correct answers");
    seen.push({ lam, smax, perf2 });
    await pick(page, "Q1", lam);
    await pick(page, "Q2", lam === 6 ? 1 : 2);
    await fillNum(page, "Q3", (lam === 6 ? 0.6 : 0.3) * smax);
    await next(page);
    await waitStep(page, `scenario_${k}_b`);
    await fillNum(page, "Q4", lam + 1); await pick(page, "Q5", 3); await next(page);
  }
  await waitStep(page, "attention1"); await pick(page, "A1", 5); await next(page);
  await waitStep(page, "covariates_1");
  await fillNum(page, "N1", 150); await fillNum(page, "N2", 100); await fillNum(page, "N3", 25);
  for (const e of ["E1", "E2", "E3"]) await pick(page, e, 2);
  await next(page);
  await waitStep(page, "covariates_2");
  for (let i = 1; i <= 4; i++) await pick(page, `PC_${i}`, 5);
  await pick(page, "R1", 6); await pick(page, "A2", 2); await next(page);
  await waitStep(page, "covariates_3");
  await pick(page, "P2", 4);
  await page.selectOption('select[name="P3_1"]', "3"); await page.selectOption('select[name="P3_2"]', "1"); await page.selectOption('select[name="P3_3"]', "2");
  await pick(page, "I1", 1); await pick(page, "I2", 5); await pick(page, "I3", 2); await next(page);
  await waitStep(page, "consistency"); await pick(page, "C1_S1", 1); await pick(page, "C1_S2", 3); await next(page);
  await waitStep(page, "demographics"); await next(page);
  await waitStep(page, "debrief"); await next(page);
  await waitStep(page, "done");
  await page.context().close();
  const file = path.join(dataDir, "participants", `${pid}__SE_${pid}.json`);
  return { saved: JSON.parse(fs.readFileSync(file, "utf-8")), seen, newsText };
}

(async () => {
  await waitServer();
  const browser = await chromium.launch();
  let failures = 0;
  const check = (name, fn) => { try { fn(); console.log("PASS", name); } catch (e) { failures++; console.log("FAIL", name, "-", e.message); } };

  // 1. full run (desktop) and a second one on a phone-sized screen
  const r1 = await runFull(browser, "P001");
  const r2 = await runFull(browser, "P002", { width: 375, height: 700 });
  for (const [label, r] of [["desktop", r1], ["mobile", r2]]) {
    const s = r.saved;
    check(`${label}: completed and eligible`, () => { assert.strictEqual(s.completed, true); assert.strictEqual(s.eligible, true); });
    check(`${label}: four scenarios saved with distinct cells`, () => { assert.deepStrictEqual(Object.keys(s.scenarios).sort(), ["C1", "C2", "C3", "C4"]); });
    check(`${label}: positions are a permutation of 1..4`, () => { assert.deepStrictEqual(Object.values(s.scenarios).map((x) => x.pos).sort(), [1, 2, 3, 4]); });
    check(`${label}: Latin square case matches version`, () => {
      const L = { V1: "ABCD", V2: "BCDA", V3: "CDAB", V4: "DABC" }[s.assignment.version];
      ["C1", "C2", "C3", "C4"].forEach((c, i) => assert.strictEqual(s.scenarios[c].caseCode, L[i]));
    });
    check(`${label}: lambda and format per cell`, () => {
      const exp = { C1: [2, 1], C2: [2, 2], C3: [6, 1], C4: [6, 2] };
      for (const c of Object.keys(exp)) { assert.strictEqual(s.scenarios[c].lam, exp[c][0]); assert.strictEqual(s.scenarios[c].perf, exp[c][1]); }
    });
    check(`${label}: news matches assignment`, () => {
      const t = r.newsText;
      assert.ok(s.assignment.news === "incident" ? t.includes("Customer records exposed") : t.includes("Companies weigh their options"));
    });
    check(`${label}: mediators recorded after choice`, () => { for (const c of Object.keys(s.scenarios)) { assert.ok(s.scenarios[c].Q4 !== undefined && s.scenarios[c].Q5 !== undefined); } });
    check(`${label}: answers present`, () => { for (const k of ["S1", "S8", "GP", "N1", "R1", "P2", "P3", "PC", "I2", "C1_S1"]) assert.ok(s.answers[k] !== undefined, k); });
    check(`${label}: no personal identifiers beyond the Prolific ID`, () => { assert.ok(!JSON.stringify(s).includes("@")); assert.ok(!("userAgent" in s)); });
  }

  // 2. screen-out (not involved in vendor decisions)
  { const page = await open(browser, "P003");
    await runToEligibility(page, { S1: 1, S2: 3, S3: 5, S4: 4, S5: 4, S6: 4, S7: 4, S8: 2 });
    await waitStep(page, "screenout"); await page.context().close();
    const s = JSON.parse(fs.readFileSync(path.join(dataDir, "participants", "P003__SE_P003.json"), "utf-8"));
    check("screen-out saved and flagged", () => { assert.strictEqual(s.screenedOut, true); assert.strictEqual(s.eligible, false); assert.ok(!s.assignment); }); }

  // 3. policy 'prohibited' (S8=1) is NOT a screen-out
  { const page = await open(browser, "P004");
    await runToEligibility(page, { S1: 1, S2: 3, S3: 1, S4: 4, S5: 4, S6: 4, S7: 4, S8: 1 });
    await waitStep(page, "intro");
    check("S8 = prohibited still continues to the study", () => {}); await page.context().close(); }

  // 4. decline consent
  { const page = await open(browser, "P005");
    await waitStep(page, "consent"); await pick(page, "consent", 2); await next(page); await waitStep(page, "declined");
    check("declining consent ends the survey", () => {}); await page.context().close(); }

  // 5. validation blocks an empty page
  { const page = await open(browser, "P006");
    await waitStep(page, "consent"); await next(page);
    const alert = await page.locator(".error").count();
    const step = await page.evaluate(() => document.body.dataset.step);
    check("empty consent page shows an error and stays", () => { assert.strictEqual(step, "consent"); assert.ok(alert >= 1); });
    await page.context().close(); }

  // 6. balanced server-side assignment over the 8 groups
  { const res = [];
    for (let i = 0; i < 16; i++) {
      const r = await fetch(`${BASE}/api/assign`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pid: `B${i}`, sessionId: "x" }) });
      res.push(await r.json());
    }
    // Earlier participants (P001, P002, P004) were assigned too, so check the server's totals: balanced within 1.
    const stored = JSON.parse(fs.readFileSync(path.join(dataDir, "assignments.json"), "utf-8")).counts;
    const vals8 = Object.values(stored);
    check("assignment counts cover the 8 groups", () => assert.strictEqual(vals8.length, 8));
    check("all 19 assignments are counted (3 earlier + 16 new)", () => assert.strictEqual(vals8.reduce((a, b) => a + b, 0), 19));
    check("groups are balanced within 1", () => assert.ok(Math.max(...vals8) - Math.min(...vals8) <= 1, JSON.stringify(stored)));
    const again = await (await fetch(`${BASE}/api/assign`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pid: "B0", sessionId: "x" }) })).json();
    check("repeat request returns the same assignment", () => assert.deepStrictEqual(again, res[0]));
    check("order is a permutation of 0..3", () => res.forEach((a) => assert.deepStrictEqual([...a.order].sort(), [0, 1, 2, 3]))); }

  // 7. no unexpected browser errors
  check("no JavaScript errors in the browser", () => assert.deepStrictEqual(pageErrors, []));

  await browser.close();

  // 8. export script
  const out = path.join(dataDir, "wide.csv");
  const ex = spawnSync("python3", [path.join(__dirname, "export_csv.py"), "--data-dir", dataDir, "--out", out], { encoding: "utf-8" });
  console.log(ex.stdout.trim(), ex.stderr.trim());
  const rows = fs.readFileSync(out, "utf-8").trim().split(/\r?\n/);
  const head = rows[0].split(","); const vals = rows[1].split(",");
  const get = (k) => vals[head.indexOf(k)];
  check("export: two completed participants", () => assert.strictEqual(rows.length - 1, 2));
  check("export: S = ln(0.6/0.3) = 0.693", () => assert.ok(Math.abs(Number(get("S")) - Math.log(2)) < 1e-6, get("S")));
  check("export: no exclusion flags for the clean runs", () => assert.strictEqual(get("excluded"), "0"));
  check("export: lnWTPL at lambda 2% equals ln(0.3 * smax / L) = ln(0.075)", () => {
    const k = head.findIndex((h, i) => h === "lnWTPL_C1"); assert.ok(Math.abs(Number(vals[k]) - Math.log(0.075)) < 1e-6, vals[k]);
  });

  server.kill();
  if (process.env.KEEP_DATA) console.log("data kept in", dataDir); else fs.rmSync(dataDir, { recursive: true, force: true });
  console.log(failures === 0 ? "ALL TESTS PASSED" : `${failures} TEST(S) FAILED`);
  process.exit(failures === 0 ? 0 : 1);
})().catch((e) => { console.error(e); server.kill(); process.exit(2); });
