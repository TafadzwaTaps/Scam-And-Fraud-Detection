"use strict";

// ── API base (auto-detects same origin or env override) ───────────────────
const API_BASE = window.API_BASE || "";

// ── Utility helpers ───────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function statusClass(status) {
  if (status === "high risk")   return "status-high-risk";
  if (status === "suspicious")  return "status-suspicious";
  return "status-safe";
}

function barClass(status) {
  if (status === "high risk")  return "risk-bar-high-risk";
  if (status === "suspicious") return "risk-bar-suspicious";
  return "risk-bar-safe";
}

function scoreColor(status) {
  if (status === "high risk")  return "#e02424";
  if (status === "suspicious") return "#d97706";
  return "#057a55";
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// ── Check form ────────────────────────────────────────────────────────────
const checkForm      = document.getElementById("check-form");
const checkSpinner   = document.getElementById("check-spinner");
const resultPanel    = document.getElementById("result-panel");
const checkAlert     = document.getElementById("check-alert");

checkForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  checkAlert.textContent = "";
  checkAlert.classList.add("d-none");
  resultPanel.style.display = "none";

  const type  = document.getElementById("check-type").value;
  const value = document.getElementById("check-value").value.trim();

  if (!value) {
    showAlert(checkAlert, "Please enter a value to check.");
    return;
  }

  checkSpinner.style.display = "flex";

  try {
    const res  = await fetch(`${API_BASE}/api/v1/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, value }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderResult(data, type, value);
  } catch (err) {
    showAlert(checkAlert, err.message);
  } finally {
    checkSpinner.style.display = "none";
  }
});

function renderResult(data, type, value) {
  const { risk_score, report_count, status, sample_reports, keyword_hits } = data;

  // Score display
  document.getElementById("res-score").textContent = risk_score.toFixed(0);
  document.getElementById("res-score").style.color  = scoreColor(status);

  // Status badge
  const badge = document.getElementById("res-status-badge");
  badge.textContent  = status.toUpperCase();
  badge.className    = `status-badge ${statusClass(status)}`;

  // Progress bar
  const bar = document.getElementById("res-bar");
  bar.style.width = `${risk_score}%`;
  bar.className   = `risk-bar ${barClass(status)}`;

  // Summary message
  const msgEl  = document.getElementById("res-message");
  const checked = `<strong>${escHtml(value)}</strong> (${escHtml(type)})`;
  if (status === "high risk") {
    msgEl.innerHTML = `⚠️ ${checked} shows strong indicators of fraud. Avoid interacting with it.`;
    msgEl.className = "alert alert-danger";
  } else if (status === "suspicious") {
    msgEl.innerHTML = `🔍 ${checked} has some suspicious signals. Proceed with caution.`;
    msgEl.className = "alert alert-warning";
  } else {
    msgEl.innerHTML = `✅ ${checked} appears to be clean based on available data.`;
    msgEl.className = "alert alert-success";
  }

  // Report count
  document.getElementById("res-report-count").textContent = report_count;

  // Keyword hits
  const kwWrap = document.getElementById("res-keywords-wrap");
  const kwEl   = document.getElementById("res-keywords");
  if (keyword_hits.length) {
    kwEl.innerHTML = keyword_hits.map(k => `<span class="kw-chip">${escHtml(k)}</span>`).join(" ");
    kwWrap.classList.remove("d-none");
  } else {
    kwWrap.classList.add("d-none");
  }

  // Sample reports
  const reportsEl   = document.getElementById("res-reports");
  const noReportsEl = document.getElementById("res-no-reports");
  reportsEl.innerHTML = "";
  if (sample_reports.length) {
    noReportsEl.classList.add("d-none");
    sample_reports.forEach(r => {
      const tags = r.tags.length
        ? r.tags.map(t => `<span class="report-tag">${escHtml(t)}</span>`).join(" ")
        : "";
      reportsEl.innerHTML += `
        <div class="report-card mb-2">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-1">
            <p class="mb-1 small">${escHtml(r.description)}</p>
            <span class="text-muted" style="font-size:.72rem;white-space:nowrap">${formatDate(r.created_at)}</span>
          </div>
          ${tags ? `<div class="mt-1">${tags}</div>` : ""}
        </div>`;
    });
  } else {
    noReportsEl.classList.remove("d-none");
  }

  resultPanel.style.display = "block";
  resultPanel.classList.remove("animate-in");
  void resultPanel.offsetWidth; // reflow
  resultPanel.classList.add("animate-in");
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Report form ────────────────────────────────────────────────────────────
const reportForm    = document.getElementById("report-form");
const reportSpinner = document.getElementById("report-spinner");
const reportAlert   = document.getElementById("report-alert");
const reportSuccess = document.getElementById("report-success");

reportForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  reportAlert.textContent = "";
  reportAlert.classList.add("d-none");
  reportSuccess.classList.add("d-none");

  const type        = document.getElementById("rep-type").value;
  const value       = document.getElementById("rep-value").value.trim();
  const description = document.getElementById("rep-description").value.trim();
  const tagsRaw     = document.getElementById("rep-tags").value.trim();
  const tags        = tagsRaw ? tagsRaw.split(",").map(t => t.trim()).filter(Boolean) : [];

  if (!value || !description) {
    showAlert(reportAlert, "Value and description are required.");
    return;
  }

  reportSpinner.style.display = "flex";

  try {
    const res = await fetch(`${API_BASE}/api/v1/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, value, description, tags }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    reportForm.reset();
    reportSuccess.classList.remove("d-none");
    reportSuccess.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    showAlert(reportAlert, err.message);
  } finally {
    reportSpinner.style.display = "none";
  }
});

// ── Recent flagged entities ───────────────────────────────────────────────
async function loadRecentEntities() {
  const tbody  = document.getElementById("recent-tbody");
  const errEl  = document.getElementById("recent-error");
  try {
    const res  = await fetch(`${API_BASE}/api/v1/entities?limit=10`);
    if (!res.ok) throw new Error("Failed to load");
    const list = await res.json();

    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No flagged entities yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(e => `
      <tr>
        <td><span class="badge bg-secondary">${escHtml(e.type)}</span></td>
        <td class="text-truncate" style="max-width:200px" title="${escHtml(e.value)}">${escHtml(e.value)}</td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="progress flex-grow-1" style="height:8px">
              <div class="progress-bar ${barClass(statusFromScore(e.risk_score))}" style="width:${e.risk_score}%"></div>
            </div>
            <span class="fw-bold" style="font-size:.85rem;min-width:2.5rem;color:${scoreColor(statusFromScore(e.risk_score))}">${e.risk_score.toFixed(0)}</span>
          </div>
        </td>
        <td>${e.report_count}</td>
        <td><span class="status-badge ${statusClass(statusFromScore(e.risk_score))}">${statusFromScore(e.risk_score)}</span></td>
      </tr>`
    ).join("");
  } catch {
    errEl.classList.remove("d-none");
  }
}

function statusFromScore(score) {
  if (score >= 60) return "high risk";
  if (score >= 30) return "suspicious";
  return "safe";
}

function showAlert(el, msg) {
  el.textContent = msg;
  el.classList.remove("d-none");
}

// ── Init ──────────────────────────────────────────────────────────────────
loadRecentEntities();
