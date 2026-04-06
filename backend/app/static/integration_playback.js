const playbackState = {
  token: null,
  runs: [],
  activeRun: null,
  currentIndex: -1,
  timer: null,
  speedMs: 900,
  selectedPatientNhs: null,
};

const elements = {
  runSelect: document.getElementById("run-select"),
  speedSelect: document.getElementById("speed-select"),
  refreshRuns: document.getElementById("refresh-runs"),
  resetPlayback: document.getElementById("reset-playback"),
  stepBack: document.getElementById("step-back"),
  playPause: document.getElementById("play-pause"),
  stepForward: document.getElementById("step-forward"),
  progressLabel: document.getElementById("progress-label"),
  progressCount: document.getElementById("progress-count"),
  progressFill: document.getElementById("progress-fill"),
  runSummary: document.getElementById("run-summary"),
  laneBoard: document.getElementById("lane-board"),
  narrationCard: document.getElementById("narration-card"),
  impactCard: document.getElementById("impact-card"),
  payloadPreview: document.getElementById("payload-preview"),
  eventScript: document.getElementById("event-script"),
  patientSelector: document.getElementById("patient-selector"),
  patientReadback: document.getElementById("patient-readback"),
};

const laneDefinitions = [
  { key: "source", label: "Source Systems", colorClass: "source", copy: "Synthetic PAS, Somerset, ICE, RIS, Aria, and Endoscopy payloads are emitted here." },
  { key: "integration", label: "Mirth / TIE", colorClass: "integration", copy: "The integration lane validates, routes, transforms, and prepares upserts." },
  { key: "database", label: "PostgreSQL CDM", colorClass: "database", copy: "The canonical data model stores the clinically integrated view of the patient journey." },
  { key: "api", label: "FastAPI", colorClass: "api", copy: "API endpoints expose the updated records back to dashboards and patient views." },
  { key: "app", label: "Main App", colorClass: "app", copy: "The operator console and Patient 360 views make the replay visible and explainable." },
];

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
  return contentType.includes("application/json") ? response.json() : response.text();
}

async function authenticate() {
  try {
    const token = await apiFetch("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({ username: "studio.operator", password: "cancer360" }),
    });
    playbackState.token = token.access_token;
  } catch (error) {
    console.warn("Playback screen could not acquire demo token.", error);
  }
}

async function loadRuns() {
  const runs = await apiFetch("/api/v1/simulation/runs");
  playbackState.runs = runs.filter((run) => run.status === "completed");
  renderRunOptions();
  if (playbackState.runs.length && !playbackState.activeRun) {
    await selectRun(playbackState.runs[0].run_id);
  } else if (!playbackState.runs.length) {
    renderEmptyState();
  }
}

function renderRunOptions() {
  elements.runSelect.innerHTML = "";
  if (!playbackState.runs.length) {
    elements.runSelect.innerHTML = `<option value="">No completed runs available</option>`;
    return;
  }
  playbackState.runs.forEach((run) => {
    const option = document.createElement("option");
    option.value = run.run_id;
    option.textContent = `Run ${run.run_id} - ${run.patient_count} patients - ${run.total_events} events`;
    elements.runSelect.appendChild(option);
  });
}

async function selectRun(runId) {
  if (!runId) {
    renderEmptyState();
    return;
  }
  stopPlayback();
  const run = await apiFetch(`/api/v1/simulation/runs/${runId}`);
  playbackState.activeRun = run;
  playbackState.currentIndex = -1;
  playbackState.selectedPatientNhs = run.created_patients[0]?.nhs_number || null;
  elements.runSelect.value = runId;
  renderAll();
}

function renderAll() {
  renderSummary();
  renderLaneBoard();
  renderProgress();
  renderCurrentStep();
  renderScript();
  renderPatientSelector();
  if (playbackState.selectedPatientNhs) {
    inspectPatient(playbackState.selectedPatientNhs);
  } else {
    elements.patientReadback.innerHTML = `<div class="empty-state">This run does not have any created patients to inspect.</div>`;
  }
}

