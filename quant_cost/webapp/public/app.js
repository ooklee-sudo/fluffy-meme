// Study 2 survey: flow, randomization, validation, saving. Plain JavaScript, no build step.
(function () {
  "use strict";

  var C = CONTENT;
  var CFG = (typeof APP_CONFIG !== "undefined") ? APP_CONFIG : {};
  var app = document.getElementById("app");
  var params = new URLSearchParams(window.location.search);

  function rid() { return Math.random().toString(36).slice(2, 10); }
  var pid = params.get("PROLIFIC_PID") || ("TEST-" + rid());
  var state = {
    pid: pid,
    studyId: params.get("STUDY_ID") || "",
    sessionId: params.get("SESSION_ID") || ("S" + rid()),
    startedAt: new Date().toISOString(),
    assignment: null, assignmentSource: null,
    eligible: null, declined: false, screenedOut: false,
    answers: {}, scenarios: {}, timing: {},
    completed: false, appVersion: "study2-webapp-1"
  };
  var apiOk = false;
  var pageStart = 0;
  var totalPages = 22;
  var pageNo = 0;

  // ---------------------------------------------------------------- utilities
  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "html") e.innerHTML = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(c); });
    return e;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function fmtErr(e) { return h("div", { "class": "error", role: "alert", text: e }); }

  function save() {
    if (!apiOk) return Promise.resolve(false);
    var body = JSON.stringify(Object.assign({ updatedAt: new Date().toISOString() }, state));
    return fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: body })
      .then(function (r) { return r.ok; }).catch(function () { return false; });
  }

  // ---------------------------------------------------------------- form fields
  // Each field: { node, get(), validate() -> error string | null, id }
  function mc(o) {
    var vals = o.values || o.options.map(function (_, i) { return i + 1; });
    var idx = vals.map(function (_, i) { return i; });
    if (o.randomize) idx = shuffle(idx);
    var box = h("div", { "class": "q" });
    box.appendChild(h("div", { "class": "label", html: o.label }));
    if (o.hint) box.appendChild(h("div", { "class": "hint", text: o.hint }));
    var wrap = h("div", { "class": o.horizontal ? "scale" : "" });
    idx.forEach(function (i) {
      var inp = h("input", { type: "radio", name: o.id, value: String(vals[i]) });
      wrap.appendChild(h("label", { "class": "opt" }, [inp, h("span", { text: o.options[i] })]));
    });
    box.appendChild(wrap);
    var order = idx.map(function (i) { return vals[i]; });
    return {
      id: o.id, node: box, order: order,
      get: function () {
        var c = box.querySelector("input:checked");
        if (!c) return null;
        var v = c.value;
        return isNaN(Number(v)) ? v : Number(v);
      },
      validate: function () { return (o.required === false || this.get() !== null) ? null : "Please answer every question on this page."; }
    };
  }

  function num(o) {
    var box = h("div", { "class": "q" });
    box.appendChild(h("div", { "class": "label", html: o.label }));
    if (o.hint) box.appendChild(h("div", { "class": "hint", text: o.hint }));
    var inp = h("input", { type: "number", name: o.id, step: "any", inputmode: "decimal", autocomplete: "off" });
    box.appendChild(inp);
    return {
      id: o.id, node: box,
      get: function () { var v = inp.value.trim(); return v === "" ? null : Number(v); },
      validate: function () {
        var v = this.get();
        if (v === null || !isFinite(v)) return o.required === false ? null : "Please answer every question on this page.";
        if (o.min !== undefined && v < o.min) return "Please enter a number of at least " + o.min + ".";
        if (o.max !== undefined && v > o.max) return "Please enter a number no larger than " + o.max + ".";
        return null;
      }
    };
  }

  // A set of statements rated on one scale. Rendered as one labelled radio row per statement
  // (a wide table does not fit on a phone).
  function matrix(o) {
    var box = h("div", { "class": "q" });
    box.appendChild(h("div", { "class": "label", text: o.label }));
    o.rows.forEach(function (r, i) {
      var item = h("div", { "class": "stmt" }, [h("div", { "class": "stmt-text", text: r })]);
      var wrap = h("div", { "class": "scale" });
      o.cols.forEach(function (c, j) {
        var inp = h("input", { type: "radio", name: o.id + "_" + (i + 1), value: String(j + 1) });
        wrap.appendChild(h("label", { "class": "opt" }, [inp, h("span", { text: c })]));
      });
      item.appendChild(wrap);
      box.appendChild(item);
    });
    return {
      id: o.id, node: box,
      get: function () {
        return o.rows.map(function (_, i) {
          var c = box.querySelector("input[name='" + o.id + "_" + (i + 1) + "']:checked");
          return c ? Number(c.value) : null;
        });
      },
      validate: function () { return this.get().indexOf(null) === -1 ? null : "Please answer every question on this page."; }
    };
  }

  function rank(o) {
    var box = h("div", { "class": "q" });
    box.appendChild(h("div", { "class": "label", text: o.label }));
    var sels = [];
    ["1st (most important)", "2nd", "3rd"].forEach(function (lab, k) {
      var s = h("select", { name: o.id + "_" + (k + 1) }, [h("option", { value: "", text: "Select..." })]);
      o.factors.forEach(function (f, i) { s.appendChild(h("option", { value: String(i + 1), text: f })); });
      sels.push(s);
      box.appendChild(h("div", { "class": "opt" }, [h("span", { text: lab + ":" }), s]));
    });
    return {
      id: o.id, node: box,
      get: function () { return sels.map(function (s) { return s.value === "" ? null : Number(s.value); }); },
      validate: function () {
        var v = this.get();
        if (v.indexOf(null) !== -1) return "Please choose three factors and rank them.";
        if (v[0] === v[1] || v[0] === v[2] || v[1] === v[2]) return "Please choose three different factors.";
        return null;
      }
    };
  }

  // ---------------------------------------------------------------- page rendering
  function page(step, opts) {
    pageNo += 1;
    document.body.dataset.step = step;
    window.scrollTo(0, 0);
    app.innerHTML = "";
    var card = h("div", { "class": "card" });
    card.appendChild(h("div", { "class": "progress", text: "Page " + Math.min(pageNo, totalPages) + " of about " + totalPages }));
    if (opts.html) card.appendChild(h("div", { html: opts.html }));
    var fields = opts.fields || [];
    fields.forEach(function (f) { card.appendChild(f.node); });
    var err = h("div");
    card.appendChild(err);
    var btn = h("button", { "class": "primary", id: "next", type: "button", text: opts.button || "Continue" });
    card.appendChild(btn);
    app.appendChild(card);
    pageStart = performance.now();
    btn.addEventListener("click", function () {
      err.innerHTML = "";
      for (var i = 0; i < fields.length; i++) {
        var e = fields[i].validate();
        if (e) { err.appendChild(fmtErr(e)); return; }
      }
      btn.disabled = true;
      state.timing[step] = (state.timing[step] || 0) + Math.round(performance.now() - pageStart);
      opts.next(fields);
    });
  }

  // ---------------------------------------------------------------- scenario text
  function money(n) { return Number(n).toLocaleString("en-US"); }

  function scenarioHTML(n, cell, cs) {
    var perfRows = "<tr><td>Accuracy</td><td>" + cs.accL + "%</td><td>" + cs.accA + "%</td></tr>";
    if (cell.perf === 2) {
      perfRows += "<tr><td>Cost per 1,000,000 correct answers (local model: including hardware and electricity)</td><td>$" + cs.costL + "</td><td>$" + cs.costA + "</td></tr>";
    }
    return "<h3>Scenario " + n + " of 4: " + cs.title + "</h3>" +
      "<p>Your company wants to use AI to " + cs.task + ". " + cs.data + " For the coming year, you must choose between the two options described below.</p>" +
      "<p><b>Key figures</b> (per year, in thousands of dollars)</p><ul>" +
      "<li><b>Running cost.</b> The local model is cheaper to run than the cloud API by <b>$" + money(cs.B) + "k</b> per year.</li>" +
      "<li><b>Errors.</b> The local model is somewhat less accurate than the cloud API. Its additional errors cost the company <b>$" + money(cs.E) + "k</b> per year.</li>" +
      "<li><b>Data exposure with the cloud API.</b> Your company's risk team estimates that there is a <b>" + cell.lam + "% chance per year</b> that personal data is exposed through the vendor. The estimate is based on industry-wide data covering all reported incidents. If an exposure happens, it would cost the company <b>$" + money(cs.L) + "k</b> (fines, notification costs, and lost business).</li>" +
      "<li><b>Data exposure with the local model.</b> All data stay in-house, so there is no exposure risk from a vendor.</li></ul>" +
      "<p>The cost figures above already take into account the performance difference shown below.</p>" +
      "<table class='perf'><tr><th></th><th>Local model</th><th>Cloud API</th></tr>" + perfRows + "</table>";
  }

  // ---------------------------------------------------------------- flow
  function start() {
    fetch("/api/ping").then(function (r) { apiOk = r.ok; }).catch(function () { apiOk = false; }).then(stepConsent);
  }

  function stepConsent() {
    var box = mc({ id: "consent", label: C.consentLabel, options: ["I agree to take part.", "I do not agree."], required: true });
    page("consent", {
      html: C.consentHTML, fields: [box],
      next: function () {
        if (box.get() === 2) {
          state.declined = true; state.answers.consent = 2;
          return save().then(function () { endScreen(C.declineMessage, CFG.screenoutUrl); });
        }
        state.answers.consent = 1;
        stepEligibility();
      }
    });
  }

  function isEligible(a) {
    return a.S1 <= 6 && a.S3 <= 3 && (a.S2 >= 3 || a.S4 >= 3 || a.S3 <= 2) && a.S6 >= 2 && a.S5 >= 2;
  }

  function stepEligibility() {
    var fields = C.eligibility.map(function (q) { return mc({ id: q.id, label: q.text, options: q.options, required: true }); });
    page("eligibility", {
      html: "<h2>A few questions about you</h2>", fields: fields,
      next: function () {
        var a = {};
        fields.forEach(function (f) { a[f.id] = f.get(); state.answers[f.id] = f.get(); });
        state.eligible = isEligible(a);
        if (!state.eligible) {
          state.screenedOut = true;
          return save().then(function () { endScreen(C.screenoutMessage, CFG.screenoutUrl); });
        }
        assign().then(function () { save(); stepIntro(); });
      }
    });
  }

  function assign() {
    var local = function () {
      state.assignment = {
        news: Math.random() < 0.5 ? "incident" : "control",
        version: "V" + (1 + Math.floor(Math.random() * 4)),
        order: shuffle([0, 1, 2, 3])
      };
      state.assignmentSource = "client";
    };
    if (!apiOk) { local(); return Promise.resolve(); }
    return fetch("/api/assign", { method: "POST", headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ pid: state.pid, sessionId: state.sessionId }) })
      .then(function (r) { if (!r.ok) throw new Error("assign"); return r.json(); })
      .then(function (j) { state.assignment = j; state.assignmentSource = "server"; })
      .catch(local);
  }

  function stepIntro() {
    page("intro", { html: C.introHTML, fields: [], next: stepNews });
  }

  function stepNews() {
    page("news", { html: C.news[state.assignment.news], fields: [], next: stepGeneral });
  }

  function stepGeneral() {
    var f = num({ id: "GP", label: C.generalProbability, min: 0, max: 100 });
    page("general", { fields: [f], next: function () { state.answers.GP = f.get(); save(); stepScenario(0); } });
  }

  function stepScenario(k) {
    if (k > 3) return stepA1();
    var a = state.assignment;
    var cellIdx = a.order[k];
    var cell = C.cells[cellIdx];
    var caseCode = C.latin[a.version].charAt(cellIdx);
    var cs = C.cases[caseCode];
    var smax = cs.L / 4;
    var q1 = mc({ id: "Q1", label: C.q.q1, options: C.q.q1opts.map(function (x) { return x + "%"; }), values: C.q.q1opts, randomize: true });
    var q2 = mc({ id: "Q2", label: C.q.q2, options: C.q.q2opts, values: [1, 2], randomize: true });
    var q3 = num({ id: "Q3", label: C.q.q3, hint: C.q.q3hint.replace("{smax}", String(smax)), min: 0 });
    page("scenario_" + (k + 1) + "_a", {
      html: scenarioHTML(k + 1, cell, cs), fields: [q1, q2, q3],
      next: function () {
        var rec = state.scenarios[cell.id] = {
          pos: k + 1, cell: cell.id, caseCode: caseCode, lam: cell.lam, perf: cell.perf,
          B: cs.B, E: cs.E, L: cs.L, smax: smax,
          Q1: q1.get(), Q1_correct: q1.get() === cell.lam, Q1_order: q1.order,
          Q2: q2.get(), Q2_choice: q2.get() === 1 ? "local" : "api", Q2_order: q2.order,
          Q3_raw: q3.get(), t_part1_ms: state.timing["scenario_" + (k + 1) + "_a"]
        };
        save();
        // Mediators are asked after the choice and the willingness-to-pay answer (preregistered order).
        var q4 = num({ id: "Q4", label: C.q.q4, min: 0, max: 100 });
        var q5 = mc({ id: "Q5", label: C.q.q5, options: C.q.q5opts, horizontal: true });
        page("scenario_" + (k + 1) + "_b", {
          html: scenarioHTML(k + 1, cell, cs), fields: [q4, q5],
          next: function () {
            rec.Q4 = q4.get(); rec.Q5 = q5.get();
            rec.t_part2_ms = state.timing["scenario_" + (k + 1) + "_b"];
            save(); stepScenario(k + 1);
          }
        });
      }
    });
  }

  function stepA1() {
    var f = mc({ id: "A1", label: C.a1.text, options: C.a1.options, horizontal: true });
    page("attention1", {
      fields: [f],
      next: function () { state.answers.A1 = f.get(); state.answers.A1_correct = f.get() === C.a1.correct; save(); stepCov1(); }
    });
  }

  function stepCov1() {
    var fields = [];
    C.numeracy.forEach(function (q) { fields.push(num({ id: q.id, label: q.text })); });
    C.experience.forEach(function (q) { fields.push(mc({ id: q.id, label: q.text, options: q.options })); });
    page("covariates_1", {
      html: "<h2>About you and your work</h2>", fields: fields,
      next: function () { fields.forEach(function (f) { state.answers[f.id] = f.get(); }); save(); stepCov2(); }
    });
  }

  function stepCov2() {
    var pc = matrix({ id: C.privacyConcern.id, label: C.privacyConcern.text, rows: C.privacyConcern.rows, cols: C.privacyConcern.cols });
    var r1 = mc({ id: C.risk.id, label: C.risk.text, options: C.risk.options, horizontal: true });
    var a2 = mc({ id: "A2", label: C.a2.text, options: C.a2.options, horizontal: true });
    page("covariates_2", {
      fields: [pc, r1, a2],
      next: function () {
        state.answers.PC = pc.get(); state.answers.R1 = r1.get(); state.answers.A2 = a2.get();
        state.answers.A2_correct = a2.get() === C.a2.correct; save(); stepCov3();
      }
    });
  }

  function stepCov3() {
    var d = mc({ id: C.discretion.id, label: C.discretion.text, options: C.discretion.options, horizontal: true });
    var rk = rank({ id: C.ranking.id, label: C.ranking.text, factors: C.ranking.factors });
    var inds = C.industry.map(function (q) { return mc({ id: q.id, label: q.text, options: q.options, horizontal: q.options.length <= 7 }); });
    var fields = [d, rk].concat(inds);
    page("covariates_3", {
      fields: fields,
      next: function () {
        state.answers.P2 = d.get(); state.answers.P3 = rk.get();
        inds.forEach(function (f) { state.answers[f.id] = f.get(); });
        save(); stepC1();
      }
    });
  }

  function stepC1() {
    var s1 = mc({ id: "C1_S1", label: "Main job function", options: C.eligibility[0].options });
    var s2 = mc({ id: "C1_S2", label: "Level", options: C.eligibility[1].options });
    page("consistency", {
      html: "<p>" + C.c1Intro + "</p>", fields: [s1, s2],
      next: function () { state.answers.C1_S1 = s1.get(); state.answers.C1_S2 = s2.get(); save(); stepDemo(); }
    });
  }

  function stepDemo() {
    var fields = C.demographics.map(function (q) { return mc({ id: q.id, label: q.text, options: q.options, required: false }); });
    var country = h("div", { "class": "q" }, [h("div", { "class": "label", text: "In which country do you live? (optional)" }),
                                                h("input", { type: "text", name: "COUNTRY", maxlength: "60", autocomplete: "off" })]);
    page("demographics", {
      html: "<h2>Last questions</h2>", fields: fields.concat([{ node: country, validate: function () { return null; } }]),
      next: function () {
        fields.forEach(function (f) { state.answers[f.id] = f.get(); });
        state.answers.COUNTRY = country.querySelector("input").value.trim().slice(0, 60);
        save(); stepDebrief();
      }
    });
  }

  function stepDebrief() {
    page("debrief", {
      html: C.debriefHTML, fields: [], button: "Finish",
      next: function () {
        state.completed = true;
        state.finishedAt = new Date().toISOString();
        save().then(function (ok) { finish(ok); });
      }
    });
  }

  function finish(saved) {
    document.body.dataset.step = "done";
    app.innerHTML = "";
    var card = h("div", { "class": "card" });
    card.appendChild(h("h2", { text: "Thank you!" }));
    if (!apiOk || !saved) {
      card.appendChild(h("p", { "class": "error", text: apiOk
        ? "Your answers could not be saved. Please do not close this page, and contact the researcher using the e-mail address given in the information at the start of the survey."
        : "Test mode: no server is connected, so nothing was saved." }));
      var blob = new Blob([JSON.stringify(state, null, 1)], { type: "application/json" });
      var a = h("a", { href: URL.createObjectURL(blob), download: "study2_" + state.pid + ".json", text: "Download your responses (JSON)" });
      card.appendChild(h("p", null, [a]));
    }
    if (CFG.completeUrl) {
      card.appendChild(h("p", { text: "Please click the button below to return to Prolific and confirm that you have completed the study." }));
      var go = h("button", { "class": "primary", id: "complete", type: "button", text: "Return to Prolific" });
      go.addEventListener("click", function () { window.location.href = CFG.completeUrl; });
      card.appendChild(go);
      if (CFG.redirectAfterSeconds > 0) setTimeout(function () { window.location.href = CFG.completeUrl; }, CFG.redirectAfterSeconds * 1000);
    } else {
      card.appendChild(h("p", { "class": "small", text: "No completion link is configured (test mode)." }));
    }
    app.appendChild(card);
  }

  function endScreen(message, url) {
    document.body.dataset.step = state.declined ? "declined" : "screenout";
    app.innerHTML = "";
    var card = h("div", { "class": "card" }, [h("p", { text: message })]);
    if (url) {
      var go = h("button", { "class": "primary", type: "button", text: "Continue" });
      go.addEventListener("click", function () { window.location.href = url; });
      card.appendChild(go);
    }
    app.appendChild(card);
  }

  start();
})();
