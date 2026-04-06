const state = {
  token: null,
  catalog: null,
  activeRunId: null,
  polling: null,
};

const elements = {
  form: document.getElementById("run-form"),
  patientCount: document.getElementById("patient-count"),
  seed: document.getElementById("seed"),
  anchorDate: document.getElementById("anchor-date"),
  sourceOptions: document.getElementById("source-options"),
  selectAllSources: document.getElementById("select-all-sources"),
  refreshRuns: document.getElementById("refresh-runs"),
  feedback: document.getElementById("run-feedback"),
  pipeline: document.getElementById("pipeline-lanes"),
  runs: document.getElementById("runs-list"),
  patients: document.getElementById("patients-list"),
  stream: document.getElementById("stream-list"),
  database: document.getElementById("database-deltas"),
  apiChecks: document.getElementById("api-checks"),
  patientView: document.getElementById("patient-view"),
};

const laneCopy = {
  source: "Synthetic payloads are generated from the selected source systems.",
  integration: "The native TIE processes the payloads. In production this is the same lane Mirth would occupy.",
  database: "The canonical data model is updated through upserts into the Cancer 360 schema.",
  api: "FastAPI reads the updated data and exposes it back through patient, PTL, and integration endpoints.",
  app: "This operator console and the patient views make the replay understandable and observable.",
};

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

async function authenticate() {
  try {
    const token = await apiFetch("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({ username: "studio.operator", password: "cancer360" }),
    });
    state.token = token.access_token;
  } catch (error) {
    console.warn("Could not acquire demo token for patient inspection.", error);
  }
}

async function loadCatalog() {
  state.catalog = await apiFetch("/api/v1/simulation/catalog");
  elements.patientCount.value = state.catalog.default_patient_count;
  elements.seed.value = state.catalog.recommended_seed;
  renderSourceOptions();
}

function renderSourceOptions() {
  elements.sourceOptions.innerHTML = "";
  state.catalog.available_sources.forEach((source) => {
    const label = document.createElement("label");
    label.className = "source-option";
    label.innerHTML = `
      <input type="checkbox" name="source-system" value="${source}" ${state.catalog.default_sources.includes(source) ? "checked" : ""}>
      <span>${source.toUpperCase()}</span>
    `;
    elements.sourceOptions.appendChild(label);
  });
}

async function loadRuns() {
  const runs = await apiFetch("/api/v1/simulation/runs");
  renderRuns(runs);
  if (!state.activeRunId && runs.length) {
    state.activeRunId = runs[0].run_id;
    await loadRun(state.activeRunId);
  }
}

function renderRuns(runs) {
  if (!runs.length) {
    elements.runs.innerHTML = `<div class="empty-state">No runs yet. Start a simulation to populate the studio.</div>`;
    return;
  }

  elements.runs.innerHTML = "";
  runs.forEach((run) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `run-card ghost-button ${run.run_id === state.activeRunId ? "is-active" : ""}`;
    button.innerHTML = `
      <div class="run-topline">
        <h3 class="run-title">Run ${run.run_id}</h3>
        <span class="status-badge ${run.status}">${run.status}</span>
      </div>
      <p class="run-meta">
        ${run.patient_count} patients, ${run.total_events} events, ${run.processed_events} processed.
      </p>
      <p class="run-meta">
        Sources: ${run.source_systems.join(", ")}
      </p>
    `;
    button.addEventListener("click", async () => {
      state.activeRunId = run.run_id;
      renderRuns(runs);
      await loadRun(run.run_id);
    });
    elements.runs.appendChild(button);
  });
}

function selectedSources() {
  return Array.from(document.querySelectorAll('input[name="source-system"]:checked')).map((input) => input.value);
}

async function startRun(event) {
  event.preventDefault();
  const sources = selectedSources();
  if (!sources.length) {
    elements.feedback.textContent = "Select at least one source system.";
    return;
  }

  elements.feedback.textContent = "Starting simulation run...";
  const body = {
    patient_count: Number(elements.patientCount.value),
    seed: Number(elements.seed.value),
    anchor_date: elements.anchorDate.value || null,
    source_systems: sources,
  };

  try {
    const run = await apiFetch("/api/v1/simulation/runs", {
      method: "POST",
      body: JSON.stringify(body),
    });
    elements.feedback.textContent = `Run ${run.run_id} queued. The console will now follow it live.`;
    state.activeRunId = run.run_id;
    await loadRuns();
    beginPolling(run.run_id);
  } catch (error) {
    elements.feedback.textContent = `Could not start run: ${error.message}`;
  }
}

