const dashboardState = {
  token: null,
  catalog: null,
  runs: [],
  activeRun: null,
  currentIndex: -1,
  pollTimer: null,
  playTimer: null,
};

const laneOrder = ["source", "integration", "database", "api", "app"];
const packetX = { source: 0, integration: 265, database: 515, api: 760, app: 1005 };

const ui = {
  auth: document.getElementById("integration-auth"),
  refresh: document.getElementById("integration-refresh"),
  play: document.getElementById("integration-play"),
  prev: document.getElementById("integration-prev"),
  next: document.getElementById("integration-next"),
  form: document.getElementById("integration-form"),
  patientCount: document.getElementById("patient-count"),
  seed: document.getElementById("seed"),
  anchorDate: document.getElementById("anchor-date"),
  sourceOptions: document.getElementById("source-options"),
  sourceAll: document.getElementById("source-all"),
  runFeedback: document.getElementById("run-feedback"),
  runsList: document.getElementById("runs-list"),
  sourceLane: document.getElementById("source-lane"),
  packet: document.getElementById("flow-packet"),
  flowStats: document.getElementById("flow-stats"),
  currentEvent: document.getElementById("current-event"),
  payloadPreview: document.getElementById("payload-preview"),
  createdPatients: document.getElementById("created-patients"),
  databaseDeltas: document.getElementById("database-deltas"),
  apiChecks: document.getElementById("api-checks"),
  eventTimeline: document.getElementById("event-timeline"),
};

async function apiFetch(url, options = {}, auth = false) {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (auth && dashboardState.token) headers.set("Authorization", `Bearer ${dashboardState.token}`);
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  const type = response.headers.get("content-type") || "";
  return type.includes("application/json") ? response.json() : response.text();
}

function fmtDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
}

function fmtNumber(value) {
  return new Intl.NumberFormat("en-GB").format(Number(value || 0));
}

async function authenticate() {
  const token = await apiFetch("/api/v1/auth/token", {
    method: "POST",
    body: JSON.stringify({ username: "integration.viewer", password: "cancer360" }),
  });
  dashboardState.token = token.access_token;
  ui.auth.textContent = "Demo user ready";
}

async function loadCatalog() {
  dashboardState.catalog = await apiFetch("/api/v1/simulation/catalog");
  ui.patientCount.value = dashboardState.catalog.default_patient_count;
  ui.seed.value = dashboardState.catalog.recommended_seed;
  ui.sourceOptions.innerHTML = dashboardState.catalog.available_sources.map((source) => `
    <label class="source-option">
      <input type="checkbox" name="source-system" value="${source}" ${dashboardState.catalog.default_sources.includes(source) ? "checked" : ""}>
      <span>${source.toUpperCase()}</span>
    </label>
  `).join("");
}

function selectedSources() {
  return Array.from(document.querySelectorAll('input[name="source-system"]:checked')).map((item) => item.value);
}

async function loadRuns() {
  dashboardState.runs = await apiFetch("/api/v1/simulation/runs");
  renderRuns();
  if (!dashboardState.activeRun && dashboardState.runs.length) {
    await selectRun(dashboardState.runs[0].run_id);
  }
}

function renderRuns() {
  if (!dashboardState.runs.length) {
    ui.runsList.innerHTML = `<div class="empty-state">No simulation runs available yet.</div>`;
    return;
  }
  ui.runsList.innerHTML = dashboardState.runs.map((run) => `
    <button type="button" class="run-card ${dashboardState.activeRun?.run_id === run.run_id ? "active" : ""}" data-run-id="${run.run_id}">
      <div class="run-card-topline">
        <strong>Run ${run.run_id}</strong>
        <span class="pill ${run.status === "completed" ? "green" : run.status === "failed" ? "red" : "amber"}">${run.status}</span>
      </div>
      <div class="meta">${fmtNumber(run.patient_count)} patients | ${fmtNumber(run.total_events)} events</div>
      <div class="meta">${run.source_systems.join(", ")}</div>
    </button>
  `).join("");
  ui.runsList.querySelectorAll(".run-card").forEach((button) => button.addEventListener("click", () => selectRun(button.dataset.runId)));
}

async function selectRun(runId) {
  stopPlayback();
  stopPolling();
  dashboardState.activeRun = await apiFetch(`/api/v1/simulation/runs/${runId}`);
  dashboardState.currentIndex = dashboardState.activeRun.stream.length ? 0 : -1;
  renderRuns();
  renderDashboard();
  if (dashboardState.activeRun.status === "running" || dashboardState.activeRun.status === "queued") {
    dashboardState.pollTimer = window.setInterval(async () => {
      dashboardState.activeRun = await apiFetch(`/api/v1/simulation/runs/${runId}`);
      dashboardState.currentIndex = Math.max(dashboardState.activeRun.stream.length - 1, 0);
      renderDashboard();
      if (!["running", "queued"].includes(dashboardState.activeRun.status)) {
        stopPolling();
      }
    }, 2000);
  }
}