function renderEmptyState() {
  elements.runSummary.innerHTML = `<div class="empty-state">Complete a run in the operator console first, then come back here to replay it.</div>`;
  elements.laneBoard.innerHTML = `<div class="empty-state">No playback available yet.</div>`;
  elements.narrationCard.innerHTML = `<div class="empty-state">Select a completed run to begin playback.</div>`;
  elements.impactCard.innerHTML = `<div class="empty-state">Current impact will appear here during playback.</div>`;
  elements.payloadPreview.textContent = "Payload preview will appear here during playback.";
  elements.eventScript.innerHTML = `<div class="empty-state">The event script will appear here after you load a completed run.</div>`;
  elements.patientSelector.innerHTML = "";
  elements.patientReadback.innerHTML = `<div class="empty-state">Patient readback becomes available after a completed run is selected.</div>`;
  elements.progressLabel.textContent = "No run loaded";
  elements.progressCount.textContent = "0 / 0";
  elements.progressFill.style.width = "0%";
}

function renderSummary() {
  const run = playbackState.activeRun;
  if (!run) return;
  const cards = [
    { label: "Patients", value: run.patient_count, copy: `${run.created_patients.length} synthetic patients are attached to this replay.` },
    { label: "Events", value: run.total_events, copy: `${run.processed_events} events were processed through the integration lane.` },
    { label: "Sources", value: run.source_systems.length, copy: run.source_systems.join(", ") },
    { label: "API checks", value: run.api_checks.length, copy: `${run.api_checks.filter((item) => item.status === "success").length} succeeded after replay.` },
  ];
  elements.runSummary.innerHTML = cards.map((card) => `
    <article class="summary-card">
      <p class="summary-label">${card.label}</p>
      <p class="summary-value">${card.value}</p>
      <p class="summary-copy">${card.copy}</p>
    </article>
  `).join("");
}

function getCurrentEvent() {
  const run = playbackState.activeRun;
  if (!run || playbackState.currentIndex < 0 || playbackState.currentIndex >= run.stream.length) return null;
  return run.stream[playbackState.currentIndex];
}

function countsUpToCurrent() {
  const counts = { source: 0, integration: 0, database: 0, api: 0, app: 0 };
  const run = playbackState.activeRun;
  if (!run) return counts;
  run.stream.forEach((item, index) => {
    if (index <= playbackState.currentIndex && counts[item.layer] !== undefined) {
      counts[item.layer] += 1;
    }
  });
  return counts;
}

function renderLaneBoard() {
  const run = playbackState.activeRun;
  if (!run) return;
  const current = getCurrentEvent();
  const counts = countsUpToCurrent();
  elements.laneBoard.innerHTML = laneDefinitions.map((lane) => `
    <article class="lane-column ${lane.colorClass} ${current?.layer === lane.key ? "active" : ""}">
      ${current?.layer === lane.key ? '<div class="lane-token"></div>' : ""}
      <span class="lane-badge">${lane.label}</span>
      <h3>${lane.label}</h3>
      <p>${lane.copy}</p>
      <div class="lane-count">${counts[lane.key] || 0}</div>
      <p>${current?.layer === lane.key ? current.title : "Waiting for the next event in this lane."}</p>
    </article>
  `).join("");
}

function renderProgress() {
  const run = playbackState.activeRun;
  if (!run) return;
  const currentNumber = Math.max(playbackState.currentIndex + 1, 0);
  const total = run.stream.length;
  elements.progressLabel.textContent = `Run ${run.run_id}`;
  elements.progressCount.textContent = `${currentNumber} / ${total}`;
  elements.progressFill.style.width = total ? `${(currentNumber / total) * 100}%` : "0%";
  elements.playPause.textContent = playbackState.timer ? "Pause" : "Play";
}

