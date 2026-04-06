const workspaceState = {
  token: null,
  activeTab: "ptl",
  ptl: null,
  dashboard: null,
  actions: [],
  actionSummary: null,
  integration: null,
  selectedPatient: null,
  ptlFilters: {
    search: "",
    pathway_status: "",
    breach_risk: "",
  },
  actionFilters: {
    team: "",
    mode: "all",
  },
};

const el = {
  authStatus: document.getElementById("auth-status"),
  shellLinks: Array.from(document.querySelectorAll(".shell-link")),
  searchForm: document.getElementById("search-form"),
  searchInput: document.getElementById("search-input"),
  searchResultsPanel: document.getElementById("search-results-panel"),
  searchResults: document.getElementById("search-results"),
  tabs: Array.from(document.querySelectorAll(".tab-button")),
  tabPanels: {
    ptl: document.getElementById("tab-ptl"),
    actions: document.getElementById("tab-actions"),
    service: document.getElementById("tab-service"),
    team: document.getElementById("tab-team"),
  },
  ptlLastUpdated: document.getElementById("ptl-last-updated"),
  ptlFilterSearch: document.getElementById("ptl-filter-search"),
  ptlFilterStatus: document.getElementById("ptl-filter-status"),
  ptlFilterRisk: document.getElementById("ptl-filter-risk"),
  ptlRefresh: document.getElementById("ptl-refresh"),
  ptlSummary: document.getElementById("ptl-summary"),
  ptlBody: document.getElementById("ptl-body"),
  actionsSummary: document.getElementById("actions-summary"),
  actionsList: document.getElementById("actions-list"),
  serviceStats: document.getElementById("service-stats"),
  siteBars: document.getElementById("site-bars"),
  integrationHealth: document.getElementById("integration-health"),
  serviceNarrative: document.getElementById("service-narrative"),
  teamHighlights: document.getElementById("team-highlights"),
  teamBody: document.getElementById("team-body"),
  drawer: document.getElementById("patient-drawer"),
  drawerClose: document.getElementById("drawer-close"),
  drawerTitle: document.getElementById("drawer-title"),
  drawerSubtitle: document.getElementById("drawer-subtitle"),
  drawerSummary: document.getElementById("drawer-summary"),
  drawerProvenance: document.getElementById("drawer-provenance"),
  drawerTimeline: document.getElementById("drawer-timeline"),
  drawerActions: document.getElementById("drawer-actions"),
  drawerPathology: document.getElementById("drawer-pathology"),
  drawerTreatment: document.getElementById("drawer-treatment"),
};

function fmtNumber(value) {
  return new Intl.NumberFormat("en-GB").format(Number(value || 0));
}

function fmtDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function fmtDateTime(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
}

function daysOld(dateValue) {
  if (!dateValue) return 0;
  const now = new Date();
  const date = new Date(dateValue);
  return Math.max(Math.round((now - date) / 86400000), 0);
}

async function apiFetch(url, options = {}, auth = true) {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (auth && workspaceState.token) headers.set("Authorization", `Bearer ${workspaceState.token}`);
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  const type = response.headers.get("content-type") || "";
  return type.includes("application/json") ? response.json() : response.text();
}

async function authenticate() {
  const token = await apiFetch("/api/v1/auth/token", {
    method: "POST",
    body: JSON.stringify({ username: "workspace.user", password: "cancer360" }),
  }, false);
  workspaceState.token = token.access_token;
  el.authStatus.textContent = "Demo user ready";
}

