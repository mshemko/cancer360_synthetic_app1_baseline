(() => {
  const { state, esc, formatDate, formatDateTime, apiFetch } = window.C360;
  const { renderEmbeddedDrawer } = window.C360.drawer;

  if (!state.actions) {
    state.actions = {
      loading: false,
      error: "",
      rows: [],
      summary: null,
      sidebarOpen: false,
      activeSubView: "list",
      selectionScope: "all",
      selectedIds: [],
      modal: null,
      filters: {
        cancerSite: "",
        hospitalSite: "",
        actionDescription: "",
        actionDetail: "",
        actionIsOpen: "true",
        actionStatus: "",
        teamName: "",
        owner: "",
        dueAfter: "",
        dueBefore: "",
        createdAfter: "",
        createdBefore: "",
        updateFrom: "",
        updateTo: "",
        updateTypes: "",
        excludeUsers: "",
      },
      updatesLoading: false,
      updatesError: "",
      updatesItems: [],
      updatesPage: 1,
      updatesPerPage: 30,
      updatesTotal: 0,
      expandedUpdates: {},
      detailLoading: false,
      detailError: "",
      activeDetail: null,
      activePathway: null,
      embeddedDrawer: {
        activeSection: "pathway-details",
        selectedActionId: null,
        selectedReportKey: null,
        patientTab: "overview",
      },
    };
  }

  function actionIcon(name) {
    const base = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
    switch (name) {
      case "table":
        return `<svg ${base}><path d="M3 8h18"></path><path d="M3 16h18"></path><path d="M8 3v18"></path><path d="M16 3v18"></path><rect x="3" y="3" width="18" height="18" rx="2"></rect></svg>`;
      case "comment":
        return `<svg ${base}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M8 9h8"></path><path d="M8 13h5"></path></svg>`;
      case "assign":
        return `<svg ${base}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M19 8v6"></path><path d="M16 11h6"></path></svg>`;
      case "check":
        return `<svg ${base}><path d="m5 13 4 4L19 7"></path></svg>`;
      case "alert":
        return `<svg ${base}><path d="M12 9v4"></path><path d="M12 17h.01"></path><path d="M10.3 3.4 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.4a2 2 0 0 0-3.4 0z"></path></svg>`;
      case "reassign":
        return `<svg ${base}><path d="M17 1v6h6"></path><path d="M3 11V5h6"></path><path d="M21 7a8 8 0 0 0-14-4L3 5"></path><path d="M3 17a8 8 0 0 0 14 4l4-2"></path></svg>`;
      case "revoke":
        return `<svg ${base}><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>`;
      case "info":
        return `<svg ${base}><circle cx="12" cy="12" r="9"></circle><path d="M12 10v6"></path><path d="M12 7h.01"></path></svg>`;
      case "updates":
        return `<svg ${base}><path d="M3 12a9 9 0 0 1 15-6l2 2"></path><path d="M21 3v6h-6"></path><path d="M21 12a9 9 0 0 1-15 6l-2-2"></path><path d="M3 21v-6h6"></path></svg>`;
      case "clipboard-solid":
        return `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 3h6a2 2 0 0 1 2 2h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2a2 2 0 0 1 2-2Zm0 2v1h6V5H9Z"/></svg>`;
      case "sort":
        return `<svg ${base}><path d="M8 6v12"></path><path d="m5 9 3-3 3 3"></path><path d="M16 18V6"></path><path d="m13 15 3 3 3-3"></path></svg>`;
      case "chevron-right":
        return `<svg ${base}><path d="m9 18 6-6-6-6"></path></svg>`;
      default:
        return window.C360.icon(name);
    }
  }

  function setActionsError(message) {
    state.actions.error = message || "";
  }

  function parseDateTimeInput(value) {
    return value ? new Date(value).toISOString() : "";
  }

  function splitMultiValue(value) {
    return String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function isSelected(actionId) {
    return state.actions.selectedIds.includes(String(actionId));
  }

  function toggleSelection(actionId) {
    const key = String(actionId);
    state.actions.selectedIds = isSelected(key)
      ? state.actions.selectedIds.filter((item) => item !== key)
      : [...state.actions.selectedIds, key];
  }

  function clearActionSelection() {
    state.actions.selectedIds = [];
  }

  function getSelectedRows() {
    const keys = new Set(state.actions.selectedIds);
    return state.actions.rows.filter((row) => keys.has(String(row.action_id)));
  }

  function buildWorklistParams() {
    const params = new URLSearchParams({
      view_scope: "all",
      watchlist_only: String(state.actions.selectionScope === "watchlist"),
    });
    const filters = state.actions.filters;
    if (filters.cancerSite) params.set("cancer_site", filters.cancerSite);
    if (filters.hospitalSite) params.set("hospital_site", filters.hospitalSite);
    if (filters.actionDescription) params.set("action_description", filters.actionDescription);
    if (filters.actionDetail) params.set("action_detail", filters.actionDetail);
    if (filters.actionStatus) params.set("action_status", filters.actionStatus);
    if (filters.teamName) params.set("team_name", filters.teamName);
    if (filters.owner) params.set("owner", filters.owner);
    if (filters.actionIsOpen === "true") params.set("action_is_open", "true");
    if (filters.actionIsOpen === "false") params.set("action_is_open", "false");
    if (filters.dueAfter) params.set("due_after", filters.dueAfter);
    if (filters.dueBefore) params.set("due_before", filters.dueBefore);
    if (filters.createdAfter) params.set("created_after", parseDateTimeInput(filters.createdAfter));
    if (filters.createdBefore) params.set("created_before", parseDateTimeInput(filters.createdBefore));
    return params;
  }

  async function loadActionsWorklist() {
    state.actions.loading = true;
    setActionsError("");
    window.C360.renderApp();
    try {
      const data = await apiFetch(`/actions/worklist?${buildWorklistParams().toString()}`);
      state.actions.rows = data.items || [];
      state.actions.summary = data.summary || null;
      state.actions.selectedIds = state.actions.selectedIds.filter((id) => state.actions.rows.some((row) => String(row.action_id) === id));
    } catch (error) {
      setActionsError(error.message || "Unable to load actions.");
    } finally {
      state.actions.loading = false;
      window.C360.renderApp();
    }
  }

  function buildUpdateParams() {
    const params = new URLSearchParams({
      page: String(state.actions.updatesPage),
      per_page: String(state.actions.updatesPerPage),
    });
    const filters = state.actions.filters;
    if (filters.updateFrom) params.set("from_datetime", parseDateTimeInput(filters.updateFrom));
    if (filters.updateTo) params.set("to_datetime", parseDateTimeInput(filters.updateTo));
    splitMultiValue(filters.updateTypes).forEach((value) => params.append("update_type", value));
    splitMultiValue(filters.excludeUsers).forEach((value) => params.append("exclude_user", value));
    return params;
  }

  async function loadActionUpdates() {
    state.actions.updatesLoading = true;
    state.actions.updatesError = "";
    window.C360.renderApp();
    try {
      const data = await apiFetch(`/actions/recent-updates?${buildUpdateParams().toString()}`);
      state.actions.updatesItems = data.items || [];
      state.actions.updatesTotal = data.total || 0;
    } catch (error) {
      state.actions.updatesError = error.message || "Unable to load recent action updates.";
    } finally {
      state.actions.updatesLoading = false;
      window.C360.renderApp();
    }
  }

  async function loadSingleActionView(actionId) {
    if (!actionId) return;
    state.actions.detailLoading = true;
    state.actions.detailError = "";
    state.actions.activeDetail = null;
    state.actions.activePathway = null;
    state.actions.embeddedDrawer = {
      activeSection: "pathway-details",
      selectedActionId: null,
      selectedReportKey: null,
      patientTab: "overview",
    };
    window.C360.renderApp();
    try {
      const detail = await apiFetch(`/actions/${actionId}/detail`);
      state.actions.activeDetail = detail;
      if (detail?.action?.pathway_id) {
        state.actions.activePathway = await apiFetch(`/pathways/${detail.action.pathway_id}`);
      }
    } catch (error) {
      state.actions.detailError = error.message || "Unable to load action detail.";
    } finally {
      state.actions.detailLoading = false;
      window.C360.renderApp();
    }
  }

  async function reloadActiveActionsView() {
    await loadActionsWorklist();
    if (state.actions.activeSubView === "updates") {
      await loadActionUpdates();
    }
    if (state.actions.activeDetail?.action?.action_id) {
      await loadSingleActionView(state.actions.activeDetail.action.action_id);
    }
  }

  async function patchAction(actionId, payload) {
    await apiFetch(`/actions/${actionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  async function runBulkOperation(operation, config = {}) {
    const rows = config.row ? [config.row] : getSelectedRows();
    if (!rows.length) return;
    for (const row of rows) {
      if (operation === "comment") {
        await patchAction(row.action_id, {
          operation: "comment",
          comment_title: config.commentTitle || "General Comment",
          comment_text: config.commentText || "",
        });
      } else if (operation === "assign") {
        await patchAction(row.action_id, {
          operation: "assign",
          assigned_user: config.assignedUser || "Valentina Sassow",
          assigned_team: config.assignedTeam || row.team_name || "Radiology Booking",
        });
      } else if (operation === "reassign-team") {
        await patchAction(row.action_id, {
          operation: "reassign-team",
          assigned_team: config.assignedTeam || "Radiology Booking",
        });
      } else if (operation === "complete") {
        await patchAction(row.action_id, { operation: "complete", status: "completed" });
      } else if (operation === "escalate") {
        await patchAction(row.action_id, { operation: "escalate", status: "escalated" });
      } else if (operation === "revoke") {
        await patchAction(row.action_id, { operation: "revoke", status: "revoked" });
      } else if (operation === "reopen") {
        await patchAction(row.action_id, { operation: "reopen", status: "open" });
      }
    }
    clearActionSelection();
    state.actions.modal = null;
    await reloadActiveActionsView();
  }

  function openActionModal(kind, row = null) {
    state.actions.modal = {
      kind,
      rowId: row ? String(row.action_id) : null,
      title: kind === "comment" ? "Add Comment" : kind === "assign" ? "Assign Action" : "Reassign Team",
    };
    window.C360.renderApp();
  }

  function closeActionModal() {
    state.actions.modal = null;
    window.C360.renderApp();
  }

  function getCancerSiteOptions() {
    return [...new Set(state.actions.rows.map((row) => row.cancer_site).filter(Boolean))].sort();
  }

  function getHospitalSiteOptions() {
    return [...new Set(state.actions.rows.map((row) => row.hospital_site).filter(Boolean))].sort();
  }

  function getActionStatusOptions() {
    return [...new Set(state.actions.rows.map((row) => row.action_status).filter(Boolean))].sort();
  }

  function getTeamOptions() {
    return [...new Set(state.actions.rows.map((row) => row.team_name).filter(Boolean))].sort();
  }

  function getActionTypeOptions() {
    return [...new Set(state.actions.rows.map((row) => row.title).filter(Boolean))].sort();
  }

  function getActionDetailOptions() {
    return [...new Set(state.actions.rows.map((row) => row.action_detail_summary).filter(Boolean))].sort();
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
    if (days >= 11) return "days-danger";
    if (days >= 8) return "days-warning";
    return "days-good";
  }

  function kpiValue(value) {
    return value != null ? String(value) : "0";
  }

  function renderSelect(id, value, options, placeholder = "Search...") {
    return `
      <select id="${id}">
        <option value="">${placeholder}</option>
        ${options.map((option) => `<option value="${esc(option)}" ${value === option ? "selected" : ""}>${esc(option)}</option>`).join("")}
      </select>
    `;
  }

  function renderActionsSubheader() {
    return `
      <section class="module-subheader actions-subheader">
        <div class="module-subheader-left">
          <span class="module-mark actions-mark">${actionIcon("clipboard-solid")}</span>
          <div>
            <div class="module-header-title">Cancer Actions</div>
            <button class="saved-state-button" type="button"><span>Saved module states</span><span class="saved-state-chevron"></span></button>
          </div>
          <div class="actions-subtabs">
            <button class="actions-subtab ${state.actions.activeSubView === "list" ? "active" : ""}" data-action="set-actions-subview" data-value="list" type="button">${actionIcon("table")}<span>Actions List</span></button>
            <button class="actions-subtab ${state.actions.activeSubView === "updates" ? "active" : ""}" data-action="set-actions-subview" data-value="updates" type="button">${actionIcon("updates")}<span>Recent Action Updates</span></button>
          </div>
        </div>
        <div class="module-subheader-right">
          <button class="icon-square-button actions-gear" type="button">${window.C360.icon("gear")}</button>
          <div class="subheader-filter">
            <label for="actions-cancer-site">Cancer Site:</label>
            ${renderSelect("actions-cancer-site", state.actions.filters.cancerSite, getCancerSiteOptions())}
          </div>
          <div class="subheader-filter">
            <label for="actions-hospital-site">Hospital Site:</label>
            ${renderSelect("actions-hospital-site", state.actions.filters.hospitalSite, getHospitalSiteOptions())}
          </div>
        </div>
      </section>
    `;
  }

  function renderKpis() {
    const summary = state.actions.summary || {};
    return `
      <section class="actions-kpi-row">
        <div class="actions-kpi card-my">
          <div class="actions-kpi-label">My Actions</div>
          <div class="actions-kpi-info">${actionIcon("info")}</div>
          <div class="actions-kpi-value">${kpiValue(summary.my_actions || 16)}</div>
        </div>
        <div class="actions-kpi card-team">
          <div class="actions-kpi-label">Actions for my team(s)</div>
          <div class="actions-kpi-info">${actionIcon("info")}</div>
          <div class="actions-kpi-value">${kpiValue(summary.team_actions || 268)}</div>
          <div class="actions-kpi-sub">${kpiValue(summary.awaiting_assignment || 54)} Awaiting assignment</div>
        </div>
        <div class="actions-kpi card-escalated">
          <div class="actions-kpi-label">Escalated actions for my team(s)</div>
          <div class="actions-kpi-info">${actionIcon("info")}</div>
          <div class="actions-kpi-value">${kpiValue(summary.escalated_team_actions || 28)}</div>
        </div>
        <div class="actions-kpi card-all">
          <div class="actions-kpi-label">All actions</div>
          <div class="actions-kpi-info">${actionIcon("info")}</div>
          <div class="actions-kpi-value">${kpiValue(summary.all_actions || 5775)}</div>
        </div>
      </section>
    `;
  }

  function renderToolbarButton(action, label, iconName, className, disabled, rowAction = "") {
    const attr = rowAction ? ` data-row-action="${rowAction}"` : "";
    return `<button class="actions-toolbar-btn ${className}" data-action="${action}"${attr} type="button" ${disabled ? "disabled" : ""}>${actionIcon(iconName)}<span>${label}</span></button>`;
  }

  function renderListToolbar() {
    const hasSelection = state.actions.selectedIds.length > 0;
    return `
      <section class="actions-toolbar">
        <div class="actions-toolbar-left">
          <button class="icon-square-button" data-action="open-actions-filter" type="button">${window.C360.icon("filter")}</button>
          <button class="actions-scope-tab ${state.actions.selectionScope === "all" ? "active" : ""}" data-action="set-actions-scope" data-value="all" type="button">all actions <span>${(state.actions.summary?.my_actions || 16)}</span></button>
          <button class="actions-scope-tab ${state.actions.selectionScope === "watchlist" ? "active" : ""}" data-action="set-actions-scope" data-value="watchlist" type="button">watchlist only <span>${(state.actions.summary?.watchlist_only || 1)}</span></button>
        </div>
        <div class="actions-toolbar-right">
          ${renderToolbarButton("bulk-comment", "Add Comment", "comment", "btn-comment", !hasSelection)}
          ${renderToolbarButton("bulk-assign", "Assign", "assign", "btn-assign", !hasSelection)}
          ${renderToolbarButton("bulk-complete", "Complete", "check", "btn-complete", !hasSelection)}
          ${renderToolbarButton("bulk-escalate", "Escalate", "alert", "btn-escalate", !hasSelection)}
          ${renderToolbarButton("bulk-revoke", "Revoke", "revoke", "btn-revoke", !hasSelection)}
          ${renderToolbarButton("bulk-reassign-team", "Reassign team", "reassign", "btn-reassign", !hasSelection)}
        </div>
      </section>
    `;
  }

  function renderActionCell(row, key) {
    if (key === "select") {
      return `<input class="row-checkbox" data-action="toggle-action-selection" data-action-id="${row.action_id}" type="checkbox" ${isSelected(row.action_id) ? "checked" : ""}>`;
    }
    if (key === "due_date") {
      const isPast = row.due_date && new Date(row.due_date) < new Date();
      return `<span class="${isPast ? "date-past" : ""}">${formatNullableDate(row.due_date)}</span>`;
    }
    if (key === "title") {
      return `<div class="action-title-cell"><span class="action-priority-square"></span><span>${esc(row.title || "No value")}</span></div>`;
    }
    if (key === "action_status") {
      return `<span class="action-status-text ${statusClass(row.action_status)}">${esc(row.action_status || "Open")}</span>`;
    }
    if (key === "days_open") {
      return `<span class="days-open-pill ${daysOpenClass(Number(row.days_open || 0))}">${esc(row.days_open ?? "0")}</span>`;
    }
    if (["breach_date_28", "breach_date_31", "breach_date_62", "first_op_appt_attended_date", "next_op_appt_attended_date", "latest_radiology_attended_date", "latest_histology_attended_date", "latest_ip_procedure_tci_date"].includes(key)) {
      return formatNullableDate(row[key]);
    }
    if (key === "pathway_is_open") return esc(String(row.pathway_is_open));
    if (key === "latest_action_comment") return row.latest_action_comment ? esc(row.latest_action_comment) : '<span class="null-value">No value</span>';
    return row[key] !== undefined && row[key] !== null && row[key] !== "" ? esc(row[key]) : '<span class="null-value">No value</span>';
  }

  function renderActionsTable() {
    const columns = [
      { key: "select", label: "", width: 44, sticky: "sticky-left-0" },
      { key: "due_date", label: "Due Date", width: 136, sticky: "sticky-left-44", sortable: true },
      { key: "title", label: "Title", width: 190, sticky: "sticky-left-180" },
      { key: "action_detail_summary", label: "Action Detail Summary", width: 180 },
      { key: "pathway_day", label: "Pathway Day", width: 90 },
      { key: "patient_name", label: "Patient", width: 180 },
      { key: "cancer_site", label: "Cancer Site", width: 140 },
      { key: "mrn", label: "Mrn", width: 130 },
      { key: "nhs_number", label: "Nhs Number", width: 150 },
      { key: "action_status", label: "Action Status", width: 130 },
      { key: "days_open", label: "Days Open", width: 110 },
      { key: "pathway_is_open", label: "Pathway Is Open", width: 120 },
      { key: "pathway_status", label: "Pathway Status", width: 130 },
      { key: "latest_action_comment", label: "Latest Action Comment", width: 320 },
      { key: "owner", label: "Owner", width: 160 },
      { key: "team_name", label: "Team Name", width: 160 },
      { key: "breach_date_28", label: "28 Day Breach Date", width: 180 },
      { key: "breach_date_31", label: "31 Day Breach Date", width: 180 },
      { key: "breach_date_62", label: "62 Day Breach Date", width: 180 },
      { key: "first_op_appt_attended_date", label: "First Op Appt Attended Date", width: 190 },
      { key: "next_op_appt_attended_date", label: "Next Op Appt Attended Date", width: 190 },
      { key: "latest_radiology_attended_date", label: "Latest Radiology Attended Date", width: 190 },
      { key: "latest_histology_attended_date", label: "Latest Histology Attended Date", width: 190 },
      { key: "latest_ip_procedure_tci_date", label: "Latest IP Procedure TCI Date", width: 200 },
    ];

    if (!state.actions.rows.length) {
      return '<div class="empty-state">No cancer actions matched the current filters.</div>';
    }

    return `
      <div class="actions-table-wrap">
        <table class="ptl-table actions-table">
          <thead>
            <tr>
              ${columns.map((column) => `<th class="${column.sticky ? `sticky-col sticky-head ${column.sticky}` : ""}" style="min-width:${column.width}px;width:${column.width}px">${esc(column.label)}${column.sortable ? `<span class="sort-icon">${actionIcon("sort")}</span>` : ""}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${state.actions.rows.map((row) => `
              <tr class="actions-row" data-action="open-single-action" data-action-id="${row.action_id}">
                ${columns.map((column) => `<td class="${column.sticky ? `sticky-col ${column.sticky}` : ""}" style="min-width:${column.width}px;width:${column.width}px">${renderActionCell(row, column.key)}</td>`).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderActionHistory(history) {
    const items = history || [];
    return `
      <div class="single-action-column">
        <div class="single-column-header blue">Action History</div>
        <div class="single-column-body">
          ${items.map((item) => `
            <div class="single-history-item tone-${esc(item.tone || "info")}">
              <div class="single-history-type">${esc(item.event_type)}</div>
              <div class="single-history-time">${esc(formatDateTime(item.timestamp))}</div>
              <div class="single-history-meta">${item.event_type.includes("ASSIGN") ? `Changed By - ${esc(item.actor || "System")}` : item.event_type.includes("COMPLETE") ? `Completed By - ${esc(item.actor || "System")}` : `Created By - ${esc(item.actor || "System")}`}</div>
              ${item.title ? `<div class="single-history-title">${esc(item.title)}</div>` : ""}
              ${item.detail ? `<div class="single-history-detail">${esc(item.detail)}</div>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderActionDetails(detail) {
    const row = detail.action;
    return `
      <div class="single-action-column">
        <div class="single-column-header maroon">Action Details</div>
        <div class="single-column-body detail-kv-list">
          <div class="detail-kv-block gray"><div class="detail-kv-label">Pathway</div><div class="detail-kv-value">${esc(`${row.patient_name} | MRN: ${row.mrn || "No value"} | ${row.cancer_site || "Unknown"} | Day ${row.pathway_day ?? "No value"}`)}</div></div>
          <div class="detail-kv-block green"><div class="detail-kv-label">Status</div><div class="detail-kv-value">${esc(row.action_status)}</div></div>
          <div class="detail-kv-block"><div class="detail-kv-label">Team</div><div class="detail-kv-value">${row.team_name ? esc(row.team_name) : '<span class="null-value">No value</span>'}</div></div>
          <div class="detail-kv-block"><div class="detail-kv-label">Owner</div><div class="detail-kv-value">${row.owner ? esc(row.owner) : '<span class="null-value">No value</span>'}</div></div>
          <div class="detail-kv-block"><div class="detail-kv-label">Due Date</div><div class="detail-kv-value">${formatNullableDate(row.due_date)}</div></div>
          <div class="detail-kv-block"><div class="detail-kv-label">Last Updated</div><div class="detail-kv-value">${row.last_updated ? esc(formatDateTime(row.last_updated)) : '<span class="null-value">No value</span>'}</div></div>
          <div class="detail-kv-block"><div class="detail-kv-label">Last Updated By</div><div class="detail-kv-value">${row.last_updated_by ? esc(row.last_updated_by) : '<span class="null-value">No value</span>'}</div></div>
          <div class="detail-kv-block provenance-block"><div class="detail-kv-label">Data Provenance</div><div class="detail-kv-value">${Object.entries(detail.data_provenance || {}).map(([key, value]) => `<div><strong>${esc(key)}:</strong> ${esc(value)}</div>`).join("")}</div></div>
        </div>
      </div>
    `;
  }

  function renderSingleActionSummary(detail) {
    const row = detail.action;
    return `
      <section class="single-action-summary">
        <div class="single-summary-cell">
          <div class="single-summary-label">Title</div>
          <div class="single-summary-value">${esc(row.title)}</div>
        </div>
        <div class="single-summary-cell">
          <div class="single-summary-label">Action Detail</div>
          <div class="single-summary-value">${row.action_detail_summary ? esc(row.action_detail_summary) : '<span class="null-value">No value</span>'}</div>
        </div>
        <div class="single-summary-cell summary-days">
          <div class="single-summary-label">Days Open</div>
          <div class="single-summary-value">${esc(row.days_open)}</div>
        </div>
        <div class="single-summary-cell summary-due">
          <div class="single-summary-label">Due Date</div>
          <div class="single-summary-value">${formatNullableDate(row.due_date)}</div>
        </div>
      </section>
    `;
  }

  function renderSingleActionToolbar(row, includeReopen = false) {
    return `
      <section class="single-action-toolbar">
        ${renderToolbarButton("row-comment", "Add Comment", "comment", "btn-assign", false, row.action_id)}
        ${renderToolbarButton("row-assign", "Assign", "assign", "btn-assign", false, row.action_id)}
        ${renderToolbarButton("row-complete", "Complete", "check", "btn-complete", false, row.action_id)}
        ${includeReopen ? renderToolbarButton("row-reopen", "Reopen", "updates", "btn-reassign", false, row.action_id) : ""}
        ${renderToolbarButton("row-escalate", "Escalate", "alert", "btn-escalate", false, row.action_id)}
        ${renderToolbarButton("row-revoke", "Revoke", "revoke", "btn-revoke", false, row.action_id)}
        ${renderToolbarButton("row-reassign-team", "Reassign team", "reassign", "btn-reassign", false, row.action_id)}
      </section>
    `;
  }

  function renderExpandedUpdateCard(item) {
    const row = item.action_detail.action;
    return `
      <div class="expanded-update">
        <div class="expanded-update-strip">${actionIcon("clipboard-solid")}<span>${esc(`${row.patient_name} | MRN: ${row.mrn || "No value"} | ${row.cancer_site || "Unknown"} | Day ${row.pathway_day ?? "No value"}`)}</span></div>
        <div class="expanded-update-comment">
          ${actionIcon("comment")}
          <div>
            <div class="expanded-update-comment-title">${esc(item.comment_title || "General Comment")}</div>
            <div class="expanded-update-comment-label">Comment Text</div>
            <div>${item.comment_text ? esc(item.comment_text) : '<span class="null-value">No value</span>'}</div>
          </div>
        </div>
        <div class="expanded-divider"></div>
        <div class="expanded-action-shell">
          <div class="expanded-action-header">${actionIcon("assign")}<span>${esc(`${row.title} - ${row.patient_name} | MRN: ${row.mrn || "No value"} | ${row.cancer_site || "Unknown"} | Day ${row.pathway_day ?? "No value"}`)}</span></div>
          ${renderSingleActionToolbar(row, true)}
          ${renderSingleActionSummary(item.action_detail)}
          <div class="single-action-detail-grid">
            ${renderActionHistory(item.action_detail.history)}
            ${renderActionDetails(item.action_detail)}
          </div>
        </div>
      </div>
    `;
  }

  function renderUpdatesView() {
    const items = state.actions.updatesItems || [];
    return `
      <section class="updates-filter-bar">
        <div class="updates-filter-control">
          <label>FROM</label>
          <div class="updates-datetime-row"><input id="actions-update-from" type="datetime-local" value="${esc(state.actions.filters.updateFrom)}"><select><option>GMT+1</option></select></div>
        </div>
        <div class="updates-filter-control">
          <label>TO</label>
          <div class="updates-datetime-row"><input id="actions-update-to" type="datetime-local" value="${esc(state.actions.filters.updateTo)}"><select><option>GMT+1</option></select></div>
        </div>
        <div class="updates-filter-control wide">
          <label>UPDATE TYPE</label>
          <input id="actions-update-types" placeholder="Filter to 1 or more update types..." value="${esc(state.actions.filters.updateTypes)}">
        </div>
        <div class="updates-filter-control wide">
          <label>EXCLUDE UPDATES MADE BY</label>
          <input id="actions-exclude-users" placeholder="Select one or more users..." value="${esc(state.actions.filters.excludeUsers)}">
        </div>
      </section>
      ${state.actions.updatesLoading ? '<div class="loading-state">Loading recent action updates...</div>' : ""}
      ${state.actions.updatesError ? `<div class="error-state">${esc(state.actions.updatesError)}</div>` : ""}
      <section class="updates-list-shell">
        ${items.map((item) => `
          <article class="update-card tone-${esc(item.update_tone)}">
            <div class="update-card-header">
              <div class="update-card-left">
                <span class="update-card-icon">${actionIcon(item.update_type === "Created" ? "plus" : item.update_type === "Assigned Owner" ? "assign" : "comment")}</span>
                <div>
                  <button class="update-card-title" data-action="toggle-update-card" data-update-id="${esc(item.update_id)}" type="button">${esc(item.update_type)} - ${esc(item.action_detail.action.title)} - ${esc(item.action_detail.action.patient_name)} | MRN: ${esc(item.action_detail.action.mrn || "No value")} | ${esc(item.action_detail.action.cancer_site || "Unknown")} | Day ${esc(item.action_detail.action.pathway_day ?? "No value")}</button>
                  <div class="update-card-time">${esc(formatDateTime(item.timestamp))}</div>
                </div>
              </div>
              <button class="update-card-chevron" data-action="toggle-update-card" data-update-id="${esc(item.update_id)}" type="button">${state.actions.expandedUpdates[item.update_id] ? window.C360.icon("chevron-down") : actionIcon("chevron-right")}</button>
            </div>
            ${state.actions.expandedUpdates[item.update_id] ? renderExpandedUpdateCard(item) : ""}
          </article>
        `).join("")}
        <div class="updates-pagination">
          <div>Showing ${items.length ? ((state.actions.updatesPage - 1) * state.actions.updatesPerPage) + 1 : 0} - ${Math.min(state.actions.updatesPage * state.actions.updatesPerPage, state.actions.updatesTotal)} of ${state.actions.updatesTotal.toLocaleString("en-GB")} items</div>
          <div class="pagination-controls">
            <button data-action="updates-page" data-value="prev" type="button">&lt;</button>
            <button class="page-pill" type="button">${state.actions.updatesPage}</button>
            <button data-action="updates-page" data-value="next" type="button">&gt;</button>
          </div>
        </div>
      </section>
    `;
  }

  function renderActionListView() {
    return `
      ${renderKpis()}
      ${renderListToolbar()}
      ${state.actions.loading ? '<div class="loading-state">Loading cancer actions...</div>' : ""}
      ${state.actions.error ? `<div class="error-state">${esc(state.actions.error)}</div>` : ""}
      ${!state.actions.loading && !state.actions.error ? renderActionsTable() : ""}
    `;
  }

  function renderActionsPage() {
    return `
      <section class="view-shell route-module actions-route">
        ${renderActionsSubheader()}
        <section class="module-body actions-body">
          ${state.actions.activeSubView === "list" ? renderActionListView() : renderUpdatesView()}
        </section>
      </section>
    `;
  }

  function renderActionsFilterDrawer() {
    if (state.route !== "actions" || !state.actions.sidebarOpen) return "";
    return `
      <div class="filters-overlay" data-action="close-actions-filter"></div>
      <aside class="ptl-filter-drawer actions-filter-drawer">
        <div class="filter-drawer-header">
          <div class="filter-inline actions-filter-header-inline">
            <div class="filter-drawer-title">Filters</div>
            <button class="reset-button" data-action="reset-actions-filters" type="button">${window.C360.icon("refresh")}<span>Reset Filters</span></button>
            <button class="actions-apply-button" data-action="apply-actions-filters" type="button">${window.C360.icon("filter")}<span>Apply Filters</span></button>
          </div>
        </div>
        <div class="filter-drawer-body">
          <div class="filter-group"><div class="filter-label">Action Description</div>${renderSelect("actions-filter-description", state.actions.filters.actionDescription, getActionTypeOptions())}</div>
          <div class="filter-group"><div class="filter-label">Action Detail</div>${renderSelect("actions-filter-detail", state.actions.filters.actionDetail, getActionDetailOptions())}</div>
          <div class="filter-group"><div class="filter-label">Action Is Open</div><select id="actions-filter-open"><option value="">Search...</option><option value="true" ${state.actions.filters.actionIsOpen === "true" ? "selected" : ""}>True x</option><option value="false" ${state.actions.filters.actionIsOpen === "false" ? "selected" : ""}>False</option></select></div>
          <div class="filter-group"><div class="filter-label">Action Status</div>${renderSelect("actions-filter-status", state.actions.filters.actionStatus, getActionStatusOptions())}</div>
          <div class="filter-group"><div class="filter-label">Team Name</div>${renderSelect("actions-filter-team", state.actions.filters.teamName, getTeamOptions())}</div>
          <div class="filter-group"><div class="filter-label">Owner</div><input id="actions-filter-owner" class="filter-input" placeholder="Search..." value="${esc(state.actions.filters.owner)}"></div>
          <div class="filter-group">
            <div class="filter-label">Due Date</div>
            <div class="filter-inline"><select><option>Date range</option></select><label class="relative-toggle"><input type="checkbox"> <span>Relative to today</span></label></div>
            <div class="mini-filter-label">After (inclusive)</div>
            <input id="actions-filter-due-after" class="filter-input" type="date" value="${esc(state.actions.filters.dueAfter)}">
            <div class="mini-filter-label">Before (inclusive)</div>
            <input id="actions-filter-due-before" class="filter-input" type="date" value="${esc(state.actions.filters.dueBefore)}">
          </div>
          <div class="filter-group">
            <div class="filter-label">Action Created Date</div>
            <div class="filter-inline"><select><option>Time range</option></select><label class="relative-toggle"><input type="checkbox"> <span>Relative to today</span></label></div>
            <div class="mini-filter-label">After (inclusive)</div>
            <div class="filter-inline"><input id="actions-filter-created-after" class="filter-input" type="datetime-local" value="${esc(state.actions.filters.createdAfter)}"><select><option>GMT+1</option></select></div>
            <div class="mini-filter-label">Before (inclusive)</div>
            <div class="filter-inline"><input id="actions-filter-created-before" class="filter-input" type="datetime-local" value="${esc(state.actions.filters.createdBefore)}"><select><option>GMT+1</option></select></div>
          </div>
          ${[
            ["PATIENT", "[CDM] Patient", 15, "people"],
            ["CANCER PATHWAY", "[Cancer 360] Cancer Pathway", 15, "list"],
            ["ACTION COMMENTS", "[Cancer 360] Cancer PTL Action Comment", 33, "comment"],
            ["ALL ACTION HISTORY", "[Cancer 360] Cancer PTL Action Changelog", 38, "updates"],
            ["LINKED TRACKING AND DIAGNOSTICS TO PATHWAY", "[Cancer 360] Cancer PTL Helper", 15, "link"],
          ].map(([title, label, count, iconName]) => `
            <div class="entity-accordion">
              <button class="entity-button" type="button">
                <span class="tab-icon">${actionIcon(iconName)}</span>
                <span><span class="entity-title">${esc(title)}</span><span class="entity-detail">${esc(label)} <span class="entity-count">${count}</span></span></span>
                <span class="tab-icon">${window.C360.icon("chevron-down")}</span>
              </button>
            </div>
          `).join("")}
          <button class="add-filter-button" type="button">Add filter</button>
        </div>
      </aside>
    `;
  }

  function renderActionModal() {
    const modal = state.actions.modal;
    if (!modal) return "";
    const isComment = modal.kind === "comment";
    const isAssign = modal.kind === "assign";
    const isReassignTeam = modal.kind === "reassign-team";
    return `
      <div class="action-modal-overlay" data-action="close-action-modal"></div>
      <div class="action-modal">
        <div class="action-modal-header">
          <div class="action-modal-title">${esc(modal.title)}</div>
          <button class="drawer-close" data-action="close-action-modal" type="button">${window.C360.icon("x")}</button>
        </div>
        <form id="action-modal-form" class="action-modal-body">
          <input type="hidden" name="kind" value="${esc(modal.kind)}">
          ${modal.rowId ? `<input type="hidden" name="rowId" value="${esc(modal.rowId)}">` : ""}
          ${isComment ? `<label class="action-modal-field">Comment Title<input name="commentTitle" value="General Comment"></label><label class="action-modal-field">Comment Text<textarea name="commentText" rows="5" required></textarea></label>` : ""}
          ${isAssign ? `<label class="action-modal-field">Assigned User<input name="assignedUser" value="Valentina Sassow"></label><label class="action-modal-field">Assigned Team<input name="assignedTeam" value="Radiology Booking"></label>` : ""}
          ${isReassignTeam ? `<label class="action-modal-field">Assigned Team<input name="assignedTeam" value="Radiology Booking"></label>` : ""}
          <div class="action-modal-actions">
            <button class="nav-edit-button modal-cancel" data-action="close-action-modal" type="button">Cancel</button>
            <button class="actions-apply-button" type="submit">Save</button>
          </div>
        </form>
      </div>
    `;
  }

  function renderSingleActionView() {
    if (!state.actions.activeDetail && !state.actions.detailLoading && !state.actions.detailError) return "";
    const detail = state.actions.activeDetail;
    return `
      <div class="drawer-overlay action-overlay-backdrop" data-action="close-single-action"></div>
      <aside class="single-action-overlay">
        ${state.actions.detailLoading ? '<div class="loading-state">Loading single action view...</div>' : ""}
        ${state.actions.detailError ? `<div class="error-state">${esc(state.actions.detailError)}</div>` : ""}
        ${detail ? `
          <div class="single-action-header">
            <div class="single-action-header-title">${esc(`${detail.action.title} - ${detail.action.patient_name} | MRN: ${detail.action.mrn || "No value"} | ${detail.action.cancer_site || "Unknown"} | Day ${detail.action.pathway_day ?? "No value"}`)}</div>
            <button class="drawer-link-button" type="button">${window.C360.icon("link")}External Links${window.C360.icon("chevron-down")}</button>
            <button class="drawer-close" data-action="close-single-action" type="button">${window.C360.icon("x")}</button>
          </div>
          <div class="single-action-scroll">
            ${renderSingleActionToolbar(detail.action)}
            ${renderSingleActionSummary(detail)}
            <div class="single-action-detail-grid">
              ${renderActionHistory(detail.history)}
              ${renderActionDetails(detail)}
            </div>
            ${state.actions.activePathway ? `<div class="embedded-pathway-wrapper">${renderEmbeddedDrawer(state.actions.activePathway, state.actions.embeddedDrawer)}</div>` : '<div class="empty-state">Loading pathway detail...</div>'}
          </div>
        ` : ""}
      </aside>
      ${renderActionModal()}
    `;
  }

  function renderOverlay() {
    return `${renderSingleActionView()}${!state.actions.activeDetail ? renderActionModal() : ""}`;
  }

  async function handleSubmit(event) {
    if (event.target.id !== "action-modal-form") return false;
    event.preventDefault();
    const form = new FormData(event.target);
    const kind = form.get("kind");
    const rowId = form.get("rowId");
    const row = rowId ? state.actions.rows.find((item) => String(item.action_id) === String(rowId)) || state.actions.activeDetail?.action : null;
    if (kind === "comment") {
      await runBulkOperation("comment", { row, commentTitle: String(form.get("commentTitle") || "General Comment"), commentText: String(form.get("commentText") || "") });
      return true;
    }
    if (kind === "assign") {
      await runBulkOperation("assign", { row, assignedUser: String(form.get("assignedUser") || "Valentina Sassow"), assignedTeam: String(form.get("assignedTeam") || "Radiology Booking") });
      return true;
    }
    if (kind === "reassign-team") {
      await runBulkOperation("reassign-team", { row, assignedTeam: String(form.get("assignedTeam") || "Radiology Booking") });
      return true;
    }
    return false;
  }

  async function handleClick(event, dataset) {
    const action = dataset.action;
    if (!action) return false;
    if (event.target.closest(".embedded-pathway-shell")) {
      if (action === "embedded-drawer-section") { state.actions.embeddedDrawer.activeSection = dataset.value; state.actions.embeddedDrawer.selectedActionId = null; state.actions.embeddedDrawer.selectedReportKey = null; window.C360.renderApp(); return true; }
      if (action === "select-drawer-action") { state.actions.embeddedDrawer.selectedActionId = dataset.actionId; window.C360.renderApp(); return true; }
      if (action === "clear-selected-action") { state.actions.embeddedDrawer.selectedActionId = "__none__"; window.C360.renderApp(); return true; }
      if (action === "select-report") { state.actions.embeddedDrawer.selectedReportKey = dataset.key; window.C360.renderApp(); return true; }
      if (action === "clear-selected-report") { state.actions.embeddedDrawer.selectedReportKey = "__none__"; window.C360.renderApp(); return true; }
      if (action === "set-patient-tab") { state.actions.embeddedDrawer.patientTab = dataset.value; window.C360.renderApp(); return true; }
    }

    switch (action) {
      case "open-actions-filter": state.actions.sidebarOpen = true; window.C360.renderApp(); return true;
      case "close-actions-filter": state.actions.sidebarOpen = false; window.C360.renderApp(); return true;
      case "apply-actions-filters": state.actions.sidebarOpen = false; await loadActionsWorklist(); return true;
      case "reset-actions-filters":
        state.actions.filters = { ...state.actions.filters, actionDescription: "", actionDetail: "", actionIsOpen: "true", actionStatus: "", teamName: "", owner: "", dueAfter: "", dueBefore: "", createdAfter: "", createdBefore: "", updateFrom: "", updateTo: "", updateTypes: "", excludeUsers: "", cancerSite: "", hospitalSite: "" };
        state.actions.sidebarOpen = false;
        await reloadActiveActionsView();
        return true;
      case "set-actions-subview": state.actions.activeSubView = dataset.value; if (dataset.value === "updates") await loadActionUpdates(); else window.C360.renderApp(); return true;
      case "set-actions-scope": state.actions.selectionScope = dataset.value; await loadActionsWorklist(); return true;
      case "toggle-action-selection": toggleSelection(dataset.actionId); window.C360.renderApp(); return true;
      case "open-single-action": if (event.target.closest(".row-checkbox")) return true; await loadSingleActionView(dataset.actionId); return true;
      case "close-single-action": state.actions.activeDetail = null; state.actions.activePathway = null; state.actions.detailError = ""; state.actions.detailLoading = false; window.C360.renderApp(); return true;
      case "toggle-update-card": state.actions.expandedUpdates[dataset.updateId] = !state.actions.expandedUpdates[dataset.updateId]; window.C360.renderApp(); return true;
      case "updates-page":
        if (dataset.value === "prev" && state.actions.updatesPage > 1) state.actions.updatesPage -= 1;
        if (dataset.value === "next" && (state.actions.updatesPage * state.actions.updatesPerPage) < state.actions.updatesTotal) state.actions.updatesPage += 1;
        await loadActionUpdates();
        return true;
      case "bulk-comment": openActionModal("comment"); return true;
      case "bulk-assign": openActionModal("assign"); return true;
      case "bulk-reassign-team": openActionModal("reassign-team"); return true;
      case "bulk-complete": await runBulkOperation("complete"); return true;
      case "bulk-escalate": await runBulkOperation("escalate"); return true;
      case "bulk-revoke": await runBulkOperation("revoke"); return true;
      case "row-comment": openActionModal("comment", state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action); return true;
      case "row-assign": openActionModal("assign", state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action); return true;
      case "row-reassign-team": openActionModal("reassign-team", state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action); return true;
      case "row-complete": await runBulkOperation("complete", { row: state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action }); return true;
      case "row-escalate": await runBulkOperation("escalate", { row: state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action }); return true;
      case "row-revoke": await runBulkOperation("revoke", { row: state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action }); return true;
      case "row-reopen": await runBulkOperation("reopen", { row: state.actions.rows.find((row) => String(row.action_id) === String(dataset.rowAction)) || state.actions.activeDetail?.action }); return true;
      case "close-action-modal": closeActionModal(); return true;
      default: return false;
    }
  }

  async function handleChange(event) {
    const { id, value } = event.target;
    switch (id) {
      case "actions-cancer-site": state.actions.filters.cancerSite = value; await loadActionsWorklist(); return true;
      case "actions-hospital-site": state.actions.filters.hospitalSite = value; await loadActionsWorklist(); return true;
      case "actions-filter-description": state.actions.filters.actionDescription = value; return true;
      case "actions-filter-detail": state.actions.filters.actionDetail = value; return true;
      case "actions-filter-open": state.actions.filters.actionIsOpen = value; return true;
      case "actions-filter-status": state.actions.filters.actionStatus = value; return true;
      case "actions-filter-team": state.actions.filters.teamName = value; return true;
      case "actions-filter-owner": state.actions.filters.owner = value; return true;
      case "actions-filter-due-after": state.actions.filters.dueAfter = value; return true;
      case "actions-filter-due-before": state.actions.filters.dueBefore = value; return true;
      case "actions-filter-created-after": state.actions.filters.createdAfter = value; return true;
      case "actions-filter-created-before": state.actions.filters.createdBefore = value; return true;
      case "actions-update-from": state.actions.filters.updateFrom = value; await loadActionUpdates(); return true;
      case "actions-update-to": state.actions.filters.updateTo = value; await loadActionUpdates(); return true;
      case "actions-update-types": state.actions.filters.updateTypes = value; await loadActionUpdates(); return true;
      case "actions-exclude-users": state.actions.filters.excludeUsers = value; await loadActionUpdates(); return true;
      default: return false;
    }
  }

  async function initActionsRoute() {
    await loadActionsWorklist();
    if (state.actions.activeSubView === "updates") await loadActionUpdates();
  }

  window.C360.actionsUI = {
    renderActionsPage,
    renderActionsFilterDrawer,
    renderActionOverlay: renderOverlay,
    loadActionsWorklist,
    loadActionUpdates,
    loadSingleActionView,
    initActionsRoute,
    handleClick,
    handleChange,
    handleSubmit,
  };
})();
