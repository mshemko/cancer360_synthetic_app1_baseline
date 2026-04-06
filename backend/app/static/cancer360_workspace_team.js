(() => {
  const { state, esc, apiFetch, formatDate } = window.C360;

  if (!state.team) {
    state.team = {
      loading: false,
      error: "",
      dashboard: null,
      teamFeed: null,
      filters: {
        pathwayTag: "",
        cancerSite: "",
        hospitalSite: "",
      },
      cancerSiteCollapsed: false,
      breakdownOpen: false,
      breakdownLoading: false,
      breakdownError: "",
      breakdownTeamKey: "",
      breakdownRows: [],
      breakdownScope: "all",
    };
  }

  const TEAM_METRICS = [
    { key: "admissions", title: "Admissions", queryName: "Admissions", icon: "#d7605c", open: 307, escalated: 27, d02: 31, d310: 71, d10plus: 196, completed: 350, watchlist: 1 },
    { key: "admissions-managers", title: "Admissions Managers", queryName: "Admissions Managers", icon: "#d7605c", open: 322, escalated: 20, d02: 46, d310: 86, d10plus: 181, completed: 488, watchlist: 1 },
    { key: "cns", title: "CNS", queryName: "CNS", icon: "#d7605c", open: 295, escalated: 26, d02: 30, d310: 85, d10plus: 172, completed: 318, watchlist: 1 },
    { key: "mdt-coordinators", title: "Cancer Services - MDT Coordinators", queryName: "Cancer Services - MDT Coordinators", icon: "#d96b5f", open: 277, escalated: 19, d02: 49, d310: 97, d10plus: 124, completed: 432, watchlist: 2 },
    { key: "senior-management", title: "Cancer Services - Senior Management", queryName: "Cancer Services - Senior Management", icon: "#e4b13d", open: 324, escalated: 25, d02: 30, d310: 91, d10plus: 190, completed: 287, watchlist: 0 },
    { key: "clinical-leads", title: "Clinical Leads", queryName: "Clinical Leads", icon: "#d7605c", open: 299, escalated: 21, d02: 50, d310: 118, d10plus: 117, completed: 547, watchlist: 1 },
    { key: "endo-bookings", title: "Endoscopy Bookings Team", queryName: "Endoscopy Bookings Team", icon: "#d7605c", open: 282, escalated: 20, d02: 38, d310: 88, d10plus: 142, completed: 353, watchlist: 1 },
    { key: "endo-managers", title: "Endoscopy Managers", queryName: "Endoscopy Managers", icon: "#d7605c", open: 275, escalated: 21, d02: 76, d310: 152, d10plus: 42, completed: 897, watchlist: 0 },
    { key: "histology", title: "Histology Team", queryName: "Histology Team", icon: "#d7605c", open: 2293, escalated: 20, d02: 1171, d310: 1121, d10plus: 1, completed: 1067, watchlist: 0 },
    { key: "hospital-labs", title: "Hospital Labs/ Pathology", queryName: "Hospital Labs/Pathology", icon: "#d7605c", open: 301, escalated: 21, d02: 78, d310: 77, d10plus: 125, completed: 1056, watchlist: 0 },
    { key: "outpatient", title: "Outpatient Booking Team (COBT)", queryName: "Outpatient Booking Team...", icon: "#d7605c", open: 287, escalated: 23, d02: 265, d310: 22, d10plus: 0, completed: 1043, watchlist: 0 },
    { key: "radiology-booking", title: "Radiology Booking", queryName: "Radiology Booking", icon: "#d7605c", open: 310, escalated: 25, d02: 101, d310: 43, d10plus: 166, completed: 522, watchlist: 1 },
    { key: "radiology-managers", title: "Radiology Managers", queryName: "Radiology Managers", icon: "#d7605c", open: 302, escalated: 19, d02: 83, d310: 38, d10plus: 181, completed: 488, watchlist: 0 },
  ];

  const ACTION_TYPE_DATA = [
    { label: "Book GA Diagnostic", value: 142, color: "#4375d0" },
    { label: "Book Surgery", value: 280, color: "#c93b7a" },
    { label: "Bring Forward Endoscopy", value: 281, color: "#99bd3a" },
    { label: "Bring Forward GA Diagnostic", value: 28, color: "#9348ae" },
    { label: "Bring Forward Surgery", value: 22, color: "#4aac9e" },
    { label: "Cancel GA Diagnostic", value: 24, color: "#d4a32a" },
    { label: "Cancel OP Diagnostic", value: 288, color: "#cf4c28" },
    { label: "Chase Endoscopy Report", value: 277, color: "#6959d6" },
    { label: "Chase Histology Report", value: 244, color: "#53ab44" },
    { label: "Chase Imaging Report", value: 523, color: "#9e7740" },
    { label: "Clinical Review Required", value: 299, color: "#3f84bf" },
    { label: "Enquiry of Sample Status", value: 281, color: "#426fc7" },
    { label: "Order Endoscopy", value: 18, color: "#da3f78" },
    { label: "Reschedule GA Diagnostic", value: 310, color: "#8fb83b" },
    { label: "Reschedule Surgery", value: 14, color: "#7a3d9e" },
    { label: "Review Diagnostic Results", value: 239, color: "#4ba6a3" },
    { label: "Update Tracking Note", value: 277, color: "#d7a630" },
    { label: "Urgent Review Required", value: 325, color: "#c64f29" },
  ];

  const OPEN_ACTIONS_BY_TEAM = [
    { label: "Admissions Managers", d10plus: 188, d510: 54, d35: 32, open: 78, total: 352 },
    { label: "Hospital Labs/Pathology", d10plus: 32, d510: 78, d35: 71, open: 170, total: 351 },
    { label: "Cancer Services - Senior...", d10plus: 201, d510: 74, d35: 17, open: 47, total: 339 },
    { label: "Endoscopy Managers", d10plus: 47, d510: 92, d35: 60, open: 136, total: 335 },
    { label: "Clinical Leads", d10plus: 130, d510: 81, d35: 37, open: 87, total: 335 },
    { label: "Admissions", d10plus: 201, d510: 43, d35: 28, open: 59, total: 331 },
    { label: "Histology Team", d10plus: 35, d510: 0, d35: 64, open: 221, total: 321 },
    { label: "Endoscopy Bookings Team", d10plus: 156, d510: 59, d35: 29, open: 67, total: 311 },
    { label: "CNS", d10plus: 177, d510: 66, d35: 19, open: 49, total: 311 },
    { label: "Radiology Booking", d10plus: 65, d510: 101, d35: 43, open: 101, total: 310 },
    { label: "Outpatient Booking Team...", d10plus: 0, d510: 2, d35: 20, open: 285, total: 307 },
    { label: "Radiology Managers", d10plus: 108, d510: 73, d35: 38, open: 83, total: 302 },
    { label: "Cancer Services - MDT Coordinators", d10plus: 130, d510: 71, d35: 26, open: 75, total: 302 },
  ];

  const OPEN_ACTIONS_BY_SITE = [
    { label: "Urology", d10plus: 259, d510: 146, d35: 103, open: 276, total: 784 },
    { label: "Gynaecology", d10plus: 135, d510: 74, d35: 43, open: 152, total: 404 },
    { label: "Skin", d10plus: 121, d510: 78, d35: 41, open: 133, total: 373 },
    { label: "Upper GI", d10plus: 135, d510: 51, d35: 36, open: 137, total: 359 },
    { label: "Brain", d10plus: 128, d510: 66, d35: 36, open: 119, total: 349 },
    { label: "Colorectal", d10plus: 136, d510: 65, d35: 38, open: 98, total: 337 },
    { label: "Head and Neck", d10plus: 116, d510: 68, d35: 34, open: 107, total: 325 },
    { label: "Haematology", d10plus: 83, d510: 64, d35: 38, open: 111, total: 296 },
    { label: "Sarcoma", d10plus: 105, d510: 58, d35: 30, open: 81, total: 274 },
    { label: "Breast", d10plus: 85, d510: 39, d35: 25, open: 70, total: 219 },
    { label: "Lung", d10plus: 67, d510: 55, d35: 25, open: 63, total: 210 },
    { label: "ADOC", d10plus: 32, d510: 43, d35: 17, open: 53, total: 145 },
    { label: "CUP", d10plus: 19, d510: 14, d35: 11, open: 26, total: 70 },
    { label: "Paediatric", d10plus: 15, d510: 0, d35: 15, open: 32, total: 62 },
  ];

  function teamIcon(name) {
    const base = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
    switch (name) {
      case "flag":
        return `<svg ${base}><path d="M5 21V4"></path><path d="m5 5 5-2 4 2 5-2v9l-5 2-4-2-5 2"></path></svg>`;
      case "star":
        return `<svg ${base}><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.2 6.4 20.2l1.1-6.2L3 9.6l6.2-.9L12 3z"></path></svg>`;
      case "send":
        return `<svg ${base}><path d="m22 2-7 20-4-9-9-4 20-7z"></path><path d="M22 2 11 13"></path></svg>`;
      case "people-house":
        return `<svg ${base}><path d="M3 10 12 3l9 7"></path><path d="M5 9v10h14V9"></path><circle cx="9" cy="13" r="2"></circle><path d="M6.5 18a2.5 2.5 0 0 1 5 0"></path><circle cx="16" cy="12.5" r="1.6"></circle><path d="M14.5 17a2 2 0 0 1 3 0"></path></svg>`;
      case "export":
        return `<svg ${base}><rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="M12 15V8"></path><path d="m9 11 3-3 3 3"></path><path d="M8 17h8"></path></svg>`;
      case "collapse":
        return `<svg ${base}><path d="m15 18-6-6 6-6"></path><path d="M20 6v12"></path></svg>`;
      case "comment":
        return `<svg ${base}><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M8 8h8"></path><path d="M8 12h5"></path></svg>`;
      case "assign":
        return `<svg ${base}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M19 8v6"></path><path d="M16 11h6"></path></svg>`;
      case "check":
        return `<svg ${base}><path d="m20 6-11 11-5-5"></path></svg>`;
      case "alert":
        return `<svg ${base}><path d="M12 9v4"></path><path d="M12 17h.01"></path><path d="M10.3 3.7 2.6 18A2 2 0 0 0 4.4 21h15.2a2 2 0 0 0 1.8-3L13.7 3.7a2 2 0 0 0-3.4 0z"></path></svg>`;
      case "revoke":
        return `<svg ${base}><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>`;
      case "reassign":
        return `<svg ${base}><path d="M17 3h4v4"></path><path d="M7 21H3v-4"></path><path d="M21 7 8 20"></path><path d="M3 17 16 4"></path></svg>`;
      case "info":
        return `<svg ${base}><circle cx="12" cy="12" r="9"></circle><path d="M12 10v6"></path><path d="M12 7h.01"></path></svg>`;
      case "sort":
        return `<svg ${base}><path d="m8 6 4-4 4 4"></path><path d="M12 2v20"></path><path d="m16 18-4 4-4-4"></path></svg>`;
      default:
        return window.C360.icon(name);
    }
  }

  function formatNullableDate(value) {
    return value ? esc(formatDate(value)) : '<span class="null-value">No value</span>';
  }

  function statusClass(status) {
    const normalized = String(status || "").toLowerCase();
    if (normalized === "escalated") return "tone-escalated";
    if (normalized === "completed") return "tone-muted";
    return "tone-open";
  }

  function daysOpenClass(days) {
    if (days >= 100) return "days-danger";
    if (days >= 30) return "days-warning";
    return "days-good";
  }

  function getDashboardFilters() {
    return state.team.dashboard?.filters || { tags: [], cancer_sites: [], hospital_sites: [] };
  }

  function renderSelect(id, value, options) {
    return `
      <select id="${id}">
        <option value="">Search...</option>
        ${(options || []).map((option) => `<option value="${esc(option)}" ${value === option ? "selected" : ""}>${esc(option)}</option>`).join("")}
      </select>
    `;
  }

  function buildTrendingActionVolume() {
    const live = state.team.dashboard?.trending_action_volume;
    if (Array.isArray(live) && live.length) return live;
    const points = [];
    let created = 0;
    let closed = 0;
    const start = new Date("2021-05-01T00:00:00Z");
    for (let index = 0; index < 48; index += 1) {
      const stamp = new Date(start);
      stamp.setUTCMonth(stamp.getUTCMonth() + index);
      const surge = index > 34 ? (index - 34) * 900 : 0;
      const spike = index > 43 ? Math.pow(index - 43, 3) * 1200 : 0;
      created += 700 + (index * 35) + surge + spike;
      closed += 680 + (index * 33) + surge + Math.max(0, spike - 600);
      points.push({
        date: stamp.toISOString().slice(0, 10),
        created: Math.round(created),
        closed: Math.round(closed),
      });
    }
    return points;
  }

  function renderSubheader() {
    const filters = getDashboardFilters();
    return `
      <section class="module-subheader team-subheader">
        <div class="module-subheader-left">
          <span class="module-mark team-mark">${teamIcon("people-house")}</span>
          <div>
            <div class="module-header-title">Team Performance</div>
            <button class="saved-state-button" type="button"><span>Saved module states</span><span class="saved-state-chevron"></span></button>
          </div>
        </div>
        <div class="module-subheader-right">
          <button class="icon-square-button service-gear" type="button">${window.C360.icon("gear")}</button>
          <div class="subheader-filter">
            <label for="team-pathway-tag">Pathway Tags:</label>
            ${renderSelect("team-pathway-tag", state.team.filters.pathwayTag, filters.tags)}
          </div>
          <div class="subheader-filter">
            <label for="team-cancer-site">Cancer Site:</label>
            ${renderSelect("team-cancer-site", state.team.filters.cancerSite, filters.cancer_sites)}
          </div>
          <div class="subheader-filter">
            <label for="team-hospital-site">Hospital Site:</label>
            ${renderSelect("team-hospital-site", state.team.filters.hospitalSite, filters.hospital_sites)}
          </div>
        </div>
      </section>
    `;
  }

  function renderTopCards() {
    return `
      <section class="team-top-grid">
        <article class="team-summary-card tone-danger">
          <div class="team-summary-head">
            <span class="team-summary-icon">${teamIcon("flag")}</span>
            <div>
              <div class="team-summary-title">Most Open 10 Day Old Actions</div>
              <div class="team-summary-subtitle">Team with the most open actions over 10 days old</div>
            </div>
          </div>
          <div class="team-summary-banner danger">Admissions (196 actions)</div>
          <ol class="team-summary-ranking">
            <li>2. Cancer Services - Senior Management (190 actions)</li>
            <li>3. Admissions Managers (181 actions)</li>
          </ol>
        </article>
        <article class="team-summary-card tone-success">
          <div class="team-summary-head">
            <span class="team-summary-icon">${teamIcon("star")}</span>
            <div>
              <div class="team-summary-title">Most Completed Actions</div>
              <div class="team-summary-subtitle">Team who completed the most actions this week</div>
            </div>
          </div>
          <div class="team-summary-banner success">Histology Team (1067 actions)</div>
          <ol class="team-summary-ranking">
            <li>2. Hospital Labs/ Pathology (1056 actions)</li>
            <li>3. Outpatient Booking Team (COBT) (1043 actions)</li>
          </ol>
        </article>
        <article class="team-summary-card tone-info">
          <div class="team-summary-head">
            <span class="team-summary-icon">${teamIcon("send")}</span>
            <div>
              <div class="team-summary-title">Most Sent Actions</div>
              <div class="team-summary-subtitle">Person who sent the most actions this week</div>
            </div>
          </div>
          <div class="team-summary-banner info">${teamIcon("star")} Elia Benhamou (7395 actions)</div>
          <ol class="team-summary-ranking">
            <li>2. Will Carroll (548 actions)</li>
            <li>3. Ollie Ursell (526 actions)</li>
          </ol>
        </article>
        <div class="team-summary-side">
          <article class="team-number-card">
            <div class="team-number-label">Number of Open Actions <span class="team-mini-info">${teamIcon("info")}</span></div>
            <div class="team-number-value">3738 Actions</div>
          </article>
          <article class="team-number-card dark">
            <div class="team-number-label">Mean Age of Open Actions <span class="team-mini-info">${teamIcon("info")}</span></div>
            <div class="team-number-value">11.4 Days</div>
          </article>
        </div>
      </section>
    `;
  }

  function renderMetricsTable() {
    return `
      <section class="team-metrics-shell">
        <div class="team-section-header">
          <div class="team-section-title">Team Metrics</div>
          <button class="service-export-button" type="button">${teamIcon("export")}</button>
        </div>
        <div class="team-metrics-table-wrap">
          <table class="ptl-table team-metrics-table">
            <thead>
              <tr>
                <th>Title <span class="sort-icon">${teamIcon("sort")}</span></th>
                <th>Open Actions</th>
                <th>Escalated Actions</th>
                <th>0-2 Days</th>
                <th>3-10 Days</th>
                <th>10+ Days</th>
                <th>Completed This Week</th>
              </tr>
            </thead>
            <tbody>
              ${TEAM_METRICS.map((row) => `
                <tr data-action="open-team-breakdown" data-team-key="${row.key}">
                  <td><div class="team-title-cell"><span class="team-square" style="background:${row.icon}"></span><span>${esc(row.title)}</span></div></td>
                  <td>${row.open}</td>
                  <td>${row.escalated}</td>
                  <td>${row.d02}</td>
                  <td>${row.d310}</td>
                  <td>${row.d10plus}</td>
                  <td>${row.completed}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </section>
    `;
  }

  function renderDonutChart(data) {
    const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
    let running = 0;
    const gradient = data.map((item) => {
      const start = (running / total) * 360;
      running += Number(item.value || 0);
      const end = (running / total) * 360;
      item.percentage = Math.round((Number(item.value || 0) / total) * 1000) / 10;
      return `${item.color} ${start}deg ${end}deg`;
    }).join(", ");
    const callouts = data.slice(0, 12).map((item) => `
      <div class="service-donut-callout">
        <span class="service-donut-callout-name">${esc(item.label.length > 18 ? `${item.label.slice(0, 18)}...` : item.label)}:</span>
        <span class="service-donut-callout-pct">${item.percentage}%</span>
      </div>
    `).join("");
    return `
      <div class="service-donut-layout team-donut-layout">
        <div class="service-donut-visual">
          <div class="service-donut-ring team-donut-ring" style="background: conic-gradient(${gradient});">
            <div class="service-donut-hole"></div>
          </div>
          <div class="service-donut-callouts">${callouts}</div>
        </div>
        <div class="service-donut-legend">
          ${data.map((item) => `
            <div class="service-legend-row">
              <span class="service-legend-swatch" style="background:${item.color}"></span>
              <span>${esc(item.label)}</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderStackedBars(data, options = {}) {
    const maxValue = options.max || Math.max(...data.map((item) => Number(item.total || 0)), 1);
    const axisTicks = options.ticks || [0, 100, 200, 300, 400];
    return `
      <div class="team-bars-shell ${options.fullWidth ? "full-width" : ""}">
        <div class="team-bars-grid">
          <div class="team-bars-axis">
            ${axisTicks.map((tick) => `<span style="left:${(tick / maxValue) * 100}%">${tick}</span>`).join("")}
          </div>
          ${data.map((item, index) => {
            const redPct = (item.d10plus / maxValue) * 100;
            const orangePct = (item.d510 / maxValue) * 100;
            const yellowPct = (item.d35 / maxValue) * 100;
            const greenPct = (item.open / maxValue) * 100;
            return `
              <div class="team-bars-row">
                <div class="team-bars-label">${index === 0 && options.showSortIcon ? `${esc(item.label)} ${teamIcon("collapse")}` : esc(item.label)}</div>
                <div class="team-bars-track">
                  <div class="team-bars-segment seg-red" style="width:${redPct}%">${item.d10plus || ""}</div>
                  <div class="team-bars-segment seg-orange" style="width:${orangePct}%">${item.d510 || ""}</div>
                  <div class="team-bars-segment seg-yellow" style="width:${yellowPct}%">${item.d35 || ""}</div>
                  <div class="team-bars-segment seg-green" style="width:${greenPct}%">${item.open || ""}</div>
                </div>
                <div class="team-bars-total">${item.total}</div>
              </div>
            `;
          }).join("")}
        </div>
        <div class="team-bars-legend-wrap">
          ${options.collapseAction ? `<button class="team-collapse-button" data-action="${options.collapseAction}" type="button">${teamIcon("collapse")}</button>` : ""}
          <div class="service-team-legend">
            <div class="service-legend-title">LEGEND</div>
            <div class="service-legend-dropdown">Default</div>
            <div class="service-legend-row"><span class="service-legend-swatch seg-green"></span><span>Open</span></div>
            <div class="service-legend-row"><span class="service-legend-swatch seg-yellow"></span><span>3-5 Days</span></div>
            <div class="service-legend-row"><span class="service-legend-swatch seg-orange"></span><span>5-10 Days Old</span></div>
            <div class="service-legend-row"><span class="service-legend-swatch seg-red"></span><span>10+ Days Old</span></div>
          </div>
        </div>
      </div>
    `;
  }

  function renderPanel(title, body, badgeText = "") {
    return `
      <section class="service-panel team-panel">
        <div class="service-panel-header">
          <div class="service-panel-title-wrap">
            <div class="service-panel-title">${esc(title)}</div>
            ${badgeText ? `<span class="service-inline-badge">${esc(badgeText)}</span>` : ""}
          </div>
          <button class="service-export-button" type="button">${teamIcon("export")}</button>
        </div>
        <div class="service-panel-body">
          ${body}
        </div>
      </section>
    `;
  }

  function renderChartsRow() {
    return `
      <div class="service-chart-row">
        ${renderPanel("# of Open Actions by Type", renderDonutChart(ACTION_TYPE_DATA), "Total open actions: 3738")}
        ${renderPanel("# of Open Actions by Team", renderStackedBars(OPEN_ACTIONS_BY_TEAM, { max: 400, ticks: [0, 100, 200, 300, 400], showSortIcon: true }), "Total open actions: 3738")}
      </div>
    `;
  }

  function renderCancerSiteSection() {
    return renderPanel(
      "# of Open Actions by Cancer Site",
      state.team.cancerSiteCollapsed
        ? '<div class="team-collapsed-placeholder">Chart collapsed</div>'
        : renderStackedBars(OPEN_ACTIONS_BY_SITE, { max: 850, ticks: [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850], fullWidth: true, collapseAction: "toggle-team-cancer-site-collapse" }),
      "Total open actions: 3738"
    );
  }

  function renderTrendingVolumeSection() {
    const serviceUI = window.C360.serviceUI || {};
    const chart = serviceUI.lineChart
      ? serviceUI.lineChart(
          buildTrendingActionVolume(),
          [
            { key: "created", label: "Actions Created", color: "#59d6cd", width: 3.6 },
            { key: "closed", label: "Actions Closed", color: "#6c5fd5", width: 3.2 },
          ],
          { max: 55000, min: -5000, step: 5000, yTitle: "Count", xTitle: "Date" }
        )
      : "";
    return `
      <section class="service-panel team-panel full-width">
        <div class="service-panel-header">
          <div class="service-panel-title-wrap">
            <div class="service-panel-title">Trending Action Volume</div>
          </div>
        </div>
        <div class="service-panel-body team-trending-panel">
          <div class="team-inline-chart-controls">
            <button class="team-collapse-button" type="button">${teamIcon("collapse")}</button>
            <button class="service-export-button" type="button">${window.C360.icon("gear")}</button>
          </div>
          ${chart}
        </div>
      </section>
    `;
  }

  function renderTeamPage() {
    return `
      <section class="view-shell route-module team-route">
        ${renderSubheader()}
        <section class="module-body team-body">
          ${state.team.loading ? '<div class="loading-state">Loading team performance...</div>' : ""}
          ${state.team.error ? `<div class="error-state">${esc(state.team.error)}</div>` : ""}
          <div class="team-content-stack">
            ${renderTopCards()}
            ${renderMetricsTable()}
            ${renderChartsRow()}
            ${renderCancerSiteSection()}
            ${renderTrendingVolumeSection()}
          </div>
        </section>
      </section>
    `;
  }

  function getActiveTeamRow() {
    return TEAM_METRICS.find((row) => row.key === state.team.breakdownTeamKey) || TEAM_METRICS[0];
  }

  function buildSyntheticBreakdownRows(teamRow, sourceRows) {
    const pool = Array.isArray(sourceRows) ? sourceRows.filter(Boolean) : [];
    const templates = [
      { due_date: "", pathway_day: 1325, patient_name: "Chavez, Robert", cancer_site: "Gynaecology", mrn: "006736951", nhs_number: "5936996311", action_status: "Open", days_open: 749, pathway_status: "Benign" },
      { due_date: "2025-01-25", pathway_day: 142, patient_name: "Simpson, Deborah", cancer_site: "Sarcoma", mrn: "009763252", nhs_number: "3104110265", action_status: "Open", days_open: 85, pathway_status: "Suspected" },
      { due_date: "2025-02-09", pathway_day: 93, patient_name: "Hubbard, Jennifer", cancer_site: "Urology", mrn: "029441153", nhs_number: "6120304070", action_status: "Open", days_open: 55, pathway_status: "Suspected" },
      { due_date: "2025-03-14", pathway_day: 81, patient_name: "Gonzalez, Kimberly", cancer_site: "Sarcoma", mrn: "002681610", nhs_number: "9412335786", action_status: "Escalated", days_open: 48, pathway_status: "Suspected" },
      { due_date: "2025-03-16", pathway_day: 80, patient_name: "Perkins, Tracy", cancer_site: "Breast", mrn: "085778144", nhs_number: "5213385806", action_status: "Open", days_open: 47, pathway_status: "Suspected" },
      { due_date: "2025-03-18", pathway_day: 60, patient_name: "Martin, Angela", cancer_site: "Paediatric", mrn: "066094469", nhs_number: "4900143369", action_status: "Open", days_open: 34, pathway_status: "Suspected" },
      { due_date: "2025-03-22", pathway_day: 56, patient_name: "Harper, Megan", cancer_site: "Lung", mrn: "085414137", nhs_number: "2064915445", action_status: "Open", days_open: 33, pathway_status: "Suspected" },
      { due_date: "2025-03-24", pathway_day: 54, patient_name: "Vasquez, Amy", cancer_site: "Gynaecology", mrn: "026483336", nhs_number: "9877513266", action_status: "Open", days_open: 31, pathway_status: "Suspected" },
      { due_date: "2025-03-26", pathway_day: 54, patient_name: "Brady, Jesse", cancer_site: "Gynaecology", mrn: "008370065", nhs_number: "7304983029", action_status: "Open", days_open: 33, pathway_status: "Suspected" },
      { due_date: "2025-03-27", pathway_day: 55, patient_name: "Finley, Veronica", cancer_site: "Brain", mrn: "098697610", nhs_number: "6492561331", action_status: "Open", days_open: 33, pathway_status: "Suspected" },
    ];
    return templates.map((template, index) => {
      const fallback = pool[index % Math.max(pool.length, 1)] || {};
      return {
        ...fallback,
        action_id: fallback.action_id || `synthetic-team-${teamRow.key}-${index + 1}`,
        title: "Update Tracking Note",
        action_detail_summary: "",
        team_name: teamRow.title,
        owner: fallback.owner || "Valentina Sassow",
        pathway_is_open: true,
        ...template,
      };
    });
  }

  async function openTeamBreakdown(teamKey) {
    const teamRow = TEAM_METRICS.find((row) => row.key === teamKey) || TEAM_METRICS[0];
    state.team.breakdownOpen = true;
    state.team.breakdownLoading = true;
    state.team.breakdownError = "";
    state.team.breakdownTeamKey = teamRow.key;
    state.team.breakdownScope = "all";
    state.team.breakdownRows = [];
    state.actions.selectedIds = [];
    state.actions.activeDetail = null;
    state.actions.activePathway = null;
    state.actions.detailError = "";
    state.actions.detailLoading = false;
    state.actions.modal = null;
    window.C360.renderApp();
    try {
      let rows = [];
      try {
        const worklist = await apiFetch(`/actions/worklist?view_scope=all&watchlist_only=false&team_name=${encodeURIComponent(teamRow.queryName)}`);
        rows = Array.isArray(worklist?.items) ? worklist.items : [];
      } catch (error) {
        rows = [];
      }
      if (!rows.length) {
        const fallback = await apiFetch("/actions/worklist?view_scope=all&watchlist_only=false");
        rows = Array.isArray(fallback?.items) ? fallback.items.slice(0, 12) : [];
      }
      const decorated = buildSyntheticBreakdownRows(teamRow, rows);
      state.team.breakdownRows = decorated;
      state.actions.rows = decorated;
      state.actions.selectedIds = [];
    } catch (error) {
      state.team.breakdownError = error.message || "Unable to load team actions.";
    } finally {
      state.team.breakdownLoading = false;
      window.C360.renderApp();
    }
  }

  function getBreakdownRows() {
    const teamRow = getActiveTeamRow();
    const rows = Array.isArray(state.team.breakdownRows) ? state.team.breakdownRows : [];
    if (state.team.breakdownScope === "watchlist") {
      return rows.filter((row, index) => index < Math.max(1, teamRow.watchlist || 1));
    }
    return rows;
  }

  function renderBreakdownToolbarButton(action, label, iconName, tone, disabled = false) {
    return `
      <button class="actions-toolbar-btn ${tone}" data-action="${action}" type="button" ${disabled ? "disabled" : ""}>
        <span class="tab-icon">${teamIcon(iconName)}</span>
        <span>${esc(label)}</span>
      </button>
    `;
  }

  function renderBreakdownCell(row, key) {
    switch (key) {
      case "select":
        return `<input class="row-checkbox" data-action="toggle-action-selection" data-action-id="${esc(row.action_id)}" type="checkbox" ${state.actions.selectedIds.includes(String(row.action_id)) ? "checked" : ""}>`;
      case "due_date":
        return row.due_date ? `<span class="date-past">${esc(formatDate(row.due_date))}</span>` : '<span class="null-value">No value</span>';
      case "title":
        return `<div class="action-title-cell"><span class="action-priority-square"></span><span>${esc(row.title || "Update Tracking Note")}</span></div>`;
      case "action_detail_summary":
        return row.action_detail_summary ? esc(row.action_detail_summary) : '<span class="null-value">No value</span>';
      case "action_status":
        return `<span class="action-status-text ${statusClass(row.action_status)}">${esc(row.action_status || "Open")}</span>`;
      case "days_open":
        return `<span class="days-open-pill ${daysOpenClass(Number(row.days_open || 0))}">${esc(row.days_open ?? "0")}</span>`;
      case "pathway_is_open":
        return String(row.pathway_is_open ?? true);
      default:
        return row[key] === null || row[key] === undefined || row[key] === "" ? '<span class="null-value">No value</span>' : esc(String(row[key]));
    }
  }

  function renderBreakdownTable() {
    const rows = getBreakdownRows();
    const columns = [
      { key: "select", label: "", cls: "sticky-col sticky-head sticky-left-0 team-col-checkbox" },
      { key: "due_date", label: `Due Date ${teamIcon("sort")}`, cls: "sticky-col sticky-head sticky-left-44 team-col-due" },
      { key: "title", label: "Title", cls: "sticky-col sticky-head sticky-left-180 team-col-title" },
      { key: "action_detail_summary", label: "Action Detail Summary" },
      { key: "pathway_day", label: "Pathway Day" },
      { key: "patient_name", label: "Patient" },
      { key: "cancer_site", label: "Cancer Site" },
      { key: "mrn", label: "Mrn" },
      { key: "nhs_number", label: "Nhs Number" },
      { key: "action_status", label: "Action Status" },
      { key: "days_open", label: "Days Open" },
      { key: "pathway_is_open", label: "Pathway Is Open" },
      { key: "pathway_status", label: "Pathway Status" },
    ];
    return `
      <div class="ptl-table-wrap team-breakdown-table-wrap">
        <table class="ptl-table actions-table team-breakdown-table">
          <thead>
            <tr>
              ${columns.map((column) => `<th class="${column.cls || ""}">${column.label}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr class="actions-row" data-action="open-single-action" data-action-id="${esc(row.action_id)}">
                ${columns.map((column) => `<td class="${column.cls?.replace("sticky-head", "") || ""}">${renderBreakdownCell(row, column.key)}</td>`).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderTeamOverlay() {
    if (!state.team.breakdownOpen) return "";
    const teamRow = getActiveTeamRow();
    const hasSelection = state.actions.selectedIds.length > 0;
    return `
      <div class="team-breakdown-backdrop" data-action="close-team-breakdown"></div>
      <aside class="team-breakdown-drawer">
        <div class="team-breakdown-headbar">
          <div class="team-breakdown-title">Team Performance Breakdown</div>
          <button class="drawer-close" data-action="close-team-breakdown" type="button">${window.C360.icon("x")}</button>
        </div>
        <div class="team-breakdown-content">
          <div class="team-breakdown-heading">Actions for: ${esc(teamRow.title)}</div>
          <section class="team-breakdown-kpis">
            <article class="team-breakdown-kpi lead"><div class="team-breakdown-kpi-label">Open</div><div class="team-breakdown-kpi-value">${teamRow.open}</div></article>
            <article class="team-breakdown-kpi"><div class="team-breakdown-kpi-label">Escalated</div><div class="team-breakdown-kpi-value">${teamRow.escalated}</div></article>
            <article class="team-breakdown-kpi"><div class="team-breakdown-kpi-label">0-2 Days Old <span class="team-mini-info">${teamIcon("info")}</span></div><div class="team-breakdown-kpi-value">${teamRow.d02}</div></article>
            <article class="team-breakdown-kpi"><div class="team-breakdown-kpi-label">3-10 Days old <span class="team-mini-info">${teamIcon("info")}</span></div><div class="team-breakdown-kpi-value">${teamRow.d310}</div></article>
            <article class="team-breakdown-kpi"><div class="team-breakdown-kpi-label">10+ Days Old <span class="team-mini-info">${teamIcon("info")}</span></div><div class="team-breakdown-kpi-value">${teamRow.d10plus}</div></article>
            <article class="team-breakdown-kpi"><div class="team-breakdown-kpi-label">Closed This Week <span class="team-mini-info">${teamIcon("info")}</span></div><div class="team-breakdown-kpi-value">${teamRow.completed}</div></article>
          </section>
          <section class="team-breakdown-toolbar">
            <div class="actions-toolbar-left">
              <button class="filter-toggle-button" type="button">${window.C360.icon("filter")}</button>
              <button class="actions-scope-tab ${state.team.breakdownScope === "all" ? "active" : ""}" data-action="set-team-breakdown-scope" data-value="all" type="button">all actions <span>${teamRow.open}</span></button>
              <button class="actions-scope-tab ${state.team.breakdownScope === "watchlist" ? "active" : ""}" data-action="set-team-breakdown-scope" data-value="watchlist" type="button">watchlist only <span>${teamRow.watchlist || 0}</span></button>
            </div>
            <div class="actions-toolbar-actions">
              ${renderBreakdownToolbarButton("bulk-comment", "Add Comment", "comment", "btn-comment", !hasSelection)}
              ${renderBreakdownToolbarButton("bulk-assign", "Assign", "assign", "btn-assign", !hasSelection)}
              ${renderBreakdownToolbarButton("bulk-complete", "Complete", "check", "btn-complete", !hasSelection)}
              ${renderBreakdownToolbarButton("bulk-escalate", "Escalate", "alert", "btn-escalate", !hasSelection)}
              ${renderBreakdownToolbarButton("bulk-revoke", "Revoke", "revoke", "btn-revoke", !hasSelection)}
              ${renderBreakdownToolbarButton("bulk-reassign-team", "Reassign team", "reassign", "btn-reassign", !hasSelection)}
            </div>
          </section>
          ${state.team.breakdownLoading ? '<div class="loading-state">Loading team actions...</div>' : ""}
          ${state.team.breakdownError ? `<div class="error-state">${esc(state.team.breakdownError)}</div>` : ""}
          ${!state.team.breakdownLoading && !state.team.breakdownError ? renderBreakdownTable() : ""}
        </div>
      </aside>
    `;
  }

  async function loadTeamRoute() {
    state.team.loading = true;
    state.team.error = "";
    window.C360.renderApp();
    try {
      const dashboard = await apiFetch("/dashboard");
      let teamFeed = null;
      try {
        teamFeed = await apiFetch("/dashboard/team");
      } catch (error) {
        teamFeed = null;
      }
      state.team.dashboard = dashboard;
      state.team.teamFeed = teamFeed;
    } catch (error) {
      state.team.error = error.message || "Unable to load team performance.";
    } finally {
      state.team.loading = false;
      window.C360.renderApp();
    }
  }

  async function handleClick(event, dataset) {
    switch (dataset.action) {
      case "open-team-breakdown":
        await openTeamBreakdown(dataset.teamKey);
        return true;
      case "close-team-breakdown":
        state.team.breakdownOpen = false;
        state.team.breakdownLoading = false;
        state.team.breakdownError = "";
        state.actions.selectedIds = [];
        state.actions.modal = null;
        window.C360.renderApp();
        return true;
      case "set-team-breakdown-scope":
        state.team.breakdownScope = dataset.value || "all";
        state.actions.selectedIds = [];
        window.C360.renderApp();
        return true;
      case "toggle-team-cancer-site-collapse":
        state.team.cancerSiteCollapsed = !state.team.cancerSiteCollapsed;
        window.C360.renderApp();
        return true;
      default:
        return false;
    }
  }

  async function handleChange(event) {
    if (event.target.id === "team-pathway-tag") {
      state.team.filters.pathwayTag = event.target.value;
      window.C360.renderApp();
      return true;
    }
    if (event.target.id === "team-cancer-site") {
      state.team.filters.cancerSite = event.target.value;
      window.C360.renderApp();
      return true;
    }
    if (event.target.id === "team-hospital-site") {
      state.team.filters.hospitalSite = event.target.value;
      window.C360.renderApp();
      return true;
    }
    return false;
  }

  window.C360.teamUI = {
    initTeamRoute: loadTeamRoute,
    renderTeamPage,
    renderTeamOverlay,
    handleClick,
    handleChange,
  };
})();