async function loadCoreData() {
  const params = new URLSearchParams({ page: "1", per_page: "200", sort_by: "breach_risk" });
  if (workspaceState.ptlFilters.search) params.set("search", workspaceState.ptlFilters.search);
  if (workspaceState.ptlFilters.pathway_status) params.set("pathway_status", workspaceState.ptlFilters.pathway_status);
  if (workspaceState.ptlFilters.breach_risk) params.set("breach_risk", workspaceState.ptlFilters.breach_risk);

  const actionParams = new URLSearchParams({ view_scope: "all" });
  const [ptl, dashboard, actionsWorklist, integration] = await Promise.all([
    apiFetch(`/api/v1/ptl?${params.toString()}`),
    apiFetch("/api/v1/dashboard/performance"),
    apiFetch(`/api/v1/actions/worklist?${actionParams.toString()}`),
    apiFetch("/api/v1/integration/status"),
  ]);
  workspaceState.ptl = ptl;
  workspaceState.dashboard = dashboard;
  workspaceState.actions = actionsWorklist.items || [];
  workspaceState.actionSummary = actionsWorklist.summary || null;
  workspaceState.integration = integration;
  syncRouteState();
  renderAll();
}

function renderAll() {
  renderPTL();
  renderActions();
  renderServiceOverview();
  renderTeamOverview();
}

function renderPTL() {
  const ptl = workspaceState.ptl;
  if (!ptl) return;
  el.ptlLastUpdated.textContent = `PTL last refreshed ${fmtDateTime(new Date().toISOString())}`;
  const summary = ptl.summary;
  const chips = [
    ["PTL size", summary.total],
    ["Breached", summary.breached],
    ["High risk", summary.high_risk],
    ["Awaiting MDT", summary.awaiting_mdt],
    ["Awaiting treatment", summary.awaiting_treatment],
    ["On treatment", summary.on_treatment],
  ];
  el.ptlSummary.innerHTML = chips.map(([label, value]) => `
    <div class="summary-chip">
      <div class="summary-chip-label">${label}</div>
      <div class="summary-chip-value">${fmtNumber(value)}</div>
    </div>
  `).join("");

  if (!ptl.items.length) {
    el.ptlBody.innerHTML = `<tr><td colspan="8" class="table-empty">No PTL rows matched the selected filters.</td></tr>`;
    return;
  }
  el.ptlBody.innerHTML = ptl.items.map((row) => `
    <tr class="ptl-row" data-nhs="${row.nhs_number}">
      <td>
        <div class="patient-name">${row.patient_name}</div>
        <div class="patient-meta">${row.nhs_number}</div>
      </td>
      <td><span class="site-badge">${row.cancer_type_desc || row.cancer_type_code || "Unknown"}</span></td>
      <td>${String(row.pathway_status || "").replaceAll("_", " ")}</td>
      <td>${row.days_on_pathway ?? ""}</td>
      <td>${row.days_to_diagnosis ?? "Pending"}</td>
      <td>${row.days_to_treatment ?? "Pending"}</td>
      <td>${row.next_action || "No next action"}<div class="patient-meta">${fmtDate(row.next_action_date)}</div></td>
      <td><span class="pill ${riskTone(row.breach_risk)}">${row.assigned_team || row.breach_risk}</span></td>
    </tr>
  `).join("");
  el.ptlBody.querySelectorAll(".ptl-row").forEach((row) => row.addEventListener("click", () => openPatient(row.dataset.nhs)));
}

