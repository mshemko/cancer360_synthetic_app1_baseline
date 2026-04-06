const state = {
  token: null,
  dashboard: null,
  ptl: null,
  actions: [],
  integration: null,
  catalog: null,
  runs: [],
  activeRunId: null,
  polling: null,
  selectedPatientNhs: null,
  selectedPatient: null,
  ptlFilters: {
    search: "",
    pathway_status: "",
    breach_risk: "",
  },
};

const elements = {
  authStatus: document.getElementById("auth-status"),
  refreshDashboard: document.getElementById("refresh-dashboard"),
  overviewMetrics: document.getElementById("overview-metrics"),
  pathwayMix: document.getElementById("pathway-mix"),
  teamPerformance: document.getElementById("team-performance"),
  integrationHealth: document.getElementById("integration-health"),
  overviewNarrative: document.getElementById("overview-narrative"),
  ptlSearch: document.getElementById("ptl-search"),
  ptlStatus: document.getElementById("ptl-status"),
  ptlRisk: document.getElementById("ptl-risk"),
  applyPtlFilters: document.getElementById("apply-ptl-filters"),
  ptlSummaryCards: document.getElementById("ptl-summary-cards"),
  ptlTableBody: document.getElementById("ptl-table-body"),
  actionSummary: document.getElementById("action-summary"),
  actionList: document.getElementById("action-list"),
  patientSearchForm: document.getElementById("patient-search-form"),
  patientSearchInput: document.getElementById("patient-search-input"),
  searchResults: document.getElementById("search-results"),
  selectedPatientBadge: document.getElementById("selected-patient-badge"),
  patientEmpty: document.getElementById("patient-empty"),
  patientContent: document.getElementById("patient-content"),
  patientHeadline: document.getElementById("patient-headline"),
  patientSummary: document.getElementById("patient-summary"),
  patientProvenance: document.getElementById("patient-provenance"),
  patientTimeline: document.getElementById("patient-timeline"),
  patientNavigation: document.getElementById("patient-navigation"),
  patientPathology: document.getElementById("patient-pathology"),
  patientTreatment: document.getElementById("patient-treatment"),
  heroRunTitle: document.getElementById("hero-run-title"),
  heroRunCopy: document.getElementById("hero-run-copy"),
  form: document.getElementById("run-form"),
  patientCount: document.getElementById("patient-count"),
  seed: document.getElementById("seed"),
  anchorDate: document.getElementById("anchor-date"),
  sourceOptions: document.getElementById("source-options"),
  selectAllSources: document.getElementById("select-all-sources"),
  refreshRuns: document.getElementById("refresh-runs"),
  runFeedback: document.getElementById("run-feedback"),
  pipelineLanes: document.getElementById("pipeline-lanes"),
  runsList: document.getElementById("runs-list"),
  runPatients: document.getElementById("run-patients"),
  streamList: document.getElementById("stream-list"),
  databaseDeltas: document.getElementById("database-deltas"),
  apiChecks: document.getElementById("api-checks"),
  navButtons: Array.from(document.querySelectorAll(".nav-button")),
};

function formatNumber(value) {
  return new Intl.NumberFormat("en-GB").format(Number(value || 0));
}

