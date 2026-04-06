(() => {
  const { state, esc, apiFetch } = window.C360;

  if (!state.service) {
    state.service = {
      loading: false,
      error: "",
      data: null,
      sidebarExpanded: false,
      filters: {
        pathwayType: "",
        tag: "",
        cancerSite: "",
        hospitalSite: "",
      },
      chartMode: {
        cancerSite: "pathway-age",
        byTag: "pathway-age",
        byType: "pathway-age",
      },
    };
  }

  const SECTION_COLORS = {
    d028: "#e56a9f",
    d2962: "#a8bf63",
    d63plus: "#67b6b2",
    no_value: "#a46bb6",
    total: "#4874d6",
    created: "#59d6cd",
    closed: "#6c5fd5",
    open: "#5f9e78",
    d35: "#f4d98a",
    d510: "#ebb16b",
    d10plus: "#ca7272",
  };

  function serviceIcon(name) {
    const base = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
    switch (name) {
      case "overview":
        return `<svg ${base}><path d="M4 20h16"></path><path d="M7 16v-5"></path><path d="M12 16V8"></path><path d="M17 16V5"></path><path d="m5 12 4-4 3 2 6-6"></path></svg>`;
      case "hamburger":
        return `<svg ${base}><path d="M4 7h16"></path><path d="M4 12h16"></path><path d="M4 17h16"></path></svg>`;
      case "export":
        return `<svg ${base}><rect x="4" y="4" width="16" height="16" rx="2"></rect><path d="M12 15V8"></path><path d="m9 11 3-3 3 3"></path><path d="M8 17h8"></path></svg>`;
      case "expand-diagonal":
        return `<svg ${base}><path d="M15 3h6v6"></path><path d="M9 21H3v-6"></path><path d="M21 3 14 10"></path><path d="M3 21l7-7"></path></svg>`;
      case "sidebar-arrow":
        return `<svg ${base}><path d="m9 18 6-6-6-6"></path></svg>`;
      default:
        return window.C360.icon(name);
    }
  }

  function formatCount(value) {
    return Number(value || 0).toLocaleString("en-GB");
  }

  function buildParams() {
    const params = new URLSearchParams();
    const filters = state.service.filters;
    if (filters.pathwayType) params.set("pathway_type", filters.pathwayType);
    if (filters.tag) params.set("tag", filters.tag);
    if (filters.cancerSite) params.set("cancer_site", filters.cancerSite);
    if (filters.hospitalSite) params.set("hospital_site", filters.hospitalSite);
    return params.toString();
  }

  async function loadServiceOverview() {
    state.service.loading = true;
    state.service.error = "";
    window.C360.renderApp();
    try {
      const query = buildParams();
      state.service.data = await apiFetch(query ? `/dashboard?${query}` : "/dashboard");
    } catch (error) {
      state.service.error = error.message || "Unable to load service overview.";
    } finally {
      state.service.loading = false;
      window.C360.renderApp();
    }
  }

  async function initServiceRoute() {
    await loadServiceOverview();
  }

  function renderSelect(id, value, options) {
    return `
      <select id="${id}">
        <option value="">Search...</option>
        ${(options || []).map((option) => `<option value="${esc(option)}" ${value === option ? "selected" : ""}>${esc(option)}</option>`).join("")}
      </select>
    `;
  }

  function serviceSubheader() {
    const filters = state.service.data?.filters || { pathway_types: [], tags: [], cancer_sites: [], hospital_sites: [] };
    return `
      <section class="module-subheader service-subheader">
        <div class="module-subheader-left">
          <span class="module-mark service-mark">${window.C360.icon("grid")}</span>
          <div>
            <div class="module-header-title">Service Overview</div>
            <button class="saved-state-button" type="button"><span>Saved module states</span><span class="saved-state-chevron"></span></button>
          </div>
        </div>
        <div class="module-subheader-right">
          <button class="icon-square-button service-gear" type="button">${window.C360.icon("gear")}</button>
          <div class="subheader-filter">
            <label for="service-pathway-type">Pathway Type:</label>
            <input id="service-pathway-type" class="service-subheader-input" value="${esc(state.service.filters.pathwayType)}" placeholder="Search...">
          </div>
          <div class="subheader-filter">
            <label for="service-tag">Tags:</label>
            ${renderSelect("service-tag", state.service.filters.tag, filters.tags)}
          </div>
          <div class="subheader-filter">
            <label for="service-cancer-site">Cancer Site:</label>
            ${renderSelect("service-cancer-site", state.service.filters.cancerSite, filters.cancer_sites)}
          </div>
          <div class="subheader-filter">
            <label for="service-hospital-site">Hospital Site:</label>
            ${renderSelect("service-hospital-site", state.service.filters.hospitalSite, filters.hospital_sites)}
          </div>
        </div>
      </section>
    `;
  }

  function sidebarRail() {
    return `
      <aside class="service-rail ${state.service.sidebarExpanded ? "expanded" : ""}">
        <button class="service-rail-toggle" data-action="toggle-service-rail" type="button" aria-label="Toggle monthly performance rail">
          ${serviceIcon("expand-diagonal")}
        </button>
        <div class="service-rail-label">Monthly performance</div>
      </aside>
    `;
  }

  function overviewCardHeader() {
    return `
      <div class="service-card-header">
        <div class="service-card-header-left">
          <span class="service-card-icon">${serviceIcon("overview")}</span>
          <span class="service-card-title">Overview</span>
        </div>
        <button class="service-card-menu" type="button" aria-label="Overview menu">${serviceIcon("hamburger")}</button>
      </div>
    `;
  }

  function renderKpiStrip(data) {
    const cards = [
      ["PTL Size", data?.ptl_size],
      ["0-28 Day", data?.d028],
      ["29-62 Day", data?.d2962],
      ["63+", data?.d63plus],
      ["Watchlist Pathways", data?.watchlist],
    ];
    return `
      <section class="service-section">
        <div class="service-section-title">PTL Size</div>
        <div class="service-kpi-strip">
          ${cards.map(([label, value]) => `
            <div class="service-kpi-card">
              <div class="service-kpi-label">${esc(label)}</div>
              <div class="service-kpi-value">${formatCount(value)}</div>
            </div>
          `).join("")}
        </div>
      </section>
    `;
  }

  function renderTogglePair(sectionKey, active, leftLabel, rightLabel) {
    return `
      <div class="service-toggle-pair">
        <button class="service-toggle ${active === "pathway-age" ? "active" : ""}" data-action="set-service-chart-mode" data-section="${sectionKey}" data-value="pathway-age" type="button">${esc(leftLabel)}</button>
        <button class="service-toggle ${active === "alternate" ? "active" : ""}" data-action="set-service-chart-mode" data-section="${sectionKey}" data-value="alternate" type="button">${esc(rightLabel)}</button>
      </div>
    `;
  }

  function stackedBarChart(data, options = {}) {
    const width = options.width || 820;
    const height = options.height || 440;
    const margins = { top: 28, right: 180, bottom: 92, left: 66 };
    const plotW = width - margins.left - margins.right;
    const plotH = height - margins.top - margins.bottom;
    const maxValue = options.max || Math.max(...data.map((item) => Number(item.total || 0)), 1);
    const step = options.step || Math.ceil(maxValue / 6 / 50) * 50 || 50;
    const tickCount = Math.ceil(maxValue / step);
    const slot = plotW / Math.max(data.length, 1);
    const barW = Math.min(42, slot * 0.62);
    const y = (value) => margins.top + plotH - (Number(value || 0) / maxValue) * plotH;
    const x = (index) => margins.left + (slot * index) + (slot - barW) / 2;
    const legendX = width - 152;
    const legendY = margins.top + 18;

    const grid = Array.from({ length: tickCount + 1 }, (_, i) => {
      const value = i * step;
      const pos = y(value);
      return `
        <line x1="${margins.left}" y1="${pos}" x2="${margins.left + plotW}" y2="${pos}" stroke="#dbe2ec" stroke-width="1" />
        <text x="${margins.left - 10}" y="${pos + 4}" text-anchor="end" class="service-axis-tick">${value}</text>
      `;
    }).join("");

    const bars = data.map((item, index) => {
      const values = [
        ["d028", item.d028, SECTION_COLORS.d028],
        ["d2962", item.d2962, SECTION_COLORS.d2962],
        ["d63plus", item.d63plus, SECTION_COLORS.d63plus],
        ["no_value", item.no_value, SECTION_COLORS.no_value],
      ];
      let cumulative = 0;
      const rects = values.map(([key, raw, color]) => {
        const value = Number(raw || 0);
        const h = (value / maxValue) * plotH;
        const yy = margins.top + plotH - h - ((cumulative / maxValue) * plotH);
        cumulative += value;
        if (!value) return "";
        const label = h > 18 ? `<text x="${x(index) + barW / 2}" y="${yy + 16}" text-anchor="middle" class="service-inside-label">${value}</text>` : "";
        return `<rect x="${x(index)}" y="${yy}" width="${barW}" height="${h}" fill="${color}" rx="2" />${label}`;
      }).join("");
      return `
        ${rects}
        <text x="${x(index) + barW / 2}" y="${y(item.total) - 8}" text-anchor="middle" class="service-total-label">${item.total}</text>
        <text transform="translate(${x(index) + barW / 2},${margins.top + plotH + 30}) rotate(-45)" text-anchor="end" class="service-axis-label">${esc(item.label)}</text>
      `;
    }).join("");

    const legend = [
      ["0-28", SECTION_COLORS.d028],
      ["29-62", SECTION_COLORS.d2962],
      ["63+", SECTION_COLORS.d63plus],
      ["No Value", SECTION_COLORS.no_value],
    ].map(([label, color], idx) => `
      <rect x="${legendX}" y="${legendY + 44 + idx * 28}" width="18" height="10" fill="${color}" rx="2" />
      <text x="${legendX + 28}" y="${legendY + 53 + idx * 28}" class="service-legend-item">${label}</text>
    `).join("");

    return `
      <svg class="service-chart-svg" viewBox="0 0 ${width} ${height}">
        ${grid}
        <text x="24" y="${margins.top + plotH / 2}" transform="rotate(-90 24 ${margins.top + plotH / 2})" class="service-axis-title">Count</text>
        ${bars}
        <text x="${legendX}" y="${legendY}" class="service-legend-title">LEGEND</text>
        <rect x="${legendX + 72}" y="${legendY - 12}" width="76" height="24" fill="#f2f4f7" rx="3" />
        <text x="${legendX + 84}" y="${legendY + 4}" class="service-dropdown-label">Default</text>
        ${legend}
      </svg>
    `;
  }

  function lineChart(data, series, options = {}) {
    const width = options.width || 820;
    const height = options.height || 440;
    const margins = { top: 26, right: 200, bottom: 54, left: 70 };
    const plotW = width - margins.left - margins.right;
    const plotH = height - margins.top - margins.bottom;
    const maxValue = options.max || Math.max(...data.flatMap((row) => series.map((entry) => Number(row[entry.key] || 0))), 1);
    const minValue = options.min || 0;
    const range = Math.max(maxValue - minValue, 1);
    const step = options.step || Math.ceil(maxValue / 6 / 100) * 100 || 100;
    const tickCount = Math.ceil((maxValue - minValue) / step);
    const x = (index) => margins.left + (plotW * (index / Math.max(data.length - 1, 1)));
    const y = (value) => margins.top + plotH - ((Number(value || 0) - minValue) / range) * plotH;
    const tickFormatter = options.tickFormatter || ((value) => Math.round(value));
    const grid = Array.from({ length: tickCount + 1 }, (_, i) => {
      const value = minValue + i * step;
      const pos = y(value);
      return `
        <line x1="${margins.left}" y1="${pos}" x2="${margins.left + plotW}" y2="${pos}" stroke="#dbe2ec" stroke-width="1" />
        <text x="${margins.left - 10}" y="${pos + 4}" text-anchor="end" class="service-axis-tick">${tickFormatter(value)}</text>
      `;
    }).join("");

    const paths = series.map((entry) => {
      const path = data.map((row, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(row[entry.key])}`).join(" ");
      return `<path d="${path}" fill="none" stroke="${entry.color}" stroke-width="${entry.width || 3}" stroke-linejoin="round" stroke-linecap="round" />`;
    }).join("");

    const tickLabels = data.filter((_, index) => index % Math.max(Math.floor(data.length / 7), 1) === 0).map((row, index, arr) => {
      const realIndex = data.indexOf(row);
      return `<text x="${x(realIndex)}" y="${margins.top + plotH + 22}" text-anchor="middle" class="service-axis-label">${esc(row.label || row.date.slice(5, 10))}</text>`;
    }).join("");

    const referenceLine = options.referenceLine != null
      ? `<line x1="${margins.left}" y1="${y(options.referenceLine)}" x2="${margins.left + plotW}" y2="${y(options.referenceLine)}" stroke="#d35f59" stroke-width="2" stroke-dasharray="8 6" />`
      : "";

    const legendX = width - 178;
    const legendY = margins.top + 56;
    const legend = series.map((entry, index) => `
      <rect x="${legendX}" y="${legendY + index * 28}" width="18" height="10" fill="${entry.color}" rx="2" />
      <text x="${legendX + 28}" y="${legendY + 9 + index * 28}" class="service-legend-item">${esc(entry.label)}</text>
    `).join("");

    return `
      <svg class="service-chart-svg" viewBox="0 0 ${width} ${height}">
        ${grid}
        ${referenceLine}
        <text x="24" y="${margins.top + plotH / 2}" transform="rotate(-90 24 ${margins.top + plotH / 2})" class="service-axis-title">${esc(options.yTitle || "Count")}</text>
        ${paths}
        ${tickLabels}
        ${options.xTitle ? `<text x="${margins.left + plotW / 2}" y="${height - 8}" text-anchor="middle" class="service-axis-label">${esc(options.xTitle)}</text>` : ""}
        <text x="${legendX}" y="${legendY - 24}" class="service-legend-title">LEGEND</text>
        ${legend}
      </svg>
    `;
  }

  function renderChartHeader(title, controls, badgeText = "") {
    return `
      <div class="service-panel-header">
        <div class="service-panel-title-row">
          <div class="service-panel-title">${title}</div>
          ${badgeText ? `<span class="service-inline-badge">${badgeText}</span>` : ""}
          ${controls || ""}
        </div>
        <button class="service-export-button" type="button" aria-label="Export chart">${serviceIcon("export")}</button>
      </div>
    `;
  }

  function renderServicePanel(title, chartHtml, controls = "", badgeText = "") {
    return `
      <section class="service-panel">
        ${renderChartHeader(title, controls, badgeText)}
        <div class="service-panel-body">
          ${chartHtml}
        </div>
      </section>
    `;
  }

  function renderTwoChartsRow(left, right) {
    return `<div class="service-chart-row">${left}${right}</div>`;
  }

  function renderDonutChart(data) {
    const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
    let running = 0;
    const gradient = data.map((item) => {
      const start = (running / total) * 360;
      running += Number(item.value || 0);
      const end = (running / total) * 360;
      return `${item.color} ${start}deg ${end}deg`;
    }).join(", ");
    const callouts = data.slice(0, 6).map((item) => `
      <div class="service-donut-callout">
        <span class="service-donut-callout-name">${esc(item.label.length > 22 ? `${item.label.slice(0, 22)}...` : item.label)}</span>
        <span class="service-donut-callout-pct">${item.percentage}%</span>
      </div>
    `).join("");
    return `
      <div class="service-donut-layout">
        <div class="service-donut-visual">
          <div class="service-donut-ring" style="background: conic-gradient(${gradient});">
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

  function renderTeamBars(data) {
    const maxValue = Math.max(...data.map((item) => Number(item.total || 0)), 1);
    const axisTicks = [0, 100, 200, 300, 400];
    return `
      <div class="service-team-chart">
        <div class="service-team-grid">
          <div class="service-team-axis">
            ${axisTicks.map((tick) => `<span style="left:${(tick / 400) * 100}%">${tick}</span>`).join("")}
          </div>
          ${data.map((item, index) => {
            const openPct = (item.open / maxValue) * 100;
            const d35Pct = (item.d35 / maxValue) * 100;
            const d510Pct = (item.d510 / maxValue) * 100;
            const d10Pct = (item.d10plus / maxValue) * 100;
            return `
              <div class="service-team-row">
                <div class="service-team-label">${index === 0 ? `${esc(item.label)} ${serviceIcon("sidebar-arrow")}` : esc(item.label)}</div>
                <div class="service-team-bar-shell">
                  <div class="service-team-segment seg-open" style="width:${openPct}%">${item.open || ""}</div>
                  <div class="service-team-segment seg-d35" style="width:${d35Pct}%">${item.d35 || ""}</div>
                  <div class="service-team-segment seg-d510" style="width:${d510Pct}%">${item.d510 || ""}</div>
                  <div class="service-team-segment seg-d10plus" style="width:${d10Pct}%">${item.d10plus || ""}</div>
                </div>
                <div class="service-team-total">${item.total}</div>
              </div>
            `;
          }).join("")}
        </div>
        <div class="service-team-legend">
          <div class="service-legend-title">LEGEND</div>
          <div class="service-legend-dropdown">Default</div>
          <div class="service-legend-row"><span class="service-legend-swatch seg-open"></span><span>Open</span></div>
          <div class="service-legend-row"><span class="service-legend-swatch seg-d35"></span><span>3-5 Days</span></div>
          <div class="service-legend-row"><span class="service-legend-swatch seg-d510"></span><span>5-10 Days Old</span></div>
          <div class="service-legend-row"><span class="service-legend-swatch seg-d10plus"></span><span>10+ Days Old</span></div>
        </div>
      </div>
    `;
  }

  function renderTrendingCloseDay(data, currentMean, lastMonthMean) {
    const line = lineChart(
      data.map((point) => ({ ...point, label: String(new Date(point.date).getFullYear()) })),
      [{ key: "value", label: "Mean close day", color: "#4874d6", width: 3 }],
      { max: 46, min: 20, step: 2, yTitle: "Average of Days Since Adjusted Pathway Start", referenceLine: 28 }
    );
    return `
      <div class="service-trend-kpi-layout">
        <div class="service-side-kpis">
          <div class="service-mini-kpi">
            <div class="service-mini-kpi-label">Current open pathways mean age</div>
            <div class="service-mini-kpi-value">Day ${currentMean}</div>
          </div>
          <div class="service-mini-kpi danger">
            <div class="service-mini-kpi-label">Mean close day for last month</div>
            <div class="service-mini-kpi-value">Day ${lastMonthMean}</div>
          </div>
        </div>
        <div class="service-trend-line">${line}</div>
      </div>
    `;
  }

  function renderOverviewContent(data) {
    return `
      <div class="service-card-body">
        ${renderKpiStrip(data.ptl_size)}
        ${renderTwoChartsRow(
          renderServicePanel(
            "# of Open Pathways x Cancer Site - Split By:",
            stackedBarChart(data.by_cancer_site, { max: 550, step: 50 }),
            renderTogglePair("cancerSite", state.service.chartMode.cancerSite, "Pathway age", "Cancer subsite")
          ),
          renderServicePanel(
            "Trending PTL Size",
            lineChart(
              data.trending_ptl_size,
              [
                { key: "total", label: "Total open pathways", color: SECTION_COLORS.total, width: 3.6 },
                { key: "d028", label: "0-28 open pathways", color: SECTION_COLORS.d028, width: 3 },
                { key: "d2962", label: "29-62 open pathways", color: SECTION_COLORS.d2962, width: 3 },
                { key: "d63plus", label: "63+ open pathways", color: SECTION_COLORS.d63plus, width: 3 },
              ],
              { max: 2800, step: 400, yTitle: "Count" }
            ),
            `<div class="service-date-controls"><span>Pathways starting from:</span><input value="Sat, May 11, 2024" readonly><input placeholder="End date" readonly></div>`
          )
        )}
        ${renderTwoChartsRow(
          renderServicePanel(
            "# Open Pathways By Tag",
            stackedBarChart(data.by_tag, { max: 2600, step: 400 }),
            renderTogglePair("byTag", state.service.chartMode.byTag, "Pathway Age", "Cancer Site")
          ),
          renderServicePanel(
            "# Open Pathways By Pathway Type",
            stackedBarChart(data.by_pathway_type, { max: 2400, step: 400 }),
            renderTogglePair("byType", state.service.chartMode.byType, "Pathway Age", "Cancer Site")
          )
        )}
        ${renderTwoChartsRow(
          renderServicePanel(
            "# of Open Actions by Type",
            renderDonutChart(data.actions_by_type),
            "",
            `Total open actions: ${formatCount(data.total_open_actions)}`
          ),
          renderServicePanel(
            "# of Open Actions by Team",
            renderTeamBars(data.actions_by_team),
            "",
            `Total open actions: ${formatCount(data.total_open_actions)}`
          )
        )}
        ${renderTwoChartsRow(
          renderServicePanel(
            "Trending Pathway Close Day",
            renderTrendingCloseDay(data.trending_close_day, data.current_open_pathways_mean_age, data.mean_close_day_last_month)
          ),
          renderServicePanel(
            "Trending Action Volume",
            lineChart(
              data.trending_action_volume.map((point) => ({ ...point, label: String(new Date(point.date).getFullYear()) })),
              [
                { key: "created", label: "Actions Created", color: SECTION_COLORS.created, width: 3.2 },
                { key: "closed", label: "Actions Closed", color: SECTION_COLORS.closed, width: 3.2 },
              ],
              { min: -5000, max: 55000, step: 10000, yTitle: "Count" }
            )
          )
        )}
      </div>
    `;
  }

  function renderServiceOverviewPage() {
    const data = state.service.data;
    const monthlyUI = window.C360.serviceMonthly || {};
    monthlyUI.ensureState?.();
    const content = !state.service.loading && data
      ? (monthlyUI.renderServiceContent
        ? monthlyUI.renderServiceContent({
            overviewHeaderHtml: overviewCardHeader(),
            overviewBodyHtml: renderOverviewContent(data),
          })
        : `${overviewCardHeader()}${renderOverviewContent(data)}`)
      : overviewCardHeader();
    return `
      <section class="view-shell route-module route-service">
        ${serviceSubheader()}
        <section class="service-overview-shell">
          ${sidebarRail()}
          <div class="service-main-column">
            <div class="service-overview-card">
              ${state.service.loading ? `<div class="loading-state">Loading Service Overview...</div>` : ""}
              ${state.service.error ? `<div class="error-state">${esc(state.service.error)}</div>` : ""}
              ${!state.service.loading && !state.service.error ? content : ""}
            </div>
          </div>
        </section>
      </section>
    `;
  }

  async function handleChange(event) {
    if (state.route !== "service") return false;
    const monthlyUI = window.C360.serviceMonthly || {};
    if (monthlyUI.handleChange && await monthlyUI.handleChange(event)) {
      return true;
    }
    const target = event.target;
    if (!target) return false;
    if (target.id === "service-tag") {
      state.service.filters.tag = target.value;
      await loadServiceOverview();
      return true;
    }
    if (target.id === "service-cancer-site") {
      state.service.filters.cancerSite = target.value;
      await loadServiceOverview();
      return true;
    }
    if (target.id === "service-hospital-site") {
      state.service.filters.hospitalSite = target.value;
      await loadServiceOverview();
      return true;
    }
    return false;
  }

  async function handleClick(event, dataset) {
    if (state.route !== "service") return false;
    const monthlyUI = window.C360.serviceMonthly || {};
    if (monthlyUI.handleClick && await monthlyUI.handleClick(dataset)) {
      return true;
    }
    switch (dataset.action) {
      case "toggle-service-rail":
        state.service.sidebarExpanded = !state.service.sidebarExpanded;
        window.C360.renderApp();
        return true;
      case "set-service-chart-mode":
        state.service.chartMode[dataset.section] = dataset.value;
        window.C360.renderApp();
        return true;
      default:
        return false;
    }
  }

  async function handleSubmit(event) {
    if (state.route !== "service") return false;
    return false;
  }

  async function handleBlur(event) {
    if (state.route !== "service") return false;
    const target = event.target;
    if (target?.id === "service-pathway-type") {
      state.service.filters.pathwayType = target.value.trim();
      await loadServiceOverview();
      return true;
    }
    return false;
  }

  window.C360.serviceUI = {
    initServiceRoute,
    renderServiceOverviewPage,
    loadServiceOverview,
    handleClick,
    handleChange,
    handleSubmit,
    handleBlur,
    serviceIcon,
    lineChart,
    formatCount,
  };
})();