function renderActions() {
  const actions = workspaceState.actions || [];
  let visible = [...actions];
  if (workspaceState.actionFilters.team) {
    visible = visible.filter((item) => item.team_name === workspaceState.actionFilters.team);
  }
  if (workspaceState.actionFilters.mode === "watchlist") {
    visible = visible.filter((item) => item.is_watchlist);
  }
  if (workspaceState.actionFilters.mode === "escalated") {
    visible = visible.filter((item) => item.action_status === "Escalated");
  }

  const summary = workspaceState.actionSummary || {
    my_actions: visible.length,
    team_actions: visible.length,
    awaiting_assignment: visible.filter((item) => !item.owner).length,
    escalated_team_actions: visible.filter((item) => item.action_status === "Escalated").length,
    all_actions: visible.length,
    watchlist_only: visible.filter((item) => item.is_watchlist).length,
  };

  const overdue = visible.filter((item) => item.due_date && new Date(item.due_date) < new Date() && item.action_status !== "Completed").length;
  const stats = [
    ["My Actions", summary.my_actions, "blue", "all"],
    ["Team Actions", summary.team_actions, "amber", "all"],
    ["Escalated", summary.escalated_team_actions, summary.escalated_team_actions ? "red" : "green", "escalated"],
    ["Watchlist", summary.watchlist_only, summary.watchlist_only ? "amber" : "green", "watchlist"],
    ["Overdue", overdue, overdue ? "red" : "green", "all"],
  ];
  el.actionsSummary.innerHTML = stats.map(([label, value, tone, mode]) => `
    <button type="button" class="stat-card stat-card-button" data-mode="${mode}">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${fmtNumber(value)}</div>
      <span class="pill ${tone}">${label}</span>
    </button>
  `).join("");

  if (!visible.length) {
    el.actionsList.innerHTML = `<div class="empty-state">No open actions available.</div>`;
    return;
  }
  el.actionsList.innerHTML = visible.slice(0, 60).map((item) => `
    <article class="action-row" data-nhs="${item.nhs_number}">
      <div class="action-topline">
        <strong>${item.title}</strong>
        <span class="pill ${item.action_status === "Escalated" ? "red" : item.action_status === "Completed" ? "green" : item.priority === "high" ? "amber" : item.due_date && new Date(item.due_date) < new Date() ? "red" : "blue"}">${item.action_status}</span>
      </div>
      <div>${item.action_detail_summary || item.latest_action_comment || "No additional description."}</div>
      <div class="action-meta">${item.patient_name} | ${item.team_name || "Unassigned"} | Due ${fmtDate(item.due_date)} | Day ${item.pathway_day ?? "?"}</div>
    </article>
  `).join("");
  el.actionsSummary.querySelectorAll(".stat-card-button").forEach((button) => button.addEventListener("click", () => {
    workspaceState.actionFilters.mode = button.dataset.mode || "all";
    renderActions();
  }));
  el.actionsList.querySelectorAll(".action-row").forEach((card) => card.addEventListener("click", () => openPatient(card.dataset.nhs)));
}

function renderServiceOverview() {
  const dashboard = workspaceState.dashboard;
  const integration = workspaceState.integration;
  const ptlItems = workspaceState.ptl?.items || [];
  if (!dashboard || !integration) return;

  const stats = [
    ["PTL size", dashboard.total_pathways],
    ["Active pathways", dashboard.active_pathways],
    ["28-day FDS", dashboard.fds_28d_performance ? `${dashboard.fds_28d_performance}%` : "N/A"],
    ["62-day RTT", dashboard.rtt_62d_performance ? `${dashboard.rtt_62d_performance}%` : "N/A"],
    ["Source feeds", integration.source_status.length],
  ];
  el.serviceStats.innerHTML = stats.map(([label, value]) => `
    <div class="stat-card">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
    </div>
  `).join("");

  const grouped = {};
  ptlItems.forEach((item) => {
    const site = item.cancer_type_desc || item.cancer_type_code || "Unknown";
    if (!grouped[site]) grouped[site] = { total: 0, d028: 0, d2962: 0, d63: 0 };
    grouped[site].total += 1;
    if ((item.days_on_pathway || 0) <= 28) grouped[site].d028 += 1;
    else if ((item.days_on_pathway || 0) <= 62) grouped[site].d2962 += 1;
    else grouped[site].d63 += 1;
  });
  const siteRows = Object.entries(grouped).sort((a, b) => b[1].total - a[1].total).slice(0, 8);
  el.siteBars.innerHTML = siteRows.map(([site, counts]) => `
    <div class="site-bar-card">
      <div class="bar-header">
        <strong>${site}</strong>
        <span>${counts.total}</span>
      </div>
      <div class="stack-bar">
        <span class="segment-0-28" style="width:${(counts.d028 / counts.total) * 100}%"></span>
        <span class="segment-29-62" style="width:${(counts.d2962 / counts.total) * 100}%"></span>
        <span class="segment-63" style="width:${(counts.d63 / counts.total) * 100}%"></span>
      </div>
      <div class="patient-meta">${counts.d028} in 0-28 days, ${counts.d2962} in 29-62 days, ${counts.d63} in 63+ days.</div>
    </div>
  `).join("") || `<div class="empty-state">No site distribution data available.</div>`;

  el.integrationHealth.innerHTML = integration.source_status.map((source) => `
    <div class="health-card">
      <div class="health-header">
        <strong>${source.source_system}</strong>
        <span class="pill ${source.error_count ? "red" : "green"}">${source.error_count ? "Attention" : "Healthy"}</span>
      </div>
      <div class="patient-meta">${fmtNumber(source.success_count)} success, ${fmtNumber(source.error_count)} error, last event ${fmtDateTime(source.last_event_at)}</div>
    </div>
  `).join("");

  el.serviceNarrative.innerHTML = `
    ${fmtNumber(dashboard.active_pathways)} pathways are active in the current service view. The integration layer has logged
    ${fmtNumber(integration.audit_total)} audit events with ${fmtNumber(integration.dlq_pending)} pending DLQ rows. These
    same source feeds are what drive the PTL, actions, and Patient 360 drawer in this workspace.
  `;
}