function renderCurrentStep() {
  const current = getCurrentEvent();
  if (!current) {
    elements.narrationCard.innerHTML = `<div class="empty-state">Press Play or step forward to start the narrated replay.</div>`;
    elements.impactCard.innerHTML = `<div class="empty-state">Current impact will appear here when the replay advances.</div>`;
    elements.payloadPreview.textContent = "Payload preview will appear here during playback.";
    return;
  }
  elements.narrationCard.innerHTML = `
    <p class="summary-label">${current.component}</p>
    <h3 class="narration-title">${current.title}</h3>
    <p class="narration-meta">Lane: ${current.layer} · ${new Date(current.timestamp).toLocaleString()}</p>
    <p class="narration-copy">${current.detail}</p>
  `;
  elements.impactCard.innerHTML = `
    <p class="summary-label">Downstream effect</p>
    <h3 class="impact-title">${current.source_system ? current.source_system.toUpperCase() : current.layer.toUpperCase()}</h3>
    <p class="impact-meta">${current.file_name || current.message_type || "Synthetic event"}</p>
    <p class="impact-copy">${current.impact_tables?.length ? `This step affects ${current.impact_tables.length} table(s) and helps make the replay visible in the app.` : "This step is explanatory and does not directly change a table."}</p>
    <div class="impact-tags">
      ${(current.impact_tables || []).map((item) => `<span class="impact-tag">${item}</span>`).join("") || '<span class="impact-tag">narration</span>'}
    </div>
  `;
  elements.payloadPreview.textContent = current.payload_preview || "No payload preview is available for this event.";
}

