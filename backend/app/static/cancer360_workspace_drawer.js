(() => {
  const { state, esc, formatDate, formatDateTime, icon } = window.C360;
  let currentDrawerState = null;

  function getDrawerState() {
    return currentDrawerState || state.drawer;
  }

  const SECTION_LABELS = {
    "pathway-details": "Pathway Details",
    actions: "Actions",
    outpatient: "Outpatient Appointments",
    inpatient: "Inpatient Procedures",
    histology: "Histology",
    radiology: "Radiology",
    mdt: "MDT Notes",
    tests: "Test Results",
    ipt: "IPT",
    tracking: "Tracking Comments",
    patient: "Patient",
  };

  function formatNullableDate(value) {
    return value ? esc(formatDate(value)) : '<span class="null-value">No value</span>';
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (match) => match.toUpperCase());
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

  function getSectionCounts() {
    const counts = {};
    (getDrawerState().data?.section_counts || []).forEach((item) => {
      counts[item.key] = item.count;
    });
    return counts;
  }

  function normaliseStatus(value) {
    return String(value || "").trim().toLowerCase();
  }

  function renderToneText(value, toneClass) {
    const cssClass = toneClass ? ` ${toneClass}` : "";
    return `<span class="drawer-tone-text${cssClass}">${esc(value || "No value")}</span>`;
  }

  function renderPathwayStatus(value) {
    return value === "Benign"
      ? '<span class="status-pill status-benign">Benign</span>'
      : '<span class="status-pill status-suspected">Suspected</span>';
  }

  function renderActionStatus(status) {
    const normalized = normaliseStatus(status);
    if (normalized === "completed") return renderToneText("Completed", "tone-muted");
    if (normalized === "revoked" || normalized === "cancelled") return renderToneText(titleCase(status), "tone-muted");
    if (normalized.includes("assign")) return renderToneText(titleCase(status), "tone-warning");
    if (normalized === "escalated") return renderToneText("Escalated", "tone-danger");
    return renderToneText(titleCase(status || "Open"), "tone-success");
  }

  function renderExamStatus(status) {
    const normalized = normaliseStatus(status);
    if (normalized === "reported" || normalized === "final" || normalized === "verified") {
      return renderToneText("reported", "tone-success");
    }
    if (normalized.includes("cancel") || normalized.includes("dna") || normalized.includes("did not attend")) {
      return renderToneText(status, "tone-danger");
    }
    return renderToneText(status || "No value", normalized ? "tone-muted" : "");
  }

  function renderNullableText(value) {
    return value !== null && value !== undefined && value !== ""
      ? esc(value)
      : '<span class="null-value">No value</span>';
  }

  function renderDateCell(value) {
    return value
      ? `<span class="${dateTone(value)}">${esc(formatDate(value))}</span>`
      : '<span class="null-value">No value</span>';
  }

  function renderCountBadge(count, hideZero = false) {
    if (!count && hideZero) return "";
    return `<span class="drawer-nav-badge ${count > 0 ? "has-data" : ""}">${count > 0 ? count : "0"}</span>`;
  }

  function buildTimelineModel(events, type) {
    const source = events || [];
    const end = source.length ? new Date(Math.max(...source.map((event) => new Date(event.event_date).getTime()))) : new Date();
    const months = [];
    const cursor = new Date(end.getFullYear(), end.getMonth() - 13, 1);
    for (let index = 0; index < 14; index += 1) {
      months.push({
        key: `${cursor.getFullYear()}-${cursor.getMonth()}`,
        label: cursor.toLocaleString("en-GB", { month: "short" }).slice(0, 1),
      });
      cursor.setMonth(cursor.getMonth() + 1);
    }

    const grouped = new Map();
    source.forEach((event) => {
      const date = new Date(event.event_date);
      if (Number.isNaN(date.getTime())) return;
      const label = event.label || event.event_type || "Event";
      const key = `${date.getFullYear()}-${date.getMonth()}`;
      const monthIndex = months.findIndex((month) => month.key === key);
      if (!grouped.has(label)) grouped.set(label, []);
      if (monthIndex >= 0) {
        const normalized = String(event.event_type || "").toLowerCase();
        let dotType = "milestone";
        if (type === "activity") {
          if (normalized.includes("episode") || normalized.includes("inpatient") || normalized.includes("procedure")) dotType = "inpatient";
          else if (normalized.includes("follow")) dotType = "outpatient-follow";
          else dotType = "outpatient-new";
        }
        grouped.get(label).push({ monthIndex, dotType });
      }
    });

    return { months, rows: [...grouped.entries()].map(([label, dots]) => ({ label, dots })) };
  }

  function renderDotTimeline(events, type) {
    const model = buildTimelineModel(events, type);
    if (!model.rows.length) return '<div class="empty-panel">No timeline data available for this section.</div>';
    const gridClass = type === "activity" ? "activity-grid" : "milestone-grid";
    return `
      <div class="${gridClass}">
        <div class="timeline-corner"></div>
        ${model.months.map((month) => `<div class="timeline-month">${esc(month.label)}</div>`).join("")}
        ${model.rows.map((row) => `
          <div class="timeline-label">${esc(row.label)}</div>
          ${model.months.map((month, index) => {
            const dot = row.dots.find((item) => item.monthIndex === index);
            return `<div class="timeline-dot-cell">${dot ? `<span class="timeline-dot ${dot.dotType}"></span>` : ""}</div>`;
          }).join("")}
        `).join("")}
      </div>
    `;
  }

  function renderSectionFrame(title, body, actionHtml = "") {
    return `
      <div class="section-card-shell">
        <div class="section-shell-header">
          <div class="section-shell-title">${esc(title)}</div>
          <div class="section-shell-actions">${actionHtml}</div>
        </div>
        <div class="section-shell-body">${body}</div>
      </div>
    `;
  }

  function renderKeyValueRows(rows) {
    return `
      <div class="drawer-kv-grid">
        ${rows.map(([label, value]) => `
          <div class="drawer-kv-label">${esc(label)}</div>
          <div class="drawer-kv-value">${value}</div>
        `).join("")}
      </div>
    `;
  }

  function renderPathwayDetails(data) {
    const details = data.details;
    return `
      <div class="drawer-details-layout">
        <div class="drawer-detail-panel">
          <div class="drawer-detail-columns">
            <div class="drawer-detail-column">
              ${renderKeyValueRows([
                ["Pathway Status", renderPathwayStatus(details.pathway_status)],
                ["Days Since Adjusted Pathway Start", esc(details.days_since_adjusted_pathway_start ?? "No value")],
                ["Pathway Type", esc(details.pathway_type || "No value")],
                ["Cancer Site", esc(details.cancer_site || "No value")],
                ["Cancer Sub Site", esc(details.cancer_sub_site || "No value")],
                ["Hospital Site", esc(details.hospital_site || "No value")],
              ])}
            </div>
            <div class="drawer-detail-column">
              ${renderKeyValueRows([
                ["Adjusted Pathway Start Date", formatNullableDate(details.adjusted_pathway_start_date)],
                ["Pathway Closed Date", formatNullableDate(details.pathway_closed_date)],
                ["28 Day Breach Date", renderDateCell(details.breach_date_28)],
                ["31 Day Breach Date", renderDateCell(details.breach_date_31)],
                ["62 Day Breach Date", renderDateCell(details.breach_date_62)],
                ["Original Pathway Start Date", formatNullableDate(details.original_pathway_start_date)],
              ])}
            </div>
          </div>
        </div>
        <div class="drawer-detail-panel">
          <div class="drawer-detail-columns">
            <div class="drawer-detail-column">
              ${renderKeyValueRows([
                ["Full Name", esc(details.full_name)],
                ["NHS Number", esc(details.nhs_number)],
                ["MRN", renderNullableText(details.mrn)],
              ])}
            </div>
            <div class="drawer-detail-column">
              ${renderKeyValueRows([
                ["Phone Number", renderNullableText(details.phone_number)],
                ["Date Of Birth", esc(formatDate(details.date_of_birth))],
                ["Hospital Site", renderNullableText(details.hospital_site)],
              ])}
            </div>
          </div>
        </div>
        <div class="drawer-collapsible-strip">
          <div class="drawer-collapsible-title">Tags</div>
          <div class="drawer-collapsible-content">
            ${details.tags?.length
              ? details.tags.map((tag) => `<span class="tag-chip">${esc(tag)}</span>`).join("")
              : '<span class="null-value">No value</span>'}
            <span class="watchlist-inline">Watchlist reason: ${details.watchlist_reason ? esc(details.watchlist_reason) : "No value"}</span>
          </div>
          <button class="mini-icon-button" type="button" aria-label="Expand tags">${icon("grid")}</button>
        </div>
        <div class="timeline-card pathway-milestones-card">
          <div class="timeline-title">Pathway Milestones</div>
          ${renderDotTimeline(data.milestones || [], "milestone")}
        </div>
      </div>
    `;
  }

  function renderActions(actions) {
    const drawerState = getDrawerState();
    const selected = drawerState.selectedActionId === "__none__"
      ? null
      : (actions.find((item) => item.action_id === drawerState.selectedActionId) || actions[0] || null);

    const table = `
      <div class="section-table-shell drawer-table-shell">
        <table class="drawer-table">
          <thead>
            <tr>
              <th style="width:40px"></th>
              <th>Title</th>
              <th>Due Date</th>
              <th>Action Status</th>
              <th>Action Detail</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            ${actions.length ? actions.map((action) => `
              <tr
                class="${selected && selected.action_id === action.action_id ? "is-selected" : ""}"
                data-action="select-drawer-action"
                data-action-id="${action.action_id}"
              >
                <td><span class="action-priority-dot ${normaliseStatus(action.priority) === "high" ? "high" : ""}"></span></td>
                <td>${esc(action.title)}</td>
                <td>${renderDateCell(action.due_date)}</td>
                <td>${renderActionStatus(action.status)}</td>
                <td>${renderNullableText(action.detail)}</td>
                <td>${renderNullableText(action.owner)}</td>
              </tr>
            `).join("") : '<tr><td colspan="6" class="null-value">No actions recorded for this pathway.</td></tr>'}
          </tbody>
        </table>
      </div>
    `;

    const historyPanel = selected ? `
      <div class="drawer-side-card">
        <div class="drawer-side-card-header">
          <div class="drawer-side-card-title">${esc(selected.title)} | Due: ${selected.due_date ? esc(formatDate(selected.due_date)) : "No value"}</div>
          <div class="drawer-side-card-actions">
            <button class="drawer-action-button compact" type="button">${icon("pencil")}Update${icon("chevron-down")}</button>
            <button class="mini-icon-button" data-action="clear-selected-action" type="button">${icon("x")}</button>
          </div>
        </div>
        <div class="drawer-side-card-body">
          ${(selected.history || []).map((item) => `
            <div class="history-item ${item.tone ? `tone-${esc(item.tone)}` : ""}">
              <div class="history-type">${esc(item.event_type)}</div>
              <div class="history-timestamp">${esc(formatDateTime(item.timestamp))}</div>
              <div class="history-meta-line">${item.actor ? esc(`Created By - ${item.actor}`) : "System generated event"}</div>
              ${item.title ? `<div class="history-meta-line">Comment Title - ${esc(item.title)}</div>` : ""}
              ${item.detail ? `<div class="history-detail">Comment Text - ${esc(item.detail)}</div>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    ` : '<div class="empty-panel">Select an action to inspect the full action history timeline.</div>';

    return `
      <div class="split-panel section-split-panel">
        ${table}
        ${historyPanel}
      </div>
    `;
  }

  function reportStatusLabel(row) {
    const normalized = normaliseStatus(row.status);
    if (normalized === "reported" || normalized === "final" || normalized === "verified") return "reported";
    if (normalized.includes("did not attend")) return "did not attend";
    return row.status || "No value";
  }

  function renderReports(title, rows) {
    const drawerState = getDrawerState();
    const selected = drawerState.selectedReportKey === "__none__"
      ? null
      : (rows.find((item) => `${title}-${item.record_id}` === drawerState.selectedReportKey) || rows[0] || null);

    const table = `
      <div class="section-table-shell drawer-table-shell">
        <table class="drawer-table">
          <thead>
            <tr>
              <th>${title === "Histology" ? "Histology Type" : "Radiology Exam Type"}</th>
              <th>Exam Status</th>
              <th>Priority</th>
              <th>${title === "Histology" ? "Report Date" : "Ordered Date"}</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map((row) => `
              <tr
                class="${selected && selected.record_id === row.record_id ? "is-selected" : ""}"
                data-action="select-report"
                data-key="${title}-${row.record_id}"
              >
                <td>${esc(row.name)}</td>
                <td>${renderExamStatus(reportStatusLabel(row))}</td>
                <td>${renderNullableText(row.priority)}</td>
                <td>${row.report_date ? esc(formatDate(row.report_date)) : row.ordered_date ? esc(formatDate(row.ordered_date)) : '<span class="null-value">No value</span>'}</td>
              </tr>
            `).join("") : '<tr><td colspan="4" class="null-value">No reports found for this section.</td></tr>'}
          </tbody>
        </table>
      </div>
    `;

    const reportPanel = selected ? `
      <div class="drawer-side-card report-side-card">
        <div class="drawer-side-card-header">
          <div class="drawer-side-card-title">${esc(selected.name)} | Report Authorised: ${selected.report_date ? esc(formatDate(selected.report_date)) : "No value"}</div>
          <button class="mini-icon-button" data-action="clear-selected-report" type="button">${icon("x")}</button>
        </div>
        <div class="drawer-side-card-body">
          <div class="report-card">
            <div><strong>${esc(selected.hospital_name || "Notional Hospital")}</strong></div>
            <div class="report-line">Patient Name: ${esc(getDrawerState().data.pathway.patient_name)}</div>
            <div class="report-line">NHS Number: ${esc(getDrawerState().data.pathway.nhs_number)}</div>
            <div class="report-line">Hospital Number: ${esc(getDrawerState().data.pathway.hospital_number || "No value")}</div>
            <div class="report-line" style="margin-top:12px">Referral Source: <strong>${esc(getDrawerState().data.patient_360?.referral?.referral_source || "General Practitioner")}</strong></div>
            <div class="report-line" style="margin-top:12px">${renderNullableText(selected.reference_number)} ${selected.report_date ? esc(formatDate(selected.report_date)) : ""} ${esc(selected.name)}</div>
            <div class="report-line" style="margin-top:12px"><strong>Clinical Question:</strong> ${selected.clinical_question ? esc(selected.clinical_question) : "Review diagnostic findings and correlate clinically."}</div>
            <div class="report-line" style="margin-top:12px"><strong>Findings:</strong></div>
            <div class="report-text-block">${selected.report_text ? esc(selected.report_text) : "No report text available."}</div>
            <div class="report-line" style="margin-top:12px"><strong>Conclusion:</strong></div>
            <div class="report-text-block">${selected.summary ? esc(selected.summary) : "Conclusion not recorded."}</div>
            <div class="report-line" style="margin-top:12px">${esc(selected.author_name || "Reporting clinician not recorded")}</div>
            <div class="report-line">${esc(title === "Histology" ? "Pathology reporting clinician" : "Radiology reporting clinician")}</div>
            <div class="report-disclaimer">This report is generated for the referring clinician. Should patients have queries regarding the report, these should be discussed with the referring clinical team.</div>
          </div>
        </div>
      </div>
    ` : '<div class="empty-panel">Select a report row to inspect the full report card.</div>';

    return `
      <div class="split-panel section-split-panel">
        ${table}
        ${reportPanel}
      </div>
    `;
  }

  function renderOutpatient(rows) {
    return renderSectionFrame(
      "Outpatient Appointments",
      `
        <table class="drawer-table">
          <thead>
            <tr>
              <th>Appointment Name</th>
              <th>Appointment Status</th>
              <th>Ordered Date</th>
              <th>Scheduled Date</th>
              <th>Attended Date</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map((row) => `
              <tr>
                <td>${esc(row.name)}</td>
                <td>${renderExamStatus(row.status)}</td>
                <td>${renderDateCell(row.ordered_date)}</td>
                <td>${renderDateCell(row.scheduled_date)}</td>
                <td>${renderDateCell(row.attended_date)}</td>
              </tr>
            `).join("") : '<tr><td colspan="5" class="null-value">No outpatient appointments found for this pathway.</td></tr>'}
          </tbody>
        </table>
      `,
      `<button class="mini-icon-button" type="button">${icon("grid")}</button>`
    );
  }

  function renderInpatient(rows) {
    return renderSectionFrame(
      "Inpatient Procedures",
      `
        <table class="drawer-table">
          <thead>
            <tr>
              <th>Procedure Name</th>
              <th>Encounter Status</th>
              <th>Ordered Date</th>
              <th>Scheduled Date</th>
              <th>Attended Date</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map((row) => `
              <tr>
                <td>${esc(row.name)}</td>
                <td>${renderExamStatus(row.status)}</td>
                <td>${renderDateCell(row.ordered_date)}</td>
                <td>${renderDateCell(row.scheduled_date)}</td>
                <td>${renderDateCell(row.attended_date)}</td>
              </tr>
            `).join("") : '<tr><td colspan="5" class="null-value">No inpatient procedures found for this pathway.</td></tr>'}
          </tbody>
        </table>
      `,
      `<button class="mini-icon-button" type="button">${icon("grid")}</button>`
    );
  }

  function renderMdt(meetings) {
    if (!meetings.length) return '<div class="empty-panel">No MDT meetings recorded for this pathway.</div>';
    return meetings.map((meeting) => `
      <div class="meeting-card">
        <div class="meeting-header">
          <div>${esc(formatDateTime(meeting.meeting_date))} | ${esc(meeting.status)}</div>
          <div class="meeting-count-pill">MDT Notes ${meeting.note_count} ${icon("chevron-down")}</div>
        </div>
        ${(meeting.notes || []).map((note) => `
          <div class="meeting-note">
            <div class="meeting-note-row">
              <span class="note-type ${esc(note.note_type)}">${esc(note.note_type)}</span>
            </div>
            <div class="meeting-note-meta">Timestamp: ${esc(formatDateTime(note.created_at))}</div>
            <div class="meeting-note-text">Text: ${esc(note.text)}</div>
          </div>
        `).join("")}
      </div>
    `).join("");
  }

  function renderTests(results) {
    if (!results.length) return '<div class="empty-panel">No test results available.</div>';
    return `
      <div class="tests-shell">
        ${results.map((result) => `
          <div class="test-card">
            <div class="test-card-left">
              <div class="test-badge">ba</div>
              <div>
                <div class="test-title">${esc(result.test_name)}</div>
                <div class="test-grid">
                  <div>Test Date: ${result.test_date ? esc(formatDate(result.test_date)) : "No value"}</div>
                  <div>Value: ${esc(result.value || "No value")}</div>
                  <div>Unit: ${esc(result.unit || "No value")}</div>
                  <div>Test Value Type: ${esc(result.value_type || result.test_name)}</div>
                </div>
              </div>
            </div>
            <button class="mini-icon-button" type="button">${icon("grid")}</button>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderIPT(rows) {
    return renderSectionFrame(
      "IPT",
      `
        <table class="drawer-table">
          <thead>
            <tr>
              <th>Reason for IPT</th>
              <th>Sent or Received</th>
              <th>IPT Date</th>
              <th>IPT on Day</th>
              <th>Sending Org Name</th>
              <th>Receiving Org Name</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map((row) => `
              <tr>
                <td>${esc(row.reason_for_ipt)}</td>
                <td>${esc(row.sent_or_received)}</td>
                <td>${renderDateCell(row.ipt_date)}</td>
                <td>${row.ipt_on_day !== null && row.ipt_on_day !== undefined ? esc(row.ipt_on_day) : '<span class="null-value">No value</span>'}</td>
                <td>${renderNullableText(row.sending_org_name)}</td>
                <td>${renderNullableText(row.receiving_org_name)}</td>
              </tr>
            `).join("") : '<tr><td colspan="6" class="null-value">No IPT events are currently available for this pathway.</td></tr>'}
          </tbody>
        </table>
      `
    );
  }

  function renderTracking(rows) {
    return `
      <div class="tracking-header">
        <button class="drawer-action-button compact" type="button">${icon("pencil")}Prepare an Example Tracking Comment</button>
      </div>
      ${rows.length ? rows.map((row) => `
        <div class="tracking-card">
          <div class="tracking-meta">
            <div><strong>Created At:</strong> ${esc(formatDateTime(row.created_at))}</div>
            <div><strong>Created By:</strong> ${esc(row.created_by || "System")}</div>
            <div><strong>Source:</strong> ${esc(row.source_system || "Cancer 360")}</div>
          </div>
          <div class="tracking-text">${esc(row.comment_text)}</div>
        </div>
      `).join("") : '<div class="empty-panel">No tracking comments available.</div>'}
    `;
  }

  function buildPatientActivityTimeline() {
    const events = [];
    const appointments = getDrawerState().data.outpatient_appointments || [];
    const episodes = getDrawerState().data.inpatient_procedures || [];

    appointments.forEach((appointment) => {
      if (!appointment.scheduled_date && !appointment.attended_date) return;
      events.push({
        event_date: appointment.attended_date || appointment.scheduled_date,
        event_type: normaliseStatus(appointment.status).includes("follow") ? "follow-up outpatient appointment" : "new outpatient appointment",
        label: appointment.specialty_name || appointment.name || "Outpatient appointment",
      });
    });

    episodes.forEach((episode) => {
      if (!episode.scheduled_date && !episode.attended_date) return;
      events.push({
        event_date: episode.attended_date || episode.scheduled_date,
        event_type: "inpatient procedure",
        label: episode.specialty_name || episode.name || "Inpatient encounter",
      });
    });

    if (!events.length) {
      // TODO: replace this fallback once a dedicated patient activity feed exists.
      return getDrawerState().data.patient_360?.timeline || [];
    }
    return events;
  }

  function renderInpatientCards(rows) {
    if (!rows.length) return '<div class="patient-empty">No inpatient encounters found for this patient.</div>';
    return rows.map((row) => `
      <div class="encounter-card">
        <div class="encounter-title">${esc(getDrawerState().data.pathway.patient_name)} | ${esc(row.specialty_name || row.name || "Inpatient encounter")}</div>
        <div class="encounter-line">TCI Date: ${row.scheduled_date ? esc(formatDate(row.scheduled_date)) : "No value"}</div>
        <div class="encounter-line">Priority: <span class="priority-pill">4 (more than 12 weeks)</span></div>
        <div class="encounter-line">Specialty Name: ${renderNullableText(row.specialty_name)}</div>
        <div class="encounter-line">Primary Consultant Name: <span class="highlight-chip">${esc(row.consultant_name || "Not recorded")}</span></div>
        <div class="encounter-line">Intended Primary Procedure Description: ${esc(row.name || "No value")}</div>
        <div class="encounter-line">Intended Primary Procedure Free Text: ${esc((row.name || "No value").toUpperCase())}</div>
      </div>
    `).join("");
  }

  function renderPatientOverview(data) {
    const patient = data.patient;
    const activityTimeline = buildPatientActivityTimeline();
    const appointments = getDrawerState().data.outpatient_appointments || [];
    const inpatient = getDrawerState().data.inpatient_procedures || [];
    return `
      <div class="patient-overview-grid">
        <div class="patient-overview-card">
          <div class="patient-overview-grid-inner">
            <div class="patient-overview-item"><div class="drawer-kv-label">Full Name</div><div>${esc(`${patient.surname}, ${patient.forename}`)}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Deceased</div><div><span class="status-pill status-benign">${patient.deceased_date ? "Yes" : "No"}</span></div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">MRN</div><div>${renderNullableText(getDrawerState().data.pathway.hospital_number || patient.hospital_number)}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">NHS Number</div><div>${esc(patient.nhs_number)}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Sex</div><div>${esc(String(patient.sex || "").toLowerCase() === "f" ? "female" : "male")}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Age</div><div>${patient.age !== null && patient.age !== undefined ? esc(patient.age) : '<span class="null-value">No value</span>'}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Date Of Birth</div><div>${esc(formatDate(patient.date_of_birth))}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Date Of Death</div><div>${patient.deceased_date ? esc(formatDate(patient.deceased_date)) : '<span class="null-value">No value</span>'}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Phone Number</div><div>${renderNullableText(patient.phone)}</div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Address Line 1</div><div><span class="null-value">No value</span></div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Address Line 2</div><div><span class="null-value">No value</span></div></div>
            <div class="patient-overview-item"><div class="drawer-kv-label">Postcode</div><div>${renderNullableText(patient.postcode)}</div></div>
          </div>
        </div>
      </div>
      <div class="timeline-card patient-timeline-card">
        <div class="patient-timeline-header">
          <div class="timeline-title">Activity Timeline</div>
          <div class="subheader-filter compact-filter">
            <label>Specialties</label>
            <select><option>Search...</option></select>
          </div>
        </div>
        ${renderDotTimeline(activityTimeline, "activity")}
        <div class="legend-row">
          <span class="legend-item"><span class="timeline-dot inpatient"></span> Inpatient Encounter</span>
          <span class="legend-item"><span class="timeline-dot outpatient-new"></span> First/New Outpatient Appointment</span>
          <span class="legend-item"><span class="timeline-dot outpatient-follow"></span> Follow-Up Outpatient Appointment</span>
        </div>
      </div>
      <div class="split-panel patient-bottom-grid">
        <div class="section-card-shell">
          <div class="section-shell-header"><div class="section-shell-title">Outpatient Appointments</div></div>
          <div class="section-shell-body patient-list-shell">
            ${appointments.length ? `
              <div class="patient-simple-list">
                ${appointments.map((row) => `
                  <div class="patient-simple-row">
                    <div class="patient-simple-title">${esc(row.name)}</div>
                    <div class="patient-simple-meta">${renderExamStatus(row.status)} | ${row.scheduled_date ? esc(formatDate(row.scheduled_date)) : "No value"}</div>
                  </div>
                `).join("")}
              </div>
            ` : '<div class="patient-empty">No outpatient appointments found for this patient</div>'}
          </div>
        </div>
        <div class="section-card-shell">
          <div class="section-shell-header"><div class="section-shell-title">Inpatient Encounters</div></div>
          <div class="section-shell-body patient-list-shell">${renderInpatientCards(inpatient)}</div>
        </div>
      </div>
    `;
  }

  function renderPatientDiagnosis(data) {
    return `
      <div class="patient-diagnosis-layout">
        <div class="detail-card">
          <div class="detail-card-title">Primary Diagnosis</div>
          <div class="drawer-kv-grid">
            <div class="drawer-kv-label">Diagnosis</div>
            <div>${renderNullableText(data.diagnosis?.icd10_description)}</div>
            <div class="drawer-kv-label">ICD-10</div>
            <div>${renderNullableText(data.diagnosis?.icd10_code)}</div>
            <div class="drawer-kv-label">Diagnosis Date</div>
            <div>${data.diagnosis?.diagnosis_date ? esc(formatDate(data.diagnosis.diagnosis_date)) : '<span class="null-value">No value</span>'}</div>
            <div class="drawer-kv-label">Morphology</div>
            <div>${renderNullableText(data.diagnosis?.morphology_code)}</div>
          </div>
        </div>
        <div class="detail-card">
          <div class="detail-card-title">Staging Snapshot</div>
          <div class="drawer-kv-grid">
            <div class="drawer-kv-label">TNM</div>
            <div>${data.staging ? esc(`${data.staging.tnm_t || "Tx"} ${data.staging.tnm_n || "Nx"} ${data.staging.tnm_m || "Mx"}`) : '<span class="null-value">No value</span>'}</div>
            <div class="drawer-kv-label">Stage Group</div>
            <div>${renderNullableText(data.staging?.stage_group)}</div>
            <div class="drawer-kv-label">Grade</div>
            <div>${renderNullableText(data.staging?.grade)}</div>
            <div class="drawer-kv-label">Performance Status</div>
            <div>${data.staging?.performance_status !== null && data.staging?.performance_status !== undefined ? esc(data.staging.performance_status) : '<span class="null-value">No value</span>'}</div>
          </div>
        </div>
      </div>
    `;
  }

  function renderPatient(data) {
    const drawerState = getDrawerState();
    const tab = drawerState.patientTab;
    return `
      <div class="patient-header-card">
        <div class="patient-header-main">
          <div class="patient-avatar-block">${icon("people")}</div>
          <div>
            <div class="patient-header-name">${esc(`${data.patient.surname}, ${data.patient.forename}`)} <span class="patient-star">*</span></div>
            <div class="patient-header-subtitle">[CDM] Patient</div>
          </div>
        </div>
        <div class="patient-tabs">
          <button class="patient-tab ${tab === "overview" ? "active" : ""}" data-action="set-patient-tab" data-value="overview" type="button">Overview</button>
          <button class="patient-tab ${tab === "diagnosis" ? "active" : ""}" data-action="set-patient-tab" data-value="diagnosis" type="button">Diagnosis History</button>
          <button class="patient-tab ${tab === "tests" ? "active" : ""}" data-action="set-patient-tab" data-value="tests" type="button">Test Results</button>
        </div>
      </div>
      ${tab === "overview" ? renderPatientOverview(data) : ""}
      ${tab === "diagnosis" ? renderPatientDiagnosis(data) : ""}
      ${tab === "tests" ? renderTests(getDrawerState().data.test_results || []) : ""}
    `;
  }

  function renderSection(data) {
    switch (getDrawerState().activeSection) {
      case "pathway-details":
        return renderPathwayDetails(data);
      case "actions":
        return renderActions(data.actions || []);
      case "outpatient":
        return renderOutpatient(data.outpatient_appointments || []);
      case "inpatient":
        return renderInpatient(data.inpatient_procedures || []);
      case "histology":
        return renderReports("Histology", data.histology || []);
      case "radiology":
        return renderReports("Radiology", data.radiology || []);
      case "mdt":
        return renderMdt(data.mdt_notes || []);
      case "tests":
        return renderTests(data.test_results || []);
      case "ipt":
        return renderIPT(data.ipt || []);
      case "tracking":
        return renderTracking(data.tracking_comments || []);
      case "patient":
        return renderPatient(data.patient_360);
      default:
        return renderPathwayDetails(data);
    }
  }

  function renderDrawer() {
    if (!state.drawer.pathwayId) return "";
    if (state.drawer.loading) {
      return `
        <div class="drawer-overlay" data-action="close-drawer"></div>
        <aside class="pathway-drawer-shell">
          <div class="loading-state">Loading pathway drawer...</div>
        </aside>
      `;
    }
    if (state.drawer.error) {
      return `
        <div class="drawer-overlay" data-action="close-drawer"></div>
        <aside class="pathway-drawer-shell">
          <div class="error-state">${esc(state.drawer.error)}</div>
        </aside>
      `;
    }

    const drawerState = getDrawerState();
    const data = drawerState.data;
    if (!data) return "";

    const counts = getSectionCounts();
    const navItems = [
      "pathway-details",
      "actions",
      "outpatient",
      "inpatient",
      "histology",
      "radiology",
      "mdt",
      "tests",
      "ipt",
      "tracking",
      "patient",
    ];

    return `
      <div class="drawer-overlay" data-action="close-drawer"></div>
      <aside class="pathway-drawer-shell">
        <div class="pathway-drawer-header">
          <div class="drawer-summary-line">${esc(`${data.pathway.patient_name} | MRN: ${data.pathway.hospital_number || "No value"} | ${data.pathway.cancer_site || "Cancer pathway"} | Day ${data.pathway.days_on_pathway || 0}`)}</div>
          <button class="drawer-link-button" type="button">${icon("link")}External Links${icon("chevron-down")}</button>
          <div class="drawer-pill">${icon("clock")}PTL Last Updated: ${window.C360.PTL_LAST_UPDATED}</div>
          <button class="drawer-action-button" type="button">Create Action${icon("chevron-down")}</button>
          <button class="drawer-close" data-action="close-drawer" type="button">${icon("x")}</button>
        </div>
        <div class="pathway-drawer-body">
          <nav class="drawer-side-nav">
            ${navItems.map((key) => {
              const count = Number(counts[key] || 0);
              const showBadge = key !== "pathway-details" && key !== "patient";
              return `
                <button class="drawer-nav-item ${drawerState.activeSection === key ? "active" : ""}" data-action="drawer-section" data-value="${key}" type="button">
                  <span>${SECTION_LABELS[key]}</span>
                  ${showBadge ? renderCountBadge(count, false) : ""}
                </button>
              `;
            }).join("")}
          </nav>
          <div class="drawer-content">
            ${renderSection(data)}
          </div>
        </div>
      </aside>
    `;
  }

  function renderEmbeddedDrawer(data, embeddedState) {
    currentDrawerState = {
      pathwayId: data?.pathway?.pathway_id || "embedded",
      loading: false,
      error: "",
      data,
      activeSection: embeddedState?.activeSection || "pathway-details",
      selectedActionId: embeddedState?.selectedActionId || null,
      selectedReportKey: embeddedState?.selectedReportKey || null,
      patientTab: embeddedState?.patientTab || "overview",
    };
    const html = `
      <div class="embedded-pathway-shell">
        <div class="pathway-drawer-header embedded-drawer-header">
          <div class="drawer-summary-line">${esc(`${data.pathway.patient_name} | MRN: ${data.pathway.hospital_number || "No value"} | ${data.pathway.cancer_site || "Cancer pathway"} | Day ${data.pathway.days_on_pathway || 0}`)}</div>
          <button class="drawer-link-button" type="button">${icon("link")}External Links${icon("chevron-down")}</button>
          <div class="drawer-pill">${icon("clock")}PTL Last Updated: ${window.C360.PTL_LAST_UPDATED}</div>
          <button class="drawer-action-button" type="button">Create Action${icon("chevron-down")}</button>
          <span></span>
        </div>
        <div class="pathway-drawer-body embedded-drawer-body">
          <nav class="drawer-side-nav">
            ${[
              "pathway-details",
              "actions",
              "outpatient",
              "inpatient",
              "histology",
              "radiology",
              "mdt",
              "tests",
              "ipt",
              "tracking",
              "patient",
            ].map((key) => {
              const count = Number((data.section_counts || []).find((item) => item.key === key)?.count || 0);
              const showBadge = key !== "pathway-details" && key !== "patient";
              return `
                <button class="drawer-nav-item ${currentDrawerState.activeSection === key ? "active" : ""}" data-action="embedded-drawer-section" data-value="${key}" type="button">
                  <span>${SECTION_LABELS[key]}</span>
                  ${showBadge ? renderCountBadge(count, false) : ""}
                </button>
              `;
            }).join("")}
          </nav>
          <div class="drawer-content">${renderSection(data)}</div>
        </div>
      </div>
    `;
    currentDrawerState = null;
    return html;
  }

  window.C360.drawer = { renderDrawer, renderEmbeddedDrawer };
})();