function renderTeamOverview() {
  const openActions = (workspaceState.actions || []).filter((item) => item.action_status !== "Completed");
  const teamMap = {};
  openActions.forEach((action) => {
    const team = action.team_name || "Unassigned";
    if (!teamMap[team]) {
      teamMap[team] = { team, open: 0, escalated: 0, d03: 0, d35: 0, d510: 0, d10: 0 };
    }
    const age = daysOld(action.last_updated || action.due_date);
    teamMap[team].open += 1;
    if (action.action_status === "Escalated") {
      teamMap[team].escalated += 1;
    }
    if (age <= 3) teamMap[team].d03 += 1;
    else if (age <= 5) teamMap[team].d35 += 1;
    else if (age <= 10) teamMap[team].d510 += 1;
    else teamMap[team].d10 += 1;
  });
  const teams = Object.values(teamMap).sort((a, b) => b.open - a.open);
  const stale = [...teams].sort((a, b) => b.d10 - a.d10).slice(0, 3);
  const volume = [...teams].sort((a, b) => b.open - a.open).slice(0, 3);
  el.teamHighlights.innerHTML = `
    <div class="highlight-card">
      <div class="highlight-header"><strong>Most open 10+ day actions</strong></div>
      ${stale.map((item, index) => `<div class="patient-meta">${index + 1}. ${item.team} (${item.d10})</div>`).join("") || `<div class="patient-meta">No stale actions.</div>`}
    </div>
    <div class="highlight-card">
      <div class="highlight-header"><strong>Highest open action volume</strong></div>
      ${volume.map((item, index) => `<div class="patient-meta">${index + 1}. ${item.team} (${item.open})</div>`).join("") || `<div class="patient-meta">No open actions.</div>`}
    </div>
  `;
  if (!teams.length) {
    el.teamBody.innerHTML = `<tr><td colspan="7" class="table-empty">No team metrics available.</td></tr>`;
    return;
  }
  el.teamBody.innerHTML = teams.slice(0, 20).map((item) => `
    <tr class="team-row" data-team="${item.team}">
      <td>${item.team}</td>
      <td>${item.open}</td>
      <td>${item.escalated}</td>
      <td>${item.d03}</td>
      <td>${item.d35}</td>
      <td>${item.d510}</td>
      <td>${item.d10}</td>
    </tr>
  `).join("");
  el.teamBody.querySelectorAll(".team-row").forEach((row) => row.addEventListener("click", () => {
    workspaceState.actionFilters.team = row.dataset.team;
    workspaceState.actionFilters.mode = "all";
    switchTab("actions", false);
  }));
}