function beginPolling(runId) {
  clearPolling();
  state.polling = window.setInterval(async () => {
    await loadRun(runId);
  }, 2000);
}

function clearPolling() {
  if (state.polling) {
    window.clearInterval(state.polling);
    state.polling = null;
  }
}

async function loadRun(runId) {
  const run = await apiFetch(`/api/v1/simulation/runs/${runId}`);
  renderRun(run);
  if (run.status === "running" || run.status === "queued") {
    beginPolling(runId);
  } else {
    clearPolling();
    await loadRuns();
  }
}

function renderRun(run) {
  renderPipeline(run);
  renderPatients(run);
  renderStream(run);
  renderDatabaseDeltas(run);
  renderApiChecks(run);
}

function renderPipeline(run) {
  const totalDbDelta = run.database_deltas.reduce((sum, item) => sum + Math.max(item.delta, 0), 0);
  const apiSuccess = run.api_checks.filter((check) => check.status === "success").length;
  const lanes = [
    { key: "source", label: "Source Systems", value: run.total_events, copy: laneCopy.source },
    { key: "integration", label: "Mirth / TIE", value: run.processed_events, copy: laneCopy.integration },
    { key: "database", label: "Database", value: totalDbDelta, copy: laneCopy.database },
    { key: "api", label: "API", value: apiSuccess, copy: laneCopy.api },
    { key: "app", label: "Main App", value: run.created_patients.length, copy: laneCopy.app },
  ];

  elements.pipeline.innerHTML = lanes.map((lane) => `
    <article class="lane-card">
      <p class="lane-label">${lane.label}</p>
      <div class="lane-value">${lane.value}</div>
      <p class="lane-copy">${lane.copy}</p>
    </article>
  `).join("");
}

function renderPatients(run) {
  if (!run.created_patients.length) {
    elements.patients.innerHTML = `<div class="empty-state">No patient cards are available for this run yet.</div>`;
    return;
  }

  elements.patients.innerHTML = "";
  run.created_patients.forEach((patient) => {
    const card = document.createElement("article");
    card.className = "patient-card";
    card.innerHTML = `
      <div class="patient-topline">
        <h3 class="patient-title">${patient.patient_name}</h3>
        <span class="status-badge success">${patient.nhs_number}</span>
      </div>
      <p class="patient-meta">Scenario: ${patient.scenario}</p>
      <p class="patient-meta">Pathway UUID: ${patient.pathway_id}</p>
      <div class="patient-actions">
        <button type="button" class="patient-button">Inspect Patient 360</button>
        <a class="patient-button" href="/api/v1/patients/${patient.nhs_number}" target="_blank" rel="noreferrer">Open JSON</a>
      </div>
    `;
    card.querySelector("button").addEventListener("click", () => inspectPatient(patient));
    elements.patients.appendChild(card);
  });
}

function renderStream(run) {
  if (!run.stream.length) {
    elements.stream.innerHTML = `<div class="empty-state">Stream events will appear here as the run progresses.</div>`;
    return;
  }

  elements.stream.innerHTML = run.stream.slice().reverse().map((item) => `
    <article class="stream-item ${item.layer} ${item.status}">
      <div class="stream-head">
        <div>
          <p class="lane-label">${item.component}</p>
          <h3 class="stream-title">${item.title}</h3>
        </div>
        <span class="stream-pill">${item.layer}</span>
      </div>
      <p class="stream-meta">${item.detail}</p>
      <div class="stream-tags">
        ${item.file_name ? `<span class="stream-tag">${item.file_name}</span>` : ""}
        ${item.message_type ? `<span class="stream-tag">${item.message_type}</span>` : ""}
        ${(item.impact_tables || []).map((table) => `<span class="stream-tag">${table}</span>`).join("")}
      </div>
      <p class="stream-meta">${new Date(item.timestamp).toLocaleString()}</p>
    </article>
  `).join("");
}

function renderDatabaseDeltas(run) {
  if (!run.database_deltas.length) {
    elements.database.innerHTML = `<div class="empty-state">Database deltas will appear after the replay completes.</div>`;
    return;
  }

  elements.database.innerHTML = run.database_deltas.map((item) => `
    <article class="table-card">
      <h3>${item.table_name}</h3>
      <div class="table-delta ${item.delta > 0 ? "positive" : "neutral"}">${item.delta >= 0 ? "+" : ""}${item.delta}</div>
      <p class="table-copy">${item.before_count} -> ${item.after_count}</p>
    </article>
  `).join("");
}

