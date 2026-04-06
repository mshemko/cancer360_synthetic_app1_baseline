(() => {
  const { state, esc, formatDate, icon, MODULES } = window.C360;

  function uniqueSortedValues(rows, key) {
    return [...new Set(rows.map((row) => row[key]).filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)));
  }

  function formatNullableDate(value) {
    return value ? esc(formatDate(value)) : '<span class="null-value">No value</span>';
  }

  function toneForPathwayDays(value) {
    const days = Number(value || 0);
    if (days >= 105) return "tone-age-high";
    if (days >= 63) return "tone-age-medium";
    return "";
  }

  function dateTone(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const now = new Date();
    if (date < now) {
      const days = Math.round((now - date) / 86400000);
      return days > 45 ? "danger-date" : "warning-date";
    }
    return "";
  }

  function getPtlTabCounts(rows) {
    return {
      full: rows.length,
      zeroTwentyEight: rows.filter((row) => Number(row.days_on_pathway || 0) <= 28).length,
      twentyNineSixtyTwo: rows.filter((row) => {
        const days = Number(row.days_on_pathway || 0);
        return days >= 29 && days <= 62;
      }).length,
      sixtyThreePlus: rows.filter((row) => Number(row.days_on_pathway || 0) >= 63).length,
      oneHundredFivePlus: rows.filter((row) => Number(row.days_on_pathway || 0) >= 105).length,
      watchlist: rows.filter((row) => row.watchlist_reason).length,
    };
  }

  function getVisiblePtlRows() {
    let rows = getBaseFilteredRows();
    switch (state.ptl.activeTab) {
      case "zeroTwentyEight":
        return rows.filter((row) => Number(row.days_on_pathway || 0) <= 28);
      case "twentyNineSixtyTwo":
        return rows.filter((row) => {
          const days = Number(row.days_on_pathway || 0);
          return days >= 29 && days <= 62;
        });
      case "sixtyThreePlus":
        return rows.filter((row) => Number(row.days_on_pathway || 0) >= 63);
      case "oneHundredFivePlus":
        return rows.filter((row) => Number(row.days_on_pathway || 0) >= 105);
      case "watchlist":
        return rows.filter((row) => row.watchlist_reason);
      default:
        return rows;
    }
  }

  function getBaseFilteredRows() {
    let rows = [...state.ptl.rows];
    if (state.ptl.filters.pathwayTag) {
      rows = rows.filter((row) => (row.tags || []).includes(state.ptl.filters.pathwayTag));
    }
    return rows;
  }

  function getPtlSidebarStats() {
    const rows = state.ptl.rows;
    const tags = new Set();
    rows.forEach((row) => (row.tags || []).forEach((tag) => tags.add(tag)));
    return {
      total: rows.length,
      openCount: rows.filter((row) => row.pathway_status !== "completed").length,
      closedCount: rows.filter((row) => row.pathway_status === "completed").length,
      watchlist: rows.filter((row) => row.watchlist_reason).length,
      trackingCount: rows.filter((row) => row.latest_tracking_comment).length,
      actionCount: rows.reduce((sum, row) => sum + Number(row.open_action_count || 0), 0),
      outpatientCount: rows.filter((row) => row.first_outpatient_attended_date || row.next_outpatient_attended_date).length,
      inpatientCount: rows.filter((row) => row.latest_inpatient_encounter_tci_date).length,
      radiologyCount: rows.filter((row) => row.latest_radiology_attended_date).length,
      histologyCount: rows.filter((row) => row.latest_histology_attended_date).length,
      testCount: rows.filter((row) => row.latest_histology_attended_date || row.latest_radiology_attended_date).length,
      iptCount: rows.filter((row) => row.latest_ipt_date).length,
      tagCount: tags.size,
    };
  }

  function renderSelectFilter(label, id, value, options, compact = false) {
    return `
      <div class="subheader-filter ${compact ? "compact-filter" : ""}">
        <label for="${id}">${label}:</label>
        <select id="${id}">
          <option value="">Search...</option>
          ${options.map((option) => `<option value="${esc(option)}" ${value === option ? "selected" : ""}>${esc(option)}</option>`).join("")}
        </select>
      </div>
    `;
  }

  function renderLandingPage() {
    return `
      <section class="view-shell route-landing">
        <div class="landing-logo">
          <div class="landing-logo-mark">NHS</div>
          <div class="landing-logo-text">Federated Data Platform</div>
        </div>
        <form id="landing-search-form" class="landing-search surface">
          <select class="landing-search-select" name="scope"><option>All</option></select>
          <button class="landing-search-button" type="submit" aria-label="Search">${icon("search")}</button>
          <input id="landing-search-input" name="search" placeholder="Search object types and properties..." value="${esc(state.ptl.filters.search)}">
          <button class="landing-help-button" type="button" aria-label="Help">${icon("help")}</button>
        </form>
        <section class="landing-canvas">
          <div class="module-grid">
            ${MODULES.map((module) => `
              <a class="module-card" href="${module.route}">
                <div class="module-card-hero module-icon-${module.heroIcon}" style="background:${module.color}">${icon(module.heroIcon)}</div>
                <div class="module-card-body">
                  <span class="module-mini-icon" style="background:${module.color}">${icon(module.miniIcon)}</span>
                  <div>
                    <div class="module-card-title">${esc(module.title)}</div>
                    <div class="module-card-subtitle">${esc(module.subtitle)}</div>
                  </div>
                </div>
              </a>
            `).join("")}
          </div>
          <aside class="landing-sidebar">
            <div class="landing-sidebar-item">
              <span class="landing-sidebar-icon">${icon("gear")}</span>
              <div><div class="sidebar-item-title">Cancer Settings</div><div class="sidebar-item-subtitle">Configure cancer module</div></div>
            </div>
            <div class="landing-sidebar-item">
              <span class="landing-sidebar-icon">${icon("book")}</span>
              <div><div class="sidebar-item-title">User Guides</div><div class="sidebar-item-subtitle">User guides and documentation for Cancer 360</div></div>
            </div>
          </aside>
        </section>
      </section>
    `;
  }

  function renderPtlCell(row, key) {
    if (key === "select") return '<input class="row-checkbox" type="checkbox" aria-label="Select row">';
    if (key === "days_on_pathway") return `<span class="cell-emphasis ${toneForPathwayDays(row.days_on_pathway)}">${esc(row.days_on_pathway ?? "No value")}</span>`;
    if (key === "recent_action_update") return `<span class="${row.recent_action_update ? "tone-yes" : "tone-no"}">${row.recent_action_update ? "Yes" : "No"}</span>`;
    if (key === "latest_tracking_comment") return `<div class="comment-cell">${row.latest_tracking_comment ? esc(row.latest_tracking_comment) : '<span class="null-value">No value</span>'}</div>`;
    if (key === "pathway_status") {
      const benign = row.pathway_status === "completed" || row.pathway_status === "active_monitoring";
      return `<span class="status-pill ${benign ? "status-benign" : "status-suspected"}">${benign ? "Benign" : "Suspected"}</span>`;
    }
    if (key === "breach_date_28" || key === "breach_date_31" || key === "breach_date_62") {
      return row[key] ? `<span class="${dateTone(row[key])}">${esc(formatDate(row[key]))}</span>` : '<span class="null-value">No value</span>';
    }
    if (["first_outpatient_attended_date", "next_outpatient_attended_date", "latest_histology_attended_date", "latest_radiology_attended_date", "latest_inpatient_encounter_tci_date"].includes(key)) {
      return formatNullableDate(row[key]);
    }
    if (key === "latest_ipt_date") return row.latest_ipt_date ? `<span class="ipt-pill"><span class="ipt-pill-dot"></span>${esc(row.latest_ipt_date)}</span>` : '<span class="null-value">No value</span>';
    if (key === "tags") return row.tags?.length ? esc(row.tags.join(" | ")) : '<span class="null-value">No value</span>';
    if (key === "watchlist_reason") return row.watchlist_reason ? esc(row.watchlist_reason) : '<span class="null-value">No value</span>';
    if (key === "hospital_number") return esc(row.hospital_number || "No value");
    return row[key] !== null && row[key] !== undefined && row[key] !== "" ? esc(row[key]) : '<span class="null-value">No value</span>';
  }

  function renderPtlTable(rows) {
    const columns = [
      { key: "select", label: "", width: 48, sticky: "sticky-left-0" },
      { key: "days_on_pathway", label: "Pathway Day", width: 112, sticky: "sticky-left-48" },
      { key: "patient_name", label: "Full Name", width: 250, sticky: "sticky-left-160" },
      { key: "nhs_number", label: "Nhs Number", width: 150 },
      { key: "hospital_number", label: "Mrn", width: 150 },
      { key: "age", label: "Age", width: 90 },
      { key: "cancer_site", label: "Cancer Site", width: 160 },
      { key: "cancer_sub_site", label: "Cancer Sub Site", width: 170 },
      { key: "hospital_site", label: "Hospital Site", width: 130 },
      { key: "open_action_count", label: "# Open Actions", width: 130 },
      { key: "latest_action", label: "Latest Action", width: 220 },
      { key: "recent_action_update", label: "Recent Action Update", width: 140 },
      { key: "latest_tracking_comment", label: "Latest Tracking Comment", width: 360 },
      { key: "pathway_status", label: "Pathway Status", width: 150 },
      { key: "breach_date_28", label: "28 Day Breach Date", width: 180 },
      { key: "breach_date_31", label: "31 Day Breach Date", width: 180 },
      { key: "breach_date_62", label: "62 Day Breach Date", width: 180 },
      { key: "first_outpatient_attended_date", label: "First Op Appt Attended Date", width: 200 },
      { key: "next_outpatient_attended_date", label: "Next Op Appt Attended Date", width: 190 },
      { key: "latest_histology_attended_date", label: "Latest Histology Attended Date", width: 190 },
      { key: "latest_radiology_attended_date", label: "Latest Radiology Attended Date", width: 190 },
      { key: "latest_inpatient_encounter_tci_date", label: "Latest Inpatient Encounter TCI Date", width: 210 },
      { key: "latest_mdt_status", label: "Latest MDT Status", width: 150 },
      { key: "latest_ipt_date", label: "Latest IPT", width: 140 },
      { key: "tags", label: "Tags", width: 360 },
      { key: "watchlist_reason", label: "Watchlist Reason", width: 220 },
    ];

    if (!rows.length) return '<div class="empty-state">No pathways matched the current PTL filters.</div>';
    return `
      <div class="ptl-table-wrap">
        <table class="ptl-table">
          <thead><tr>${columns.map((column) => `<th class="${column.sticky ? `sticky-col sticky-head ${column.sticky}` : ""}" style="min-width:${column.width}px;width:${column.width}px">${esc(column.label)}</th>`).join("")}</tr></thead>
          <tbody>
            ${rows.map((row) => `
              <tr data-action="open-pathway" data-pathway-id="${row.pathway_id}">
                ${columns.map((column) => `<td class="${column.sticky ? `sticky-col ${column.sticky}` : ""}" style="min-width:${column.width}px;width:${column.width}px">${renderPtlCell(row, column.key)}</td>`).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderPtlPage() {
    const rows = getVisiblePtlRows();
    const counts = getPtlTabCounts(getBaseFilteredRows());
    const summary = state.ptl.summary;
    const cancerSites = uniqueSortedValues(state.ptl.rows, "cancer_site");
    const hospitalSites = uniqueSortedValues(state.ptl.rows, "hospital_site");
    const pathwayTags = [...new Set(state.ptl.rows.flatMap((row) => row.tags || []))].sort((a, b) => a.localeCompare(b));
    const pathwayTypes = ["28 Day", "31 Day", "62 Day"];
    const tabs = [
      ["full", "Full PTL", counts.full],
      ["zeroTwentyEight", "0-28 Days", counts.zeroTwentyEight],
      ["twentyNineSixtyTwo", "29-62 Days", counts.twentyNineSixtyTwo],
      ["sixtyThreePlus", "63+ Days", counts.sixtyThreePlus],
      ["oneHundredFivePlus", "105+ Days", counts.oneHundredFivePlus],
      ["watchlist", "Watchlist", counts.watchlist],
    ];

    return `
      <section class="view-shell route-module">
        <section class="module-subheader">
          <div class="module-subheader-left">
            <span class="module-mark">${icon("list")}</span>
            <div>
              <div class="module-header-title">Cancer PTL</div>
              <button class="saved-state-button" type="button"><span>Saved module states</span><span class="saved-state-chevron"></span></button>
            </div>
          </div>
          <div class="module-subheader-right">
            <button class="icon-square-button" type="button">${icon("gear")}</button>
            ${renderSelectFilter("Pathway Tags", "ptl-pathway-tags", state.ptl.filters.pathwayTag, pathwayTags)}
            ${renderSelectFilter("Cancer Sites", "ptl-cancer-site", state.ptl.filters.cancerSite, cancerSites)}
            ${renderSelectFilter("Hospital Sites", "ptl-hospital-site", state.ptl.filters.hospitalSite, hospitalSites)}
          </div>
        </section>
        <section class="module-body">
          <div class="ptl-toolbar">
            <div class="ptl-tabs">
              <button class="icon-square-button" data-action="open-filter" type="button">${icon("filter")}</button>
              ${tabs.map(([key, label, count]) => `<button class="ptl-tab ${state.ptl.activeTab === key ? "active" : ""}" data-action="set-ptl-tab" data-value="${key}" type="button">${state.ptl.activeTab === key ? icon("filter") : ""}<span>${label}</span><span class="ptl-badge">${count}</span></button>`).join("")}
            </div>
            <div class="ptl-meta-actions">
              <div class="ptl-updated-pill">${icon("clock")}<span>PTL Last Updated: ${window.C360.PTL_LAST_UPDATED}</span></div>
              <button class="refresh-square" data-action="refresh-ptl" type="button">${icon("refresh")}</button>
              <button class="create-action-button" type="button"><span class="create-action-main">${icon("plus")}Create Action</span><span class="create-action-caret">${icon("chevron-down")}</span></button>
            </div>
          </div>
          <div class="ptl-search-row">
            <div class="ptl-summary-text">${summary ? `${summary.total} pathways available, ${summary.breached} breached, ${summary.high_risk} high risk, ${summary.awaiting_mdt} awaiting MDT.` : "Loading PTL summary..."}</div>
            <form id="ptl-search-form" class="ptl-search-form"><input id="ptl-search-input" class="ptl-search-input" name="search" placeholder="Search by patient, NHS, or MRN" value="${esc(state.ptl.filters.search)}"></form>
            ${renderSelectFilter("Pathway Type", "ptl-pathway-type", state.ptl.filters.pathwayType, pathwayTypes, true)}
          </div>
          ${state.ptl.loading ? '<div class="loading-state">Loading PTL pathways...</div>' : ""}
          ${state.ptl.error ? `<div class="error-state">${esc(state.ptl.error)}</div>` : ""}
          ${!state.ptl.loading && !state.ptl.error ? renderPtlTable(rows) : ""}
        </section>
      </section>
    `;
  }

  function renderFilterDrawer() {
    if (state.route !== "ptl" || !state.ptl.sidebarOpen) return "";
    const stats = getPtlSidebarStats();
    const entities = [
      ["patient", "PATIENT", `[CDM] Patient`, stats.total, "people"],
      ["pathway", "CANCER PATHWAY", `[Cancer 360] Cancer Pathway`, stats.total, "list"],
      ["tags", "PATHWAY TAGS", `[Cancer 360] Tagging Rule`, stats.tagCount, "grid"],
      ["watchlist", "WATCHLIST", `[Cancer 360] Cancer Watchlist`, stats.watchlist, "grid"],
      ["tracking", "TRACKING COMMENTS", `[Cancer 360] Tracking Comment`, stats.trackingCount, "clipboard"],
      ["actions", "CANCER ACTIONS", `[Cancer 360] Cancer PTL Action`, stats.actionCount, "clipboard"],
      ["outpatient", "OUTPATIENT APPOINTMENTS", `[Sho-Like][Cancer 360] Outpatient Appointment`, stats.outpatientCount, "list"],
      ["inpatient", "INPATIENT PROCEDURES", `[Sho-Like][Cancer 360] Inpatient Procedure`, stats.inpatientCount, "list"],
      ["radiology", "RADIOLOGY EXAMS", `[Cancer 360] Radiology`, stats.radiologyCount, "grid"],
      ["histology", "HISTOLOGY", `[Cancer 360] Histology`, stats.histologyCount, "grid"],
      ["tests", "TEST RESULTS", `[Sho-Like][Cancer 360] Test Result`, stats.testCount, "grid"],
      ["ipt", "IPT", `[Cancer 360] ITR`, stats.iptCount, "grid"],
    ];

    return `
      <div class="filters-overlay" data-action="close-filter"></div>
      <aside class="ptl-filter-drawer">
        <div class="filter-drawer-header">
          <div class="filter-drawer-title">Filters &amp; Config</div>
          <div class="filter-inline">
            <button class="reset-button" data-action="reset-ptl-filters" type="button">${icon("refresh")}<span>Reset Filters</span></button>
            <button class="icon-square-button" data-action="close-filter" type="button">${icon("filter")}</button>
          </div>
        </div>
        <div class="filter-drawer-body">
          <div class="filter-group"><div class="filter-label">Excluded users for recent action updates</div><input class="filter-input" placeholder="Updates from selected users won't be counted"></div>
          <div class="filter-group"><div class="filter-label">Flag recent action updates for the last N days</div><div class="filter-inline"><input id="ptl-recent-days" class="filter-number" type="number" min="1" value="${esc(state.ptl.recentDays)}"><button class="mini-icon-button" type="button">${icon("refresh")}</button></div></div>
          <div class="filter-group">
            <div class="filter-label">Pathway is open</div>
            <label class="checkbox-meter"><input type="checkbox"><span>No</span><span>${stats.closedCount.toLocaleString("en-GB")}</span><span></span><div class="meter-bar"><div class="meter-fill" style="width:${stats.total ? (stats.closedCount / stats.total) * 100 : 0}%"></div></div><span></span></label>
            <label class="checkbox-meter"><input type="checkbox" checked><span>Yes</span><span>${stats.openCount.toLocaleString("en-GB")}</span><span></span><div class="meter-bar"><div class="meter-fill" style="width:${stats.total ? (stats.openCount / stats.total) * 100 : 0}%"></div></div><span></span></label>
          </div>
          ${entities.map(([key, title, label, count, iconName]) => `
            <div class="entity-accordion">
              <button class="entity-button" data-action="toggle-filter-section" data-key="${key}" type="button">
                <span class="tab-icon" data-icon="${iconName}"></span>
                <span><span class="entity-title">${title}</span><span class="entity-detail">${label} <span class="entity-count">${count.toLocaleString("en-GB")}</span></span></span>
                <span class="tab-icon" data-icon="chevron-down"></span>
              </button>
              ${state.ptl.filterSections[key] ? `<div class="entity-body">Additional filter controls for ${esc(title.toLowerCase())} can be wired here next.</div>` : ""}
            </div>
          `).join("")}
        </div>
      </aside>
    `;
  }

  function renderPlaceholderPage(title, description) {
    return `<section class="view-shell placeholder-view"><div class="placeholder-card"><div class="placeholder-title">${esc(title)}</div><div class="placeholder-text">${esc(description)}</div></div></section>`;
  }

  window.C360.views = {
    renderLandingPage,
    renderPtlPage,
    renderFilterDrawer,
    renderPlaceholderPage,
  };
})();