async function openPatient(nhsNumber) {
  const data = await apiFetch(`/api/v1/patients/${nhsNumber}`);
  workspaceState.selectedPatient = data;
  el.drawer.classList.remove("hidden-drawer");
  el.drawerTitle.textContent = `${data.patient.surname}, ${data.patient.forename}`;
  el.drawerSubtitle.textContent = `${data.patient.nhs_number} | ${data.pathway?.cancer_type_desc || "Unknown cancer type"} | ${String(data.pathway?.pathway_status || "unknown").replaceAll("_", " ")}`;
  el.drawerSummary.innerHTML = renderDefinition([
    ["NHS number", data.patient.nhs_number],
    ["Hospital number", data.patient.hospital_number || "Not populated"],
    ["DOB", fmtDate(data.patient.date_of_birth)],
    ["Cancer site", data.pathway?.cancer_type_desc || data.pathway?.cancer_type_code || "Not available"],
    ["Pathway day", data.pathway?.days_on_pathway ?? "Not available"],
    ["Breach risk", data.pathway?.breach_risk || "Not available"],
    ["Assigned team", data.pathway?.assigned_team || "Not available"],
    ["Next action", data.pathway?.next_action || "Not available"],
  ]);
  el.drawerProvenance.innerHTML = provenanceItems(data).map((item) => `
    <div class="drawer-item">
      <strong>${item.label}</strong>
      <div class="patient-meta">${item.count} records</div>
      <div class="patient-meta">${item.detail}</div>
    </div>
  `).join("");
  el.drawerTimeline.innerHTML = renderDrawerList((data.timeline || []).slice(0, 8), (item) => `
    <strong>${item.label}</strong>
    <div class="patient-meta">${fmtDate(item.event_date)} | ${item.source_system || "System"}</div>
    <div>${item.detail || ""}</div>
  `);
  const actionItems = [...(data.navigation_actions || []), ...(data.actions || []).slice(0, 4)];
  el.drawerActions.innerHTML = renderDrawerList(actionItems, (item) => `
    <strong>${item.action_type}</strong>
    <div class="patient-meta">${item.status} | ${item.priority} | ${item.source_system || "Cancer 360"}</div>
    <div>${item.action_description || item.notes || ""}</div>
  `);
  el.drawerPathology.innerHTML = renderDrawerList((data.pathology_results || []).slice(0, 6), (item) => `
    <strong>${item.test_name || item.discipline || "Pathology"}</strong>
    <div class="patient-meta">${fmtDateTime(item.report_date || item.specimen_date)}</div>
    <div>${item.narrative_report || item.status}</div>
  `);
  const treatment = [
    ...(data.radiology_results || []).slice(0, 3).map((item) => `${item.exam_description || item.modality || "Radiology"}|${fmtDateTime(item.report_date || item.exam_date)}|${item.conclusion || item.status}`),
    ...(data.sact_courses || []).slice(0, 2).map((item) => `${item.regimen_name || "SACT course"}|${fmtDate(item.start_date)}|${item.course_status}`),
    ...(data.rt_courses || []).slice(0, 2).map((item) => `${item.treatment_site || "RT course"}|${fmtDate(item.first_fraction_date)}|${item.course_status}`),
  ];
  el.drawerTreatment.innerHTML = renderDrawerList(treatment, (item) => {
    const [title, meta, body] = String(item).split("|");
    return `<strong>${title}</strong><div class="patient-meta">${meta}</div><div>${body}</div>`;
  });
}

function renderDefinition(rows) {
  return rows.map(([label, value]) => `<div class="label">${label}</div><div>${value}</div>`).join("");
}

function renderDrawerList(items, renderFn) {
  if (!items.length) return `<div class="empty-state">No records available.</div>`;
  return items.map((item) => `<div class="drawer-item">${renderFn(item)}</div>`).join("");
}

function provenanceItems(data) {
  return [
    { label: "Somerset", count: (data.navigation_actions || []).filter((item) => item.source_system === "Somerset").length + (data.mdt_discussions || []).length, detail: "Pathway, MDT, and navigation context." },
    { label: "ICE / WinPath", count: (data.pathology_results || []).length, detail: "Pathology and structured histology." },
    { label: "RIS / CRIS", count: (data.radiology_results || []).length, detail: "Radiology reports and conclusions." },
    { label: "Aria", count: (data.sact_courses || []).length + (data.rt_courses || []).length, detail: "Treatment courses, cycles, and fractions." },
    { label: "Endoscopy", count: (data.navigation_actions || []).filter((item) => item.source_system === "Endoscopy").length, detail: "Endoscopy-derived navigation tasks." },
  ];
}