function renderApiChecks(run) {
  if (!run.api_checks.length) {
    elements.apiChecks.innerHTML = `<div class="empty-state">API checks will appear when the run is far enough through the pipeline.</div>`;
    return;
  }

  elements.apiChecks.innerHTML = run.api_checks.map((check) => `
    <article class="check-card">
      <div class="check-topline">
        <h3 class="check-title">${check.name}</h3>
        <span class="status-badge ${check.status}">${check.status}</span>
      </div>
      <p class="check-copy">${check.detail}</p>
    </article>
  `).join("");
}

async function inspectPatient(patient) {
  if (!state.token) {
    elements.patientView.innerHTML = `<div class="empty-state">The console could not get a demo token, so patient inspection is unavailable right now.</div>`;
    return;
  }

  elements.patientView.innerHTML = `<div class="empty-state">Loading patient 360 for ${patient.nhs_number}...</div>`;
  try {
    const response = await apiFetch(`/api/v1/patients/${patient.nhs_number}`, {
      headers: { Authorization: `Bearer ${state.token}` },
    });
    renderPatientView(response, patient);
  } catch (error) {
    elements.patientView.innerHTML = `<div class="empty-state">Could not load patient 360: ${error.message}</div>`;
  }
}

function renderPatientView(data, patient) {
  const timeline = (data.timeline || []).slice(0, 8);
  const pathology = (data.pathology_results || []).slice(0, 4);
  const actions = (data.actions || []).slice(0, 4);

  elements.patientView.innerHTML = `
    <div class="patient-view-grid">
      <section class="patient-pane">
        <h3>${patient.patient_name}</h3>
        <dl>
          <dt>NHS number</dt><dd>${data.patient.nhs_number}</dd>
          <dt>Hospital number</dt><dd>${data.patient.hospital_number || "Not populated"}</dd>
          <dt>Cancer type</dt><dd>${data.pathway?.cancer_type_desc || "Not yet available"}</dd>
          <dt>Pathway status</dt><dd>${data.pathway?.pathway_status || "Not yet available"}</dd>
          <dt>Next action</dt><dd>${data.pathway?.next_action || "Not yet available"}</dd>
          <dt>Navigation items</dt><dd>${(data.navigation_actions || []).length}</dd>
          <dt>Pathology results</dt><dd>${(data.pathology_results || []).length}</dd>
          <dt>Radiology results</dt><dd>${(data.radiology_results || []).length}</dd>
        </dl>
      </section>
      <section class="patient-pane">
        <h3>Pathway Timeline</h3>
        <ul class="mini-list">
          ${timeline.map((item) => `
            <li class="mini-item">
              <strong>${item.label}</strong>
              <div>${item.event_date} - ${item.source_system || "System"}</div>
              <div>${item.detail || ""}</div>
            </li>
          `).join("") || `<li class="mini-item">No timeline events returned yet.</li>`}
        </ul>
      </section>
      <section class="patient-pane">
        <h3>Pathology Snapshot</h3>
        <ul class="mini-list">
          ${pathology.map((item) => `
            <li class="mini-item">
              <strong>${item.test_name || item.discipline || "Pathology"}</strong>
              <div>${item.report_date || item.specimen_date || "No date"}</div>
              <div>${item.narrative_report || item.status}</div>
            </li>
          `).join("") || `<li class="mini-item">No pathology rows returned yet.</li>`}
        </ul>
      </section>
      <section class="patient-pane">
        <h3>Open Actions</h3>
        <ul class="mini-list">
          ${actions.map((item) => `
            <li class="mini-item">
              <strong>${item.action_type}</strong>
              <div>${item.status} - ${item.priority}</div>
              <div>${item.action_description || item.notes || ""}</div>
            </li>
          `).join("") || `<li class="mini-item">No actions returned yet.</li>`}
        </ul>
      </section>
    </div>
  `;
}

function bindEvents() {
  elements.form.addEventListener("submit", startRun);
  elements.selectAllSources.addEventListener("click", () => {
    document.querySelectorAll('input[name="source-system"]').forEach((input) => {
      input.checked = true;
    });
  });
  elements.refreshRuns.addEventListener("click", loadRuns);
}

async function init() {
  bindEvents();
  await authenticate();
  await loadCatalog();
  await loadRuns();
}

init().catch((error) => {
  elements.feedback.textContent = `Studio failed to initialise: ${error.message}`;
});