function currentEvent() {
  if (!dashboardState.activeRun || dashboardState.currentIndex < 0) return null;
  return dashboardState.activeRun.stream[dashboardState.currentIndex] || null;
}

function laneCounts() {
  const counts = { source: 0, integration: 0, database: 0, api: 0, app: 0 };
  if (!dashboardState.activeRun) return counts;
  dashboardState.activeRun.stream.forEach((item, index) => {
    if (index <= dashboardState.currentIndex) counts[item.layer] += 1;
  });
  return counts;
}

function renderDashboard() {
  renderSourceLane();
  renderFlowStats();
  renderCurrentEvent();
  renderCreatedPatients();
  renderDatabaseDeltas();
  renderApiChecks();
  renderEventTimeline();
}

function renderSourceLane() {
  const run = dashboardState.activeRun;
  const sourceCounts = run?.source_event_counts || {};
  const active = currentEvent();
  const sources = dashboardState.catalog?.available_sources || [];
  ui.sourceLane.innerHTML = sources.map((source) => `
    <div class="source-node ${active?.source_system === source ? "active" : ""}">
      <div class="run-card-topline">
        <strong>${source.toUpperCase()}</strong>
        <span class="pill blue">${fmtNumber(sourceCounts[source] || 0)}</span>
      </div>
      <div class="meta">${active?.source_system === source ? "Current emitting source" : "Waiting or already processed"}</div>
    </div>
  `).join("");

  document.querySelectorAll(".flow-stage").forEach((stage) => {
    stage.classList.toggle("active", active?.layer === stage.dataset.stage);
  });
  if (active) {
    ui.packet.style.transform = `translateX(${packetX[active.layer] || 0}px)`;
  } else {
    ui.packet.style.transform = "translateX(0)";
  }
}

function renderFlowStats() {
  const run = dashboardState.activeRun;
  if (!run) {
    ui.flowStats.innerHTML = `<div class="empty-state">Choose a run to populate the flow board.</div>`;
    return;
  }
  const counts = laneCounts();
  const cards = [
    ["Source events", counts.source],
    ["Mirth/TIE steps", counts.integration],
    ["Database writes", counts.database],
    ["API confirmations", counts.api],
    ["App readbacks", counts.app],
  ];
  ui.flowStats.innerHTML = cards.map(([label, value]) => `
    <div class="stat-card">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${fmtNumber(value)}</div>
    </div>
  `).join("");
}

function renderCurrentEvent() {
  const event = currentEvent();
  if (!event) {
    ui.currentEvent.innerHTML = `Select a run and press play to start the animated flow.`;
    ui.payloadPreview.textContent = "Payload previews will appear here.";
    return;
  }
  ui.currentEvent.classList.remove("empty-state");
  ui.currentEvent.innerHTML = `
    <div class="event-topline">
      <span class="pill blue">${event.layer}</span>
      <span class="meta">${fmtDate(event.timestamp)}</span>
    </div>
    <h3>${event.title}</h3>
    <div class="meta">${event.component} | ${event.file_name || event.message_type || "Synthetic event"}</div>
    <p>${event.detail}</p>
    <div class="meta">Impacts: ${(event.impact_tables || []).join(", ") || "Narration / orchestration step"}</div>
  `;
  ui.payloadPreview.textContent = event.payload_preview || "No payload preview is available for this event.";
}

function renderCreatedPatients() {
  const patients = dashboardState.activeRun?.created_patients || [];
  if (!patients.length) {
    ui.createdPatients.innerHTML = `<div class="empty-state">Created patients will appear here after a run starts.</div>`;
    return;
  }
  ui.createdPatients.innerHTML = patients.slice(0, 8).map((patient) => `
    <div class="created-patient-card">
      <strong>${patient.patient_name}</strong>
      <div class="meta">${patient.nhs_number} | ${patient.scenario}</div>
      <div class="meta"><a href="/app?nhs=${patient.nhs_number}">Open in main app</a></div>
    </div>
  `).join("");
}