function riskTone(risk) {
  if (risk === "breached" || risk === "high") return "red";
  if (risk === "medium") return "amber";
  return "green";
}

async function searchPatients(query) {
  if (!query || query.trim().length < 2) {
    el.searchResults.classList.remove("has-results");
    el.searchResults.classList.add("empty-state");
    el.searchResults.textContent = "Enter at least two characters to search.";
    return;
  }
  const results = await apiFetch(`/api/v1/search?q=${encodeURIComponent(query.trim())}`);
  el.searchResultsPanel.classList.remove("hidden-panel");
  if (!results.length) {
    el.searchResults.classList.remove("has-results");
    el.searchResults.classList.add("empty-state");
    el.searchResults.textContent = "No matching patients found.";
    return;
  }
  el.searchResults.classList.remove("empty-state");
  el.searchResults.classList.add("has-results");
  el.searchResults.innerHTML = results.map((patient) => `
    <button type="button" class="search-patient" data-nhs="${patient.nhs_number}">
      <div class="patient-name">${patient.surname}, ${patient.forename}</div>
      <div class="patient-meta">${patient.nhs_number} | ${fmtDate(patient.date_of_birth)}</div>
    </button>
  `).join("");
  el.searchResults.querySelectorAll(".search-patient").forEach((button) => button.addEventListener("click", () => openPatient(button.dataset.nhs)));
}

function switchTab(tabId) {
  workspaceState.activeTab = tabId;
  el.tabs.forEach((button) => button.classList.toggle("active", button.dataset.tab === tabId));
  Object.entries(el.tabPanels).forEach(([key, panel]) => panel.classList.toggle("hidden-tab", key !== tabId));
  const pathname = (window.location.pathname || "/app").toLowerCase();
  const routeKey = pathname === "/" || pathname === "/app" ? "app"
    : pathname === "/ptl" ? "ptl"
    : pathname === "/actions" ? "actions"
    : pathname === "/service-overview" ? "service"
    : pathname === "/team-overview" ? "team"
    : "app";
  el.shellLinks.forEach((link) => link.classList.toggle("active", link.dataset.route === routeKey));
}

function routeToTab(pathname) {
  const normalized = (pathname || "/app").toLowerCase();
  if (normalized === "/" || normalized === "/app") return "ptl";
  if (normalized === "/ptl") return "ptl";
  if (normalized === "/actions") return "actions";
  if (normalized === "/service-overview") return "service";
  if (normalized === "/team-overview") return "team";
  return "ptl";
}

function syncRouteState() {
  switchTab(routeToTab(window.location.pathname));
}

function bindEvents() {
  el.tabs.forEach((button) => button.addEventListener("click", () => {
    const routeMap = { ptl: "/ptl", actions: "/actions", service: "/service-overview", team: "/team-overview" };
    const target = routeMap[button.dataset.tab] || "/app";
    window.location.assign(target);
  }));
  el.searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await searchPatients(el.searchInput.value);
  });
  el.ptlRefresh.addEventListener("click", async () => {
    workspaceState.ptlFilters.search = el.ptlFilterSearch.value.trim();
    workspaceState.ptlFilters.pathway_status = el.ptlFilterStatus.value;
    workspaceState.ptlFilters.breach_risk = el.ptlFilterRisk.value;
    await loadCoreData();
  });
  el.drawerClose.addEventListener("click", () => el.drawer.classList.add("hidden-drawer"));
  el.drawer.addEventListener("click", (event) => {
    if (event.target === el.drawer) el.drawer.classList.add("hidden-drawer");
  });
}

async function hydrateQuery() {
  const params = new URLSearchParams(window.location.search);
  const nhs = params.get("nhs");
  if (nhs) {
    await openPatient(nhs);
  }
}

async function init() {
  bindEvents();
  await authenticate();
  await loadCoreData();
  syncRouteState();
  await hydrateQuery();
}

init().catch((error) => {
  el.authStatus.textContent = `Initialisation failed: ${error.message}`;
});