function formatDate(value) {
  if (!value) {
    return "Not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function percentage(value) {
  if (value === null || value === undefined) {
    return "Not available";
  }
  return `${value}%`;
}

async function apiFetch(url, options = {}, requireAuth = true) {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (requireAuth && state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
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
  const token = await apiFetch("/api/v1/auth/token", {
    method: "POST",
    body: JSON.stringify({ username: "cancer360.demo", password: "cancer360" }),
  }, false);
  state.token = token.access_token;
  elements.authStatus.textContent = "Ready";
}

function makeMetricCard(label, value, detail, tone = "") {
  return `
    <article class="metric-card ${tone}">
      <p class="metric-label">${label}</p>
      <div class="metric-value">${value}</div>
      <p class="metric-detail">${detail}</p>
    </article>
  `;
}

function makeMiniCard(label, value, detail = "", tone = "") {
  return `
    <article class="mini-card ${tone}">
      <p class="metric-label">${label}</p>
      <div class="metric-value">${value}</div>
      <p class="metric-detail">${detail}</p>
    </article>
  `;
}

function renderBarRows(rows, valueKey, labelKey) {
  const max = Math.max(...rows.map((row) => Number(row[valueKey] || 0)), 1);
  return rows.map((row) => {
    const value = Number(row[valueKey] || 0);
    const width = Math.max((value / max) * 100, value ? 8 : 0);
    const label = String(row[labelKey] || row.risk || "Unknown").replaceAll("_", " ");
    const tone = label.includes("breach") ? "danger" : "";
    return `
      <article class="stack-item">
        <div class="metric-topline">
          <strong>${label}</strong>
          <span>${formatNumber(value)}</span>
        </div>
        <div class="bar-row">
          <div class="bar-track"><div class="bar-fill ${tone}" style="width:${width}%"></div></div>
        </div>
      </article>
    `;
  });
}

function renderOverview() {
  if (!state.dashboard || !state.integration || !state.ptl) {
    return;
  }

  const totalActions = state.actions.length;
  const overdueActions = state.actions.filter((action) => {
    if (!action.due_date || action.status === "completed") {
      return false;
    }
    return new Date(action.due_date) < new Date();
  }).length;

  elements.overviewMetrics.innerHTML = [
    makeMetricCard("Total pathways", formatNumber(state.dashboard.total_pathways), `${formatNumber(state.dashboard.active_pathways)} currently active`),
    makeMetricCard("28-day FDS", percentage(state.dashboard.fds_28d_performance), `${formatNumber(state.dashboard.fds_28d_numerator)} of ${formatNumber(state.dashboard.fds_28d_denominator)} diagnosed within standard`),
    makeMetricCard("62-day RTT", percentage(state.dashboard.rtt_62d_performance), `${formatNumber(state.dashboard.rtt_62d_numerator)} of ${formatNumber(state.dashboard.rtt_62d_denominator)} treated within standard`),
    makeMetricCard("Integration errors", formatNumber(state.integration.audit_error), `${formatNumber(state.integration.dlq_pending)} pending in the DLQ`, state.integration.audit_error ? "danger" : ""),
    makeMetricCard("Open actions", formatNumber(totalActions), `${formatNumber(overdueActions)} overdue or past due date`, overdueActions ? "warn" : ""),
  ].join("");

  elements.pathwayMix.innerHTML = [
    ...renderBarRows(state.dashboard.by_cancer_type.slice(0, 6), "count", "label"),
    ...renderBarRows(state.dashboard.by_status, "count", "status"),
  ].join("") || `<div class="empty-state">No pathway mix is available yet.</div>`;

  const teamCounts = {};
  state.ptl.items.forEach((item) => {
    const team = item.assigned_team || "Unassigned";
    if (!teamCounts[team]) {
      teamCounts[team] = { pathways: 0, breached: 0, high: 0 };
    }
    teamCounts[team].pathways += 1;
    if (item.breach_risk === "breached") {
      teamCounts[team].breached += 1;
    }
    if (item.breach_risk === "high") {
      teamCounts[team].high += 1;
    }
  });
  const rankedTeams = Object.entries(teamCounts)
    .sort((a, b) => (b[1].breached + b[1].high) - (a[1].breached + a[1].high))
    .slice(0, 6);
  elements.teamPerformance.innerHTML = rankedTeams.map(([team, counts]) => `
    <article class="stack-item">
      <div class="metric-topline">
        <strong>${team}</strong>
        <span class="pill ${counts.breached ? "danger" : counts.high ? "warn" : "success"}">${counts.pathways} pathways</span>
      </div>
      <div class="source-meta">${counts.breached} breached, ${counts.high} high risk.</div>
    </article>
  `).join("") || `<div class="empty-state">No team allocation data is available yet.</div>`;

  elements.integrationHealth.innerHTML = state.integration.source_status.map((source) => `
    <article class="source-card">
      <div class="metric-topline">
        <strong>${source.source_system}</strong>
        <span class="pill ${source.error_count ? "danger" : "success"}">${source.error_count ? "Attention" : "Healthy"}</span>
      </div>
      <div class="counts">
        <span class="pill success">${formatNumber(source.success_count)} success</span>
        <span class="pill ${source.error_count ? "danger" : "info"}">${formatNumber(source.error_count)} error</span>
      </div>
      <div class="source-meta">Last event ${formatDateTime(source.last_event_at)}</div>
    </article>
  `).join("") || `<div class="empty-state">No source-system audit data is available yet.</div>`;

  const activeRun = getActiveRun();
  elements.overviewNarrative.innerHTML = `
    <strong>${formatNumber(state.dashboard.active_pathways)} pathways are currently in flight.</strong>
    The live backend is reporting ${formatNumber(state.integration.audit_total)} integration audit events across
    ${formatNumber(state.integration.source_status.length)} source-system groupings. The PTL contains
    ${formatNumber(state.ptl.total)} visible pathways, and the actions inbox currently holds ${formatNumber(totalActions)}
    items. ${activeRun ? `The selected simulation run has processed ${formatNumber(activeRun.processed_events)} of ${formatNumber(activeRun.total_events)} events and already created ${formatNumber(activeRun.created_patients.length)} patient records visible in the app.` : "No simulation run is selected right now, so the integration lane is showing the latest persisted state."}
  `;
}

function renderPTL() {
  if (!state.ptl) {
    return;
  }

  const summary = state.ptl.summary;
  elements.ptlSummaryCards.innerHTML = [
    makeMiniCard("Total", formatNumber(summary.total)),
    makeMiniCard("Breached", formatNumber(summary.breached), "", summary.breached ? "danger" : ""),
    makeMiniCard("High risk", formatNumber(summary.high_risk), "", summary.high_risk ? "warn" : ""),
    makeMiniCard("Awaiting MDT", formatNumber(summary.awaiting_mdt)),
    makeMiniCard("Awaiting treatment", formatNumber(summary.awaiting_treatment)),
    makeMiniCard("On treatment", formatNumber(summary.on_treatment)),
  ].join("");

  if (!state.ptl.items.length) {
    elements.ptlTableBody.innerHTML = `<tr><td colspan="7" class="table-empty">No PTL rows match the current filters.</td></tr>`;
    return;
  }

  elements.ptlTableBody.innerHTML = state.ptl.items.map((item) => `
    <tr class="data-row" data-nhs="${item.nhs_number}">
      <td>
        <strong>${item.patient_name}</strong>
        <div class="muted">${item.nhs_number}</div>
      </td>
      <td>${item.cancer_type_desc || item.cancer_type_code || "Not yet coded"}</td>
      <td>${String(item.pathway_status || "").replaceAll("_", " ")}</td>
      <td>${item.days_on_pathway ?? "Not available"}</td>
      <td><span class="risk-chip ${item.breach_risk}">${item.breach_risk}</span></td>
      <td>${item.next_action || "No next action recorded"}</td>
      <td>${item.assigned_team || "Unassigned"}</td>
    </tr>
  `).join("");

  Array.from(elements.ptlTableBody.querySelectorAll(".data-row")).forEach((row) => {
    row.addEventListener("click", () => {
      loadPatient(row.dataset.nhs, true);
    });
  });
}

function renderActions() {
  const open = state.actions.filter((action) => action.status !== "completed");
  const completed = state.actions.filter((action) => action.status === "completed");
  const somersetDerived = state.actions.filter((action) => ["Somerset", "Endoscopy"].includes(action.source_system)).length;

  elements.actionSummary.innerHTML = [
    makeMiniCard("Open", formatNumber(open.length)),
    makeMiniCard("Completed", formatNumber(completed.length)),
    makeMiniCard("Somerset or Endoscopy", formatNumber(somersetDerived)),
    makeMiniCard("High priority", formatNumber(state.actions.filter((action) => action.priority === "high").length), "", "warn"),
  ].join("");

  if (!state.actions.length) {
    elements.actionList.innerHTML = `<div class="empty-state">No actions have been returned yet.</div>`;
    return;
  }

  elements.actionList.innerHTML = state.actions.slice(0, 30).map((action) => `
    <article class="action-card" data-patient-id="${action.patient_id}">
      <div class="action-topline">
        <strong>${action.action_type}</strong>
        <span class="pill ${action.status === "completed" ? "success" : action.priority === "high" ? "warn" : "info"}">${action.status}</span>
      </div>
      <div>${action.action_description || action.notes || "No action description supplied."}</div>
      <div class="tag-row">
        <span class="tag">${action.priority}</span>
        ${action.assigned_team ? `<span class="tag">${action.assigned_team}</span>` : ""}
        ${action.source_system ? `<span class="tag">${action.source_system}</span>` : ""}
      </div>
      <div class="source-meta">Due ${formatDate(action.due_date)}. Created ${formatDateTime(action.created_at)}.</div>
    </article>
  `).join("");

  const ptlById = new Map((state.ptl?.items || []).map((item) => [String(item.patient_id), item.nhs_number]));
  Array.from(elements.actionList.querySelectorAll(".action-card")).forEach((card) => {
    card.addEventListener("click", () => {
      const nhs = ptlById.get(card.dataset.patientId);
      if (nhs) {
        loadPatient(nhs, true);
      }
    });
  });
}

function renderSearchResults(results) {
  if (!results.length) {
    elements.searchResults.classList.add("empty-state");
    elements.searchResults.classList.remove("has-results");
    elements.searchResults.innerHTML = "No matching patients were found.";
    return;
  }

  elements.searchResults.classList.remove("empty-state");
  elements.searchResults.classList.add("has-results");
  elements.searchResults.innerHTML = results.map((patient) => `
    <button type="button" class="search-result" data-nhs="${patient.nhs_number}">
      <div class="metric-topline">
        <strong>${patient.surname}, ${patient.forename}</strong>
        <span class="pill info">${patient.nhs_number}</span>
      </div>
      <div class="source-meta">DOB ${formatDate(patient.date_of_birth)}. ${patient.sex}.</div>
    </button>
  `).join("");

  Array.from(elements.searchResults.querySelectorAll(".search-result")).forEach((button) => {
    button.addEventListener("click", () => {
      loadPatient(button.dataset.nhs, true);
    });
  });
}

function renderDefinitionGrid(rows) {
  return rows.map(([label, value]) => `
    <div class="label">${label}</div>
    <div>${value}</div>
  `).join("");
}

function renderSimpleCards(items, titleFn, metaFn, bodyFn, tagFn) {
  if (!items.length) {
    return `<div class="empty-state">No records are available yet.</div>`;
  }
  return items.slice(0, 8).map((item) => `
    <article class="stack-item">
      <div class="metric-topline">
        <strong>${titleFn(item)}</strong>
        <span class="pill info">${tagFn(item)}</span>
      </div>
      <div class="source-meta">${metaFn(item)}</div>
      <div>${bodyFn(item)}</div>
    </article>
  `).join("");
}

function sourceClass(source) {
  const normalized = String(source || "").toLowerCase();
  if (normalized.includes("somerset")) {
    return "source-somerset";
  }
  if (normalized.includes("ice")) {
    return "source-ice";
  }
  if (normalized.includes("ris")) {
    return "source-ris";
  }
  if (normalized.includes("aria")) {
    return "source-aria";
  }
  if (normalized.includes("endo")) {
    return "source-endoscopy";
  }
  return "";
}

function buildProvenance(data) {
  const navigation = (data.navigation_actions || []).map((item) => item.source_system || "Cancer 360");
  return [
    {
      source: "Somerset Cancer Register",
      count: (data.timeline || []).filter((event) => String(event.source_system || "").toLowerCase().includes("somerset")).length + navigation.filter((source) => source === "Somerset").length,
      detail: "Pathway, diagnosis, MDT, and navigation context.",
    },
    {
      source: "ICE / WinPath",
      count: (data.pathology_results || []).length,
      detail: "Pathology and structured histopathology records.",
    },
    {
      source: "RIS / CRIS",
      count: (data.radiology_results || []).length,
      detail: "Radiology examinations and conclusions.",
    },
    {
      source: "Aria",
      count: (data.sact_courses || []).length + (data.rt_courses || []).length,
      detail: "Treatment courses, cycles, and fractions.",
    },
    {
      source: "Endoscopy",
      count: navigation.filter((source) => source === "Endoscopy").length,
      detail: "Endoscopy-derived navigation items and downstream actions.",
    },
  ];
}

function renderPatient() {
  if (!state.selectedPatient) {
    elements.patientEmpty.classList.remove("is-hidden");
    elements.patientContent.classList.add("is-hidden");
    elements.selectedPatientBadge.querySelector("strong").textContent = "None";
    return;
  }

  const data = state.selectedPatient;
  const patientName = `${data.patient.surname}, ${data.patient.forename}`;
  elements.patientEmpty.classList.add("is-hidden");
  elements.patientContent.classList.remove("is-hidden");
  elements.selectedPatientBadge.querySelector("strong").textContent = data.patient.nhs_number;
  elements.patientHeadline.innerHTML = `
    <h3>${patientName}</h3>
    <p>
      ${data.pathway?.cancer_type_desc || "Cancer type not yet classified"}.
      Pathway status: ${String(data.pathway?.pathway_status || "not available").replaceAll("_", " ")}.
      Next action: ${data.pathway?.next_action || "not yet recorded"}.
    </p>
  `;

  elements.patientSummary.innerHTML = renderDefinitionGrid([
    ["NHS number", data.patient.nhs_number],
    ["Hospital number", data.patient.hospital_number || "Not populated"],
    ["DOB", formatDate(data.patient.date_of_birth)],
    ["Age", data.patient.age ?? "Not available"],
    ["Cancer type", data.pathway?.cancer_type_desc || data.pathway?.cancer_type_code || "Not available"],
    ["Pathway status", String(data.pathway?.pathway_status || "Not available").replaceAll("_", " ")],
    ["Breach risk", data.pathway?.breach_risk || "Not available"],
    ["Assigned team", data.pathway?.assigned_team || "Not available"],
    ["Next action", data.pathway?.next_action || "Not available"],
    ["Referral received", formatDate(data.pathway?.date_referral_received)],
  ]);

  elements.patientProvenance.innerHTML = buildProvenance(data).map((item) => `
    <article class="stack-item">
      <div class="metric-topline">
        <strong>${item.source}</strong>
        <span class="pill ${item.count ? "success" : "info"}">${formatNumber(item.count)} items</span>
      </div>
      <div class="source-meta">${item.detail}</div>
    </article>
  `).join("");

  elements.patientTimeline.innerHTML = (data.timeline || []).map((event) => `
    <article class="timeline-item ${sourceClass(event.source_system)}">
      <div class="metric-topline">
        <strong>${event.label}</strong>
        <span class="pill info">${event.source_system || "System"}</span>
      </div>
      <div class="source-meta">${formatDate(event.event_date)}. ${event.detail || "No detail supplied."}</div>
    </article>
  `).join("") || `<div class="empty-state">No timeline events were returned for this patient.</div>`;

  elements.patientNavigation.innerHTML = renderSimpleCards(
    [...(data.navigation_actions || []), ...(data.actions || []).slice(0, 4)],
    (item) => item.action_type,
    (item) => `${item.status} | ${item.priority}`,
    (item) => item.action_description || item.notes || "No description",
    (item) => item.source_system || "Cancer 360"
  );

  elements.patientPathology.innerHTML = renderSimpleCards(
    data.pathology_results || [],
    (item) => item.test_name || item.discipline || "Pathology",
    (item) => formatDateTime(item.report_date || item.specimen_date),
    (item) => item.narrative_report || item.status,
    () => "ICE / WinPath"
  );

  const treatmentCards = [
    ...(data.radiology_results || []).map((item) => ({
      title: item.exam_description || item.modality || "Radiology",
      meta: formatDateTime(item.report_date || item.exam_date),
      body: item.conclusion || item.report_text || item.status,
      tag: "RIS / CRIS",
    })),
    ...(data.sact_courses || []).map((item) => ({
      title: item.regimen_name || "SACT course",
      meta: `${formatDate(item.start_date)} to ${formatDate(item.end_date)}`,
      body: `${item.course_status}. ${item.completed_cycles || 0} cycles completed.`,
      tag: "Aria",
    })),
    ...(data.rt_courses || []).map((item) => ({
      title: item.treatment_site || "Radiotherapy course",
      meta: `${formatDate(item.first_fraction_date)} to ${formatDate(item.last_fraction_date)}`,
      body: `${item.course_status}. ${item.fractions_prescribed || 0} fractions prescribed.`,
      tag: "Aria",
    })),
    ...(data.mdt_discussions || []).slice(0, 4).map((item) => ({
      title: `${item.mdt_type || "MDT"} discussion`,
      meta: formatDate(item.mdt_date),
      body: item.decision || item.clinical_summary || "No MDT note available.",
      tag: "Somerset MDT",
    })),
  ];
  elements.patientTreatment.innerHTML = renderSimpleCards(
    treatmentCards,
    (item) => item.title,
    (item) => item.meta,
    (item) => item.body,
    (item) => item.tag
  );
}

function renderSourceOptions() {
  if (!state.catalog) {
    return;
  }
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
  elements.patientCount.value = state.catalog.default_patient_count;
  elements.seed.value = state.catalog.recommended_seed;
}

function selectedSources() {
  return Array.from(document.querySelectorAll('input[name="source-system"]:checked')).map((input) => input.value);
}

function getActiveRun() {
  return state.runs.find((run) => run.run_id === state.activeRunId) || state.runs[0] || null;
}

function renderPipeline(run) {
  const totalDbDelta = run ? run.database_deltas.reduce((sum, item) => sum + Math.max(item.delta, 0), 0) : 0;
  const apiSuccess = run ? run.api_checks.filter((check) => check.status === "success").length : 0;
  const lanes = [
    {
      label: "Source Systems",
      value: run ? formatNumber(run.total_events) : formatNumber((state.integration?.source_status || []).reduce((sum, item) => sum + item.success_count + item.error_count, 0)),
      copy: run ? "Synthetic payloads generated for the selected run." : "Latest persisted source-system activity from the audit trail.",
    },
    {
      label: "Mirth / TIE",
      value: run ? formatNumber(run.processed_events) : formatNumber(state.integration?.audit_total || 0),
      copy: "This is the integration lane where payloads are parsed, routed, and acknowledged.",
    },
    {
      label: "Database",
      value: run ? formatNumber(totalDbDelta) : formatNumber(state.dashboard?.total_pathways || 0),
      copy: "Rows written to the canonical model and then made available to the API.",
    },
    {
      label: "API",
      value: run ? formatNumber(apiSuccess) : formatNumber((state.integration?.source_status || []).length),
      copy: "Checks and endpoints that read the resulting data back out.",
    },
    {
      label: "Main App",
      value: run ? formatNumber(run.created_patients.length) : formatNumber((state.ptl?.items || []).length),
      copy: "Patients and pathways currently visible in the interface.",
    },
  ];
  elements.pipelineLanes.innerHTML = lanes.map((lane) => `
    <article class="lane-card">
      <p class="lane-label">${lane.label}</p>
      <div class="lane-value">${lane.value}</div>
      <p class="metric-detail">${lane.copy}</p>
    </article>
  `).join("");
}

function renderRuns(activeRun) {
  if (!state.runs.length) {
    elements.runsList.innerHTML = `<div class="empty-state">No simulation runs are available yet.</div>`;
    return;
  }

  elements.runsList.innerHTML = state.runs.map((run) => `
    <button type="button" class="run-card ${activeRun && run.run_id === activeRun.run_id ? "is-active" : ""}" data-run-id="${run.run_id}">
      <div class="run-topline">
        <strong>Run ${run.run_id}</strong>
        <span class="pill ${run.status === "completed" ? "success" : run.status === "failed" ? "danger" : "warn"}">${run.status}</span>
      </div>
      <div>${formatNumber(run.patient_count)} patients, ${formatNumber(run.total_events)} events.</div>
      <div class="source-meta">${run.source_systems.join(", ")}</div>
    </button>
  `).join("");

  Array.from(elements.runsList.querySelectorAll(".run-card")).forEach((button) => {
    button.addEventListener("click", async () => {
      state.activeRunId = button.dataset.runId;
      await loadRun(state.activeRunId);
    });
  });
}

function renderRunPatients(run) {
  if (!run || !run.created_patients.length) {
    elements.runPatients.innerHTML = `<div class="empty-state">Patients created by the selected run will appear here.</div>`;
    return;
  }
  elements.runPatients.innerHTML = run.created_patients.map((patient) => `
    <button type="button" class="patient-card" data-nhs="${patient.nhs_number}">
      <div class="patient-card-topline">
        <strong>${patient.patient_name}</strong>
        <span class="pill success">${patient.nhs_number}</span>
      </div>
      <div>${patient.scenario}</div>
      <div class="source-meta">Pathway ${patient.pathway_id}</div>
    </button>
  `).join("");

  Array.from(elements.runPatients.querySelectorAll(".patient-card")).forEach((button) => {
    button.addEventListener("click", () => {
      loadPatient(button.dataset.nhs, true);
    });
  });
}

function renderStream(run) {
  if (!run || !run.stream.length) {
    elements.streamList.innerHTML = `<div class="empty-state">The event stream will appear here when a run is selected.</div>`;
    return;
  }
  elements.streamList.innerHTML = run.stream.slice().reverse().slice(0, 30).map((item) => `
    <article class="stream-item ${item.layer}">
      <div class="stream-topline">
        <div>
          <p class="lane-label">${item.component}</p>
          <strong>${item.title}</strong>
        </div>
        <span class="pill ${item.status === "error" ? "danger" : "info"}">${item.layer}</span>
      </div>
      <div>${item.detail}</div>
      <div class="tag-row">
        ${item.file_name ? `<span class="tag">${item.file_name}</span>` : ""}
        ${item.message_type ? `<span class="tag">${item.message_type}</span>` : ""}
        ${(item.impact_tables || []).map((table) => `<span class="tag">${table}</span>`).join("")}
      </div>
      <div class="source-meta">${formatDateTime(item.timestamp)}</div>
    </article>
  `).join("");
}

function renderDatabaseImpact(run) {
  if (!run || !run.database_deltas.length) {
    elements.databaseDeltas.innerHTML = `<div class="empty-state">Database deltas will appear when a run completes.</div>`;
    return;
  }
  elements.databaseDeltas.innerHTML = run.database_deltas.map((item) => makeMiniCard(
    item.table_name,
    `${item.delta >= 0 ? "+" : ""}${formatNumber(item.delta)}`,
    `${formatNumber(item.before_count)} to ${formatNumber(item.after_count)}`,
    item.delta > 0 ? "success" : ""
  )).join("");
}

function renderApiChecks(run) {
  if (!run || !run.api_checks.length) {
    elements.apiChecks.innerHTML = `<div class="empty-state">API confirmation checks will appear after replay.</div>`;
    return;
  }
  elements.apiChecks.innerHTML = run.api_checks.map((check) => `
    <article class="stack-item">
      <div class="metric-topline">
        <strong>${check.name}</strong>
        <span class="pill ${check.status === "success" ? "success" : "danger"}">${check.status}</span>
      </div>
      <div class="source-meta">${check.detail}</div>
    </article>
  `).join("");
}

function renderIntegration() {
  const run = getActiveRun();
  if (run) {
    elements.heroRunTitle.textContent = `Run ${run.run_id}`;
    elements.heroRunCopy.textContent = `${run.status}. ${formatNumber(run.processed_events)} of ${formatNumber(run.total_events)} events processed across ${run.source_systems.join(", ")}.`;
  } else {
    elements.heroRunTitle.textContent = "No simulation selected";
    elements.heroRunCopy.textContent = "Start a synthetic run below or open one of the recent runs to watch source data enter the app.";
  }

  renderPipeline(run);
  renderRuns(run);
  renderRunPatients(run);
  renderStream(run);
  renderDatabaseImpact(run);
  renderApiChecks(run);
}

async function loadPTL() {
  const params = new URLSearchParams({
    page: "1",
    per_page: "20",
    sort_by: "breach_risk",
  });
  if (state.ptlFilters.search) {
    params.set("search", state.ptlFilters.search);
  }
  if (state.ptlFilters.pathway_status) {
    params.set("pathway_status", state.ptlFilters.pathway_status);
  }
  if (state.ptlFilters.breach_risk) {
    params.set("breach_risk", state.ptlFilters.breach_risk);
  }
  const ptl = await apiFetch(`/api/v1/ptl?${params.toString()}`);
  state.ptl = ptl;
  return ptl;
}

async function loadDashboardData() {
  const [dashboard, integration, actions, ptl, catalog, runs] = await Promise.all([
    apiFetch("/api/v1/dashboard/performance"),
    apiFetch("/api/v1/integration/status"),
    apiFetch("/api/v1/actions"),
    loadPTL(),
    apiFetch("/api/v1/simulation/catalog", {}, false),
    apiFetch("/api/v1/simulation/runs", {}, false),
  ]);
  state.dashboard = dashboard;
  state.integration = integration;
  state.actions = actions;
  state.catalog = catalog;
  state.runs = runs;

  if (!state.activeRunId && state.runs.length) {
    state.activeRunId = state.runs[0].run_id;
  }
  renderSourceOptions();
  if (state.activeRunId) {
    await loadRun(state.activeRunId);
  } else {
    renderIntegration();
  }
  renderOverview();
  renderActions();
  renderPTL();
}

async function loadRun(runId) {
  const run = await apiFetch(`/api/v1/simulation/runs/${runId}`, {}, false);
  const index = state.runs.findIndex((item) => item.run_id === runId);
  if (index >= 0) {
    state.runs[index] = run;
  } else {
    state.runs.unshift(run);
  }
  state.activeRunId = runId;
  renderIntegration();
  renderOverview();

  if (run.status === "running" || run.status === "queued") {
    beginPolling(runId);
  } else {
    clearPolling();
  }
}

function beginPolling(runId) {
  clearPolling();
  state.polling = window.setInterval(async () => {
    await loadRun(runId);
    if (state.runs.find((run) => run.run_id === runId)?.status === "completed") {
      await refreshClinicalData();
    }
  }, 2000);
}

function clearPolling() {
  if (state.polling) {
    window.clearInterval(state.polling);
    state.polling = null;
  }
}

async function refreshClinicalData() {
  state.dashboard = await apiFetch("/api/v1/dashboard/performance");
  state.integration = await apiFetch("/api/v1/integration/status");
  state.actions = await apiFetch("/api/v1/actions");
  await loadPTL();
  renderOverview();
  renderPTL();
  renderActions();
  if (state.selectedPatientNhs) {
    await loadPatient(state.selectedPatientNhs, false);
  }
}

async function loadPatient(nhsNumber, scrollIntoView) {
  try {
    const patient = await apiFetch(`/api/v1/patients/${nhsNumber}`);
    state.selectedPatient = patient;
    state.selectedPatientNhs = nhsNumber;
    renderPatient();
    if (scrollIntoView) {
      document.getElementById("patient-section").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    elements.patientEmpty.innerHTML = `Could not load Patient 360: ${error.message}`;
    elements.patientEmpty.classList.remove("is-hidden");
    elements.patientContent.classList.add("is-hidden");
  }
}

async function runSearch(query) {
  if (!query || query.trim().length < 2) {
    elements.searchResults.classList.add("empty-state");
    elements.searchResults.classList.remove("has-results");
    elements.searchResults.innerHTML = "Enter at least two characters to search.";
    return;
  }
  const results = await apiFetch(`/api/v1/search?q=${encodeURIComponent(query.trim())}`);
  renderSearchResults(results);
}

async function startRun(event) {
  event.preventDefault();
  const sources = selectedSources();
  if (!sources.length) {
    elements.runFeedback.textContent = "Select at least one source system.";
    return;
  }

  const payload = {
    patient_count: Number(elements.patientCount.value),
    seed: Number(elements.seed.value),
    anchor_date: elements.anchorDate.value || null,
    source_systems: sources,
  };
  elements.runFeedback.textContent = "Starting simulation run...";
  try {
    const run = await apiFetch("/api/v1/simulation/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    }, false);
    elements.runFeedback.textContent = `Run ${run.run_id} queued. The flow view will now follow it live.`;
    state.activeRunId = run.run_id;
    state.runs.unshift(run);
    renderIntegration();
    beginPolling(run.run_id);
  } catch (error) {
    elements.runFeedback.textContent = `Could not start run: ${error.message}`;
  }
}

function bindEvents() {
  elements.refreshDashboard.addEventListener("click", refreshClinicalData);
  elements.applyPtlFilters.addEventListener("click", async () => {
    state.ptlFilters.search = elements.ptlSearch.value.trim();
    state.ptlFilters.pathway_status = elements.ptlStatus.value;
    state.ptlFilters.breach_risk = elements.ptlRisk.value;
    await loadPTL();
    renderPTL();
    renderOverview();
  });
  elements.patientSearchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runSearch(elements.patientSearchInput.value);
  });
  elements.form.addEventListener("submit", startRun);
  elements.refreshRuns.addEventListener("click", async () => {
    state.runs = await apiFetch("/api/v1/simulation/runs", {}, false);
    if (state.activeRunId) {
      await loadRun(state.activeRunId);
    } else {
      renderIntegration();
    }
  });
  elements.selectAllSources.addEventListener("click", () => {
    document.querySelectorAll('input[name="source-system"]').forEach((input) => {
      input.checked = true;
    });
  });
  elements.navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      elements.navButtons.forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      document.getElementById(button.dataset.target).scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function targetForPathname(pathname) {
  const normalized = (pathname || "/").toLowerCase();
  if (normalized === "/ptl") {
    return "ptl-section";
  }
  if (normalized === "/actions") {
    return "actions-section";
  }
  if (normalized === "/service-overview") {
    return "overview-section";
  }
  if (normalized === "/team-overview") {
    return "actions-section";
  }
  return "overview-section";
}

function setActiveNav(targetId) {
  elements.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.target === targetId);
  });
}

function focusRouteSection() {
  const targetId = targetForPathname(window.location.pathname);
  setActiveNav(targetId);
  const section = document.getElementById(targetId);
  if (section) {
    window.requestAnimationFrame(() => {
      section.scrollIntoView({ behavior: "auto", block: "start" });
    });
  }
}

function hydrateFromQueryString() {
  const params = new URLSearchParams(window.location.search);
  const nhs = params.get("nhs");
  if (nhs) {
    state.selectedPatientNhs = nhs;
  }
}

async function init() {
  hydrateFromQueryString();
  bindEvents();
  try {
    await authenticate();
  } catch (error) {
    elements.authStatus.textContent = "Error";
    elements.overviewNarrative.textContent = `The app could not initialise authentication: ${error.message}`;
    throw error;
  }
  await loadDashboardData();
  focusRouteSection();
  if (state.selectedPatientNhs) {
    await loadPatient(state.selectedPatientNhs, false);
  }
}

init().catch((error) => {
  elements.authStatus.textContent = "Error";
  elements.overviewNarrative.textContent = `The app could not initialise: ${error.message}`;
});