function renderDatabaseDeltas() {
  const deltas = dashboardState.activeRun?.database_deltas || [];
  if (!deltas.length) {
    ui.databaseDeltas.innerHTML = `<div class="empty-state">Database deltas will appear when a run completes.</div>`;
    return;
  }
  ui.databaseDeltas.innerHTML = deltas.filter((item) => item.delta > 0).map((item) => `
    <div class="stat-card">
      <div class="stat-label">${item.table_name}</div>
      <div class="stat-value">+${fmtNumber(item.delta)}</div>
      <div class="meta">${fmtNumber(item.before_count)} to ${fmtNumber(item.after_count)}</div>
    </div>
  `).join("");
}

function renderApiChecks() {
  const checks = dashboardState.activeRun?.api_checks || [];
  if (!checks.length) {
    ui.apiChecks.innerHTML = `<div class="empty-state">API checks will appear after a run completes.</div>`;
    return;
  }
  ui.apiChecks.innerHTML = checks.map((check) => `
    <div class="api-check">
      <div class="event-topline">
        <strong>${check.name}</strong>
        <span class="pill ${check.status === "success" ? "green" : "red"}">${check.status}</span>
      </div>
      <div class="meta">${check.detail}</div>
    </div>
  `).join("");
}

function renderEventTimeline() {
  const stream = dashboardState.activeRun?.stream || [];
  if (!stream.length) {
    ui.eventTimeline.innerHTML = `<div class="empty-state">The event timeline will populate once a run is selected.</div>`;
    return;
  }
  ui.eventTimeline.innerHTML = stream.map((event, index) => `
    <div class="timeline-row ${index === dashboardState.currentIndex ? "active" : ""}" data-index="${index}">
      <div class="timeline-topline">
        <strong>${event.title}</strong>
        <span class="pill blue">${event.layer}</span>
      </div>
      <div class="meta">${event.component} | ${event.file_name || event.message_type || "Synthetic event"}</div>
      <div class="meta">${(event.impact_tables || []).join(", ") || "No direct table impact"}</div>
    </div>
  `).join("");
  ui.eventTimeline.querySelectorAll(".timeline-row").forEach((row) => row.addEventListener("click", () => {
    dashboardState.currentIndex = Number(row.dataset.index);
    renderDashboard();
  }));
}

function step(delta) {
  if (!dashboardState.activeRun) return;
  const max = dashboardState.activeRun.stream.length - 1;
  dashboardState.currentIndex = Math.max(0, Math.min(max, dashboardState.currentIndex + delta));
  renderDashboard();
}

function stopPlayback() {
  if (dashboardState.playTimer) {
    window.clearInterval(dashboardState.playTimer);
    dashboardState.playTimer = null;
  }
  ui.play.textContent = "Play Flow";
}

function stopPolling() {
  if (dashboardState.pollTimer) {
    window.clearInterval(dashboardState.pollTimer);
    dashboardState.pollTimer = null;
  }
}

function togglePlayback() {
  if (!dashboardState.activeRun || dashboardState.activeRun.stream.length < 2) return;
  if (dashboardState.playTimer) {
    stopPlayback();
    return;
  }
  ui.play.textContent = "Pause";
  dashboardState.playTimer = window.setInterval(() => {
    if (!dashboardState.activeRun) return;
    if (dashboardState.currentIndex >= dashboardState.activeRun.stream.length - 1) {
      stopPlayback();
      return;
    }
    dashboardState.currentIndex += 1;
    renderDashboard();
  }, 900);
}

async function startRun(event) {
  event.preventDefault();
  const sources = selectedSources();
  if (!sources.length) {
    ui.runFeedback.textContent = "Select at least one source system.";
    return;
  }
  ui.runFeedback.textContent = "Starting simulation run...";
  const run = await apiFetch("/api/v1/simulation/runs", {
    method: "POST",
    body: JSON.stringify({
      patient_count: Number(ui.patientCount.value),
      seed: Number(ui.seed.value),
      anchor_date: ui.anchorDate.value || null,
      source_systems: sources,
    }),
  });
  ui.runFeedback.textContent = `Run ${run.run_id} queued. The flow board will now follow it.`;
  await loadRuns();
  await selectRun(run.run_id);
}

function bindEvents() {
  ui.form.addEventListener("submit", startRun);
  ui.refresh.addEventListener("click", loadRuns);
  ui.play.addEventListener("click", togglePlayback);
  ui.prev.addEventListener("click", () => step(-1));
  ui.next.addEventListener("click", () => step(1));
  ui.sourceAll.addEventListener("click", () => {
    document.querySelectorAll('input[name="source-system"]').forEach((item) => {
      item.checked = true;
    });
  });
}

async function init() {
  bindEvents();
  await authenticate();
  await loadCatalog();
  await loadRuns();
}

init().catch((error) => {
  ui.auth.textContent = `Integration dashboard failed: ${error.message}`;
});