function renderScript() {
  const run = playbackState.activeRun;
  if (!run) return;
  elements.eventScript.innerHTML = run.stream.map((item, index) => `
    <article class="script-row ${index === playbackState.currentIndex ? "active" : ""}">
      <div class="topline">
        <h3>${item.title}</h3>
        <span class="lane-badge">${item.layer}</span>
      </div>
      <p>${item.detail}</p>
      <div class="script-tags">
        ${item.file_name ? `<span class="script-tag">${item.file_name}</span>` : ""}
        ${item.message_type ? `<span class="script-tag">${item.message_type}</span>` : ""}
        ${(item.impact_tables || []).map((table) => `<span class="script-tag">${table}</span>`).join("")}
      </div>
    </article>
  `).join("");
  const active = elements.eventScript.querySelector(".script-row.active");
  if (active) active.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderPatientSelector() {
  const run = playbackState.activeRun;
  if (!run || !run.created_patients.length) {
    elements.patientSelector.innerHTML = "";
    return;
  }
  elements.patientSelector.innerHTML = run.created_patients.map((patient) => `
    <button type="button" class="patient-pick ${playbackState.selectedPatientNhs === patient.nhs_number ? "is-active" : ""}" data-nhs="${patient.nhs_number}">
      ${patient.patient_name}<br>${patient.nhs_number}
    </button>
  `).join("");
  elements.patientSelector.querySelectorAll("[data-nhs]").forEach((button) => {
    button.addEventListener("click", () => {
      playbackState.selectedPatientNhs = button.dataset.nhs;
      renderPatientSelector();
      inspectPatient(button.dataset.nhs);
    });
  });
}

async function inspectPatient(nhsNumber) {
  if (!playbackState.token) {
    elements.patientReadback.innerHTML = `<div class="empty-state">A demo token is required to inspect Patient 360.</div>`;
    return;
  }
  elements.patientReadback.innerHTML = `<div class="empty-state">Loading Patient 360 for ${nhsNumber}...</div>`;
  try {
    const data = await apiFetch(`/api/v1/patients/${nhsNumber}`, {
      headers: { Authorization: `Bearer ${playbackState.token}` },
    });
    const timeline = (data.timeline || []).slice(0, 6);
    const actions = (data.actions || []).slice(0, 5);
    elements.patientReadback.innerHTML = `
      <div class="readback-grid">
        <section class="readback-pane">
          <h3>${data.patient.surname}, ${data.patient.forename}</h3>
          <dl>
            <dt>NHS number</dt><dd>${data.patient.nhs_number}</dd>
            <dt>Hospital number</dt><dd>${data.patient.hospital_number || "Not populated"}</dd>
            <dt>Cancer type</dt><dd>${data.pathway?.cancer_type_desc || "Not available"}</dd>
            <dt>Pathway status</dt><dd>${data.pathway?.pathway_status || "Not available"}</dd>
            <dt>Pathology</dt><dd>${(data.pathology_results || []).length}</dd>
            <dt>Radiology</dt><dd>${(data.radiology_results || []).length}</dd>
            <dt>Navigation</dt><dd>${(data.navigation_actions || []).length}</dd>
            <dt>Actions</dt><dd>${(data.actions || []).length}</dd>
          </dl>
        </section>
        <section class="readback-pane">
          <h3>Timeline Readback</h3>
          <ul class="mini-list">
            ${timeline.map((item) => `<li class="mini-item"><strong>${item.label}</strong><div>${item.event_date} - ${item.source_system || "System"}</div><div>${item.detail || ""}</div></li>`).join("") || `<li class="mini-item">No timeline rows returned yet.</li>`}
          </ul>
        </section>
        <section class="readback-pane">
          <h3>Action Readback</h3>
          <ul class="mini-list">
            ${actions.map((item) => `<li class="mini-item"><strong>${item.action_type}</strong><div>${item.status} - ${item.priority}</div><div>${item.action_description || item.notes || ""}</div></li>`).join("") || `<li class="mini-item">No actions returned yet.</li>`}
          </ul>
        </section>
        <section class="readback-pane">
          <h3>Useful Links</h3>
          <ul class="mini-list">
            <li class="mini-item"><a href="/api/v1/patients/${nhsNumber}" target="_blank" rel="noreferrer">Open Patient 360 JSON</a></li>
            <li class="mini-item"><a href="/api/v1/patients/${nhsNumber}/navigation" target="_blank" rel="noreferrer">Open Navigation JSON</a></li>
          </ul>
        </section>
      </div>
    `;
  } catch (error) {
    elements.patientReadback.innerHTML = `<div class="empty-state">Could not load Patient 360: ${error.message}</div>`;
  }
}

function stepForward() {
  const run = playbackState.activeRun;
  if (!run) return;
  if (playbackState.currentIndex < run.stream.length - 1) {
    playbackState.currentIndex += 1;
    renderLaneBoard();
    renderProgress();
    renderCurrentStep();
    renderScript();
  } else {
    stopPlayback();
  }
}

function stepBack() {
  if (playbackState.currentIndex > -1) {
    playbackState.currentIndex -= 1;
    renderLaneBoard();
    renderProgress();
    renderCurrentStep();
    renderScript();
  }
}

function resetPlayback() {
  stopPlayback();
  playbackState.currentIndex = -1;
  renderLaneBoard();
  renderProgress();
  renderCurrentStep();
  renderScript();
}

function stopPlayback() {
  if (playbackState.timer) {
    window.clearInterval(playbackState.timer);
    playbackState.timer = null;
  }
  elements.playPause.textContent = "Play";
}

function startPlayback() {
  stopPlayback();
  playbackState.timer = window.setInterval(() => {
    stepForward();
    if (!playbackState.activeRun || playbackState.currentIndex >= playbackState.activeRun.stream.length - 1) {
      stopPlayback();
    }
  }, playbackState.speedMs);
  elements.playPause.textContent = "Pause";
}

function togglePlayback() {
  if (!playbackState.activeRun) return;
  if (playbackState.timer) stopPlayback();
  else startPlayback();
}

function bindEvents() {
  elements.runSelect.addEventListener("change", async (event) => {
    await selectRun(event.target.value);
  });
  elements.speedSelect.addEventListener("change", (event) => {
    playbackState.speedMs = Number(event.target.value);
    if (playbackState.timer) startPlayback();
  });
  elements.refreshRuns.addEventListener("click", loadRuns);
  elements.resetPlayback.addEventListener("click", resetPlayback);
  elements.stepBack.addEventListener("click", stepBack);
  elements.stepForward.addEventListener("click", stepForward);
  elements.playPause.addEventListener("click", togglePlayback);
}

async function init() {
  bindEvents();
  await authenticate();
  await loadRuns();
}

init().catch((error) => {
  elements.narrationCard.innerHTML = `<div class="empty-state">Playback failed to initialise: ${error.message}</div>`;
});
