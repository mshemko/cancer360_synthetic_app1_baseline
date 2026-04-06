(() => {
  const { state, esc, formatDate } = window.C360;

  const MONTHS = [
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "January 2025",
    "February",
    "March",
    "April",
    "May",
  ];

  const MONTH_POINTS = [
    "2024-06-01",
    "2024-07-01",
    "2024-08-01",
    "2024-09-01",
    "2024-10-01",
    "2024-11-01",
    "2024-12-01",
    "2025-01-01",
    "2025-02-01",
    "2025-03-01",
    "2025-04-01",
    "2025-05-01",
  ];

  const METRIC_COLORS = {
    first_opa: { accent: "#58a9d7", tint: "#e9f6fc", strong: "#d6eef9" },
    radiology: { accent: "#57c2bc", tint: "#edfafa", strong: "#d9f5f2" },
    ip_diagnostics: { accent: "#64be57", tint: "#edf9ef", strong: "#dff4e2" },
    op_diagnostics: { accent: "#9cb333", tint: "#f4f8e9", strong: "#ecf3d8" },
    endoscopy: { accent: "#e1b13d", tint: "#fcf8e8", strong: "#f4edca" },
    histology: { accent: "#df7b53", tint: "#fcf0eb", strong: "#f7dfd5" },
    follow_up_opa: { accent: "#db6795", tint: "#fdf0f6", strong: "#f8d8e8" },
    ipt: { accent: "#b676d2", tint: "#f7eefc", strong: "#ead8f5" },
    treatment: { accent: "#8d7df1", tint: "#f2f0fd", strong: "#e1ddfa" },
  };

  const TABLE_SET = {
    standard: [
      { key: "select", label: "", width: 44, sticky: "sticky-left-0" },
      { key: "pathway_day", label: "Pathway Day", width: 86, sticky: "sticky-left-44" },
      { key: "full_name", label: "Full Name", width: 170, sticky: "sticky-left-130" },
      { key: "nhs_number", label: "Nhs Number", width: 128 },
      { key: "mrn", label: "Mrn", width: 112 },
      { key: "diagnostic_title", label: "Diagnostic Title Value", width: 250 },
      { key: "clean_status", label: "Clean Diagnostic Status", width: 150 },
      { key: "ordered_date", label: "Ordered Date", width: 120 },
      { key: "scheduled_date", label: "Scheduled Date", width: 120 },
      { key: "attended_date", label: "Attended Date", width: 120 },
      { key: "reported_date", label: "Reported Date", width: 120 },
      { key: "open_actions", label: "# Open Actions", width: 110 },
      { key: "latest_action", label: "Latest Action", width: 170 },
      { key: "breach_28", label: "28 Day Breach Date", width: 170 },
    ],
    histology: [
      { key: "select", label: "", width: 44, sticky: "sticky-left-0" },
      { key: "pathway_day", label: "Pathway Day", width: 86, sticky: "sticky-left-44" },
      { key: "full_name", label: "Full Name", width: 170, sticky: "sticky-left-130" },
      { key: "nhs_number", label: "Nhs Number", width: 128 },
      { key: "mrn", label: "Mrn", width: 112 },
      { key: "diagnostic_title", label: "Diagnostic Title Value", width: 220 },
      { key: "clean_status", label: "Clean Diagnostic Status", width: 150 },
      { key: "attended_date", label: "Attended Date", width: 120 },
      { key: "reported_date", label: "Reported Date", width: 120 },
      { key: "open_actions", label: "# Open Actions", width: 110 },
      { key: "latest_action", label: "Latest Action", width: 170 },
      { key: "breach_28", label: "28 Day Breach Date", width: 160 },
      { key: "breach_31", label: "31 Day Breach Date", width: 160 },
      { key: "breach_62", label: "62 Day Breach Date", width: 160 },
    ],
    treatment: [
      { key: "select", label: "", width: 44, sticky: "sticky-left-0" },
      { key: "pathway_day", label: "Pathway Day", width: 86, sticky: "sticky-left-44" },
      { key: "full_name", label: "Full Name", width: 170, sticky: "sticky-left-130" },
      { key: "nhs_number", label: "Nhs Number", width: 128 },
      { key: "mrn", label: "Mrn", width: 112 },
      { key: "diagnostic_title", label: "Diagnostic Title Value", width: 340 },
      { key: "clean_status", label: "Clean Diagnostic Status", width: 150 },
      { key: "attended_date", label: "Attended Date", width: 120 },
      { key: "reported_date", label: "Reported Date", width: 120 },
      { key: "open_actions", label: "# Open Actions", width: 110 },
      { key: "latest_action", label: "Latest Action", width: 180 },
      { key: "breach_28", label: "28 Day Breach Date", width: 160 },
    ],
    ipt: [
      { key: "select", label: "", width: 44, sticky: "sticky-left-0" },
      { key: "pathway_day", label: "Pathway Day", width: 86, sticky: "sticky-left-44" },
      { key: "full_name", label: "Full Name", width: 170, sticky: "sticky-left-130" },
      { key: "nhs_number", label: "Nhs Number", width: 128 },
      { key: "mrn", label: "Mrn", width: 112 },
      { key: "tertiary_date", label: "Tertiary Date", width: 120 },
      { key: "tertiary_reason", label: "Tertiary Reason", width: 160 },
      { key: "sending_org", label: "Sending Org Name", width: 220 },
      { key: "receiving_org", label: "Receiving Org Name", width: 180 },
      { key: "sending_comment", label: "Tertiary Sending Comment", width: 180 },
      { key: "return_comment", label: "Tertiary Return Comment", width: 180 },
      { key: "sent_date", label: "Tertiary Sent Date", width: 130 },
      { key: "received_date", label: "Tertiary Received Date", width: 150 },
    ],
  };

  function ensureState() {
    if (!state.service.monthlyPerformance) {
      state.service.monthlyPerformance = {
        activeMetric: null,
        collapsedSections: {},
        chartMode: {},
        statusTab: {},
        iptSummaryMode: "received",
        iptTrendMode: "received",
        iptTableMode: "received",
        iptReasonFilter: "",
      };
    }
  }

  function colorFor(metricKey) {
    return METRIC_COLORS[metricKey] || METRIC_COLORS.first_opa;
  }

  function metricIcon(metricKey) {
    const base = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
    switch (metricKey) {
      case "first_opa":
        return `<svg ${base}><rect x="4" y="5" width="16" height="15" rx="2"></rect><path d="M8 3v4"></path><path d="M16 3v4"></path><path d="M4 10h16"></path></svg>`;
      case "radiology":
        return `<svg ${base}><rect x="5" y="5" width="14" height="14" rx="2"></rect><path d="M9 9h6v6H9z"></path><path d="m4 12 2 0"></path><path d="m18 12 2 0"></path><path d="m12 4 0 2"></path><path d="m12 18 0 2"></path></svg>`;
      case "ip_diagnostics":
        return `<svg ${base}><path d="M4 12h4l2-5 4 10 2-5h4"></path></svg>`;
      case "op_diagnostics":
        return `<svg ${base}><path d="M8 4v10"></path><path d="M16 4v10"></path><path d="M6 4h4"></path><path d="M14 4h4"></path><path d="M6 10h4"></path><path d="M14 10h4"></path><path d="M12 20v-6"></path></svg>`;
      case "endoscopy":
        return `<svg ${base}><path d="M6 6h6v6"></path><path d="M12 12c2 0 4 2 4 4v2"></path><path d="m16 7 4 0"></path><path d="m18 5 0 4"></path></svg>`;
      case "histology":
        return `<svg ${base}><circle cx="8" cy="8" r="2"></circle><circle cx="16" cy="7" r="2"></circle><circle cx="10" cy="16" r="2"></circle><path d="m9.5 9.5 5 5"></path><path d="m10 8 4 0"></path><path d="m8.8 10.2 1 4"></path></svg>`;
      case "follow_up_opa":
        return `<svg ${base}><path d="M4 7h16v10H4z"></path><path d="m4 8 8 6 8-6"></path></svg>`;
      case "ipt":
        return `<svg ${base}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M17 8h4"></path><path d="m19 6 2 2-2 2"></path></svg>`;
      case "treatment":
        return `<svg ${base}><path d="M10 3v5l-4 7a4 4 0 0 0 3.5 6h5A4 4 0 0 0 18 15l-4-7V3"></path><path d="M9 8h6"></path></svg>`;
      default:
        return window.C360.icon("grid");
    }
  }

  function infoIcon(text) {
    return `<span class="monthly-info-icon" title="${esc(text)}">i</span>`;
  }

  function monthSeries(values) {
    return MONTHS.map((label, index) => ({
      label,
      date: MONTH_POINTS[index],
      value: values[index],
    }));
  }

  function combinedSeries(payload) {
    return MONTHS.map((label, index) => ({
      label,
      date: MONTH_POINTS[index],
      order: payload.order?.[index] ?? null,
      scheduled: payload.scheduled?.[index] ?? null,
      attended: payload.attended?.[index] ?? null,
      report: payload.report?.[index] ?? null,
      turnaround: payload.turnaround?.[index] ?? null,
      report_turnaround: payload.report_turnaround?.[index] ?? null,
    }));
  }

  function buildRecord(values) {
    const [pathwayDay, fullName, nhs, mrn, diagnosticTitle, cleanStatus, orderedDate, scheduledDate, attendedDate, reportedDate, openActions, latestAction, breach28, breach31, breach62] = values;
    return {
      pathway_day: pathwayDay,
      full_name: fullName,
      nhs_number: nhs,
      mrn,
      diagnostic_title: diagnosticTitle,
      clean_status: cleanStatus,
      ordered_date: orderedDate,
      scheduled_date: scheduledDate,
      attended_date: attendedDate,
      reported_date: reportedDate,
      open_actions: openActions,
      latest_action: latestAction,
      breach_28: breach28,
      breach_31: breach31,
      breach_62: breach62,
    };
  }

  function getActiveMetric() {
    ensureState();
    return state.service.monthlyPerformance.activeMetric;
  }

  function isSectionCollapsed(metricKey) {
    ensureState();
    return !!state.service.monthlyPerformance.collapsedSections[metricKey];
  }

  function activeStatus(metric) {
    ensureState();
    return state.service.monthlyPerformance.statusTab[metric.key] || metric.defaultTab;
  }

  function activeTrend(metricKey) {
    ensureState();
    return state.service.monthlyPerformance.chartMode[metricKey] || "key-events";
  }

  function standardRows() {
    return {
      first_opa: {
        attended: [
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "Colorectal Surg 2WW New", "attended", "2024-02-02", "2024-02-03", "2024-02-09", null, 1, "Review Diagnostic Results", "2024-02-27"]),
          buildRecord([185, "White, Jennifer", "8509009452", "098330677", "Gynae 2WW New", "attended", "2024-11-10", "2024-11-11", "2024-11-18", null, 3, "Chase Histology Report", "2024-12-05"]),
          buildRecord([175, "Spencer, Hailey", "9728083096", "094596436", "Colorectal Surg 2WW Telepho...", "attended", "2024-11-20", "2024-11-21", "2024-11-28", null, 1, "Enquiry of Sample Status", "2024-12-15"]),
          buildRecord([142, "Simpson, Deborah", "3104110265", "009763252", "Colorectal Sarcoma 2W...", "attended", "2024-12-22", "2024-12-23", "2024-12-28", null, 1, "Update Tracking Note", "2025-01-17"]),
          buildRecord([90, "Kent, Mckenzie", "6395254765", "067870676", "Colorectal Sarcoma 2W...", "attended", "2025-02-12", "2025-02-13", "2025-02-18", null, 0, "No value", "2025-03-10"]),
          buildRecord([89, "Wilkins, Christine", "7289866432", "091565157", "Derm Telederm New", "attended", "2025-02-13", "2025-02-14", "2025-02-18", null, 0, "No value", "2025-03-11"]),
          buildRecord([89, "Hill, Robert", "5738926188", "002431857", "Gastro 2WW Tel New", "attended", "2025-02-13", "2025-02-14", "2025-02-18", null, 0, "No value", "2025-03-11"]),
          buildRecord([88, "Romero, Scott", "9450054667", "032256483", "Neurology Tel New", "attended", "2025-02-15", "2025-02-16", "2025-02-23", null, 0, "No value", "2025-03-12"]),
          buildRecord([88, "Spencer, Robert", "0026324057", "075946128", "Gynae Rapid Access New", "attended", "2025-02-14", "2025-02-15", "2025-02-19", null, 0, "No value", "2025-03-12"]),
          buildRecord([87, "Simpson, Jessica", "2731617942", "045769111", "Colorectal Surg 2WW Telepho...", "attended", "2025-02-16", "2025-02-17", "2025-02-24", null, 0, "No value", "2025-03-13"]),
          buildRecord([85, "James, Amy", "0226345041", "022831120", "Urology 2WW New", "attended", "2025-02-18", "2025-02-19", "2025-02-26", null, 0, "No value", "2025-03-15"]),
          buildRecord([84, "Chan, Nicholas", "0828003710", "042472215", "Neurology Tel New", "attended", "2025-02-19", "2025-02-20", "2025-02-26", null, 0, "No value", "2025-03-16"]),
        ],
        scheduled: [
          buildRecord([32, "Hughes, Martin", "8419920065", "053821240", "Colorectal Surg 2WW New", "scheduled", "2025-04-11", "2025-04-15", null, null, 1, "Clinical Review Required", "2025-04-23"]),
          buildRecord([29, "Parker, Susan", "6285214413", "072448509", "Gynae 2WW New", "scheduled", "2025-04-12", "2025-04-17", null, null, 0, "No value", "2025-04-24"]),
        ],
        unscheduled: [],
        cancelled: [
          buildRecord([24, "Bishop, Clare", "0723894104", "041225490", "Derm Telederm New", "cancelled", "2025-04-20", null, null, null, 2, "Update Tracking Note", "2025-05-01"]),
          buildRecord([23, "Holmes, Joshua", "4117283301", "035641922", "Gastro 2WW Tel New", "did not attend", "2025-04-21", "2025-04-24", null, null, 1, "Book Surgery", "2025-05-02"]),
        ],
      },
      follow_up_opa: {
        attended: [
          buildRecord([61, "Murray, Olivia", "6044332190", "071221104", "Gynaecology F/Up", "attended", "2025-03-14", "2025-03-15", "2025-03-19", null, 1, "Update Tracking Note", "2025-04-10"]),
          buildRecord([56, "West, Pauline", "1720938454", "031792650", "Breast F/Up", "attended", "2025-03-18", "2025-03-19", "2025-03-24", null, 0, "No value", "2025-04-14"]),
          buildRecord([48, "Bates, Leon", "9245513372", "064407320", "Urology F/Up", "attended", "2025-03-25", "2025-03-26", "2025-03-31", null, 2, "Clinical Review Required", "2025-04-20"]),
        ],
        scheduled: [
          buildRecord([18, "Mills, Rachel", "9241153304", "079520118", "Breast F/Up", "scheduled", "2025-04-25", "2025-04-28", null, null, 0, "No value", "2025-05-06"]),
        ],
        unscheduled: [],
        cancelled: [
          buildRecord([12, "Sharp, Daniel", "4628159304", "088400721", "Gynaecology F/Up", "cancelled", "2025-05-02", null, null, null, 1, "Reschedule GA Diagnostic", "2025-05-12"]),
        ],
      },
      radiology: {
        report_available: [
          buildRecord([1325, "Chavez, Robert", "5936996311", "006736951", "CT Thorax abdomen pel...", "reported", "2022-01-05", "2022-04-10", "2023-03-09", "2024-08-22", 1, "Update Tracking Note", "2024-10-22"]),
          buildRecord([1325, "Chavez, Robert", "5936996311", "006736951", "CT Abdomen and pelvis", "reported", "2021-12-09", "2022-04-02", "2023-02-22", "2024-07-22", 1, "Update Tracking Note", "2024-10-25"]),
          buildRecord([747, "Lucero, Stephen", "2607596361", "052553838", "CT Abdomen and pelvis", "reported", "2023-07-02", "2023-08-18", "2024-02-28", "2025-01-02", 2, "Clinical Review Required", "2023-05-23"]),
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "MRI Pelvis and rectum wi...", "reported", "2024-03-13", "2024-04-11", "2024-08-12", "2025-02-22", 1, "Review Diagnostic Results", "2024-02-27"]),
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "NM Bone thorax SPECT CT", "reported", "2024-02-29", "2024-04-08", "2024-08-06", "2025-02-10", 1, "Review Diagnostic Results", "2024-02-27"]),
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "US Endoanal sphincter scan", "reported", "2024-02-24", "2024-03-26", "2024-07-10", "2024-12-18", 1, "Review Diagnostic Results", "2024-02-27"]),
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "CT Thorax abdomen pel...", "reported", "2024-12-14", "2024-12-15", "2024-12-19", "2024-12-25", 1, "Review Diagnostic Results", "2025-01-14"]),
          buildRecord([467, "Perry, Brian", "4664316796", "058407589", "CT Pelvis", "reported", "2024-12-14", "2024-12-15", "2024-12-20", "2024-12-27", 1, "Review Diagnostic Results", "2025-01-14"]),
          buildRecord([185, "White, Jennifer", "8509009452", "098330677", "US Pelvis TA and transvaginal", "reported", "2024-11-22", "2024-12-01", "2025-01-16", "2025-03-27", 3, "Chase Histology Report", "2024-12-05"]),
          buildRecord([185, "Sims, Amy", "5657930599", "082334649", "MRI Lower leg Lt", "reported", "2024-11-25", "2024-12-06", "2025-01-26", "2025-04-16", 1, "Reschedule GA Diagnostic", "2024-12-05"]),
          buildRecord([185, "White, Jennifer", "8509009452", "098330677", "CT Abdomen and pelvis", "reported", "2024-11-20", "2024-12-06", "2025-01-26", "2025-04-16", 3, "Chase Histology Report", "2024-12-05"]),
          buildRecord([185, "Sims, Amy", "5657930599", "082334649", "MRI Wrist Both", "reported", "2024-11-19", "2024-12-05", "2025-01-23", "2025-04-11", 1, "Reschedule GA Diagnostic", "2024-12-05"]),
        ],
        attended: [
          buildRecord([61, "Mason, Donna", "6124539782", "061824509", "MRI Pelvis and rectum wi...", "attended", "2025-03-10", "2025-03-15", "2025-03-28", null, 1, "Clinical Review Required", "2025-04-19"]),
          buildRecord([58, "Khan, Elliot", "3033209841", "071109284", "US Abdomen", "attended", "2025-03-12", "2025-03-16", "2025-03-30", null, 0, "No value", "2025-04-20"]),
        ],
        scheduled: [
          buildRecord([22, "Logan, Ruth", "8214417783", "064208881", "CT Thorax abdomen pel...", "scheduled", "2025-04-25", "2025-05-01", null, null, 1, "Update Tracking Note", "2025-05-18"]),
        ],
        unscheduled: [
          buildRecord([18, "Gibson, Nigel", "7291883610", "049208177", "US Pelvis TA and transvaginal", "unscheduled", "2025-05-02", null, null, null, 1, "Book Surgery", "2025-05-25"]),
        ],
        cancelled: [
          buildRecord([14, "Day, Kirsty", "6311882447", "057188003", "MRI Groin Right", "cancelled", "2025-04-29", "2025-05-03", null, null, 0, "No value", "2025-05-29"]),
        ],
      },
      ip_diagnostics: {
        attended: [
          buildRecord([73, "Murphy, Jennifer", "0976845960", "004784745", "Brain Diagnostic", "attended", "2025-04-19", "2025-04-20", "2025-04-21", null, 3, "Chase Imaging Report", "2025-05-22"]),
          buildRecord([60, "Chan, Kathleen", "1233144038", "047350970", "Biopsy of lesion of nasal sinus ...", "attended", "2025-03-13", "2025-03-13", "2025-03-13", null, 0, "No value", "2025-05-28"]),
          buildRecord([60, "Hendrix, Erica", "7948452175", "046360525", "Diagnostic extraction of ...", "attended", "2025-03-12", "2025-03-12", "2025-03-12", null, 1, "Chase Endoscopy Report", "2025-05-28"]),
          buildRecord([59, "Yoder, James", "6793288954", "043711718", "Drainage of lesion of breast", "attended", "2025-03-15", "2025-03-15", "2025-03-15", null, 0, "No value", "2025-05-29"]),
          buildRecord([54, "Parker, Christopher", "5320964119", "035502150", "Brain Diagnostic", "attended", "2025-03-22", "2025-03-22", "2025-03-22", null, 1, "Chase Imaging Report", "2025-06-03"]),
          buildRecord([53, "Cunningham, Susan", "7505835510", "041332574", "Brain Diagnostic", "attended", "2025-03-27", "2025-03-27", "2025-03-27", null, 3, "Clinical Review Required", "2025-06-04"]),
          buildRecord([53, "Thomas, Joseph", "7736616715", "088887815", "Excision of lesion of colo...", "attended", "2025-03-20", "2025-03-20", "2025-03-20", null, 0, "No value", "2025-06-04"]),
          buildRecord([47, "Miller, Julia", "6912705820", "043800241", "Clinical Haematology ...", "attended", "2025-03-28", "2025-03-28", "2025-03-28", null, 2, "Update Tracking Note", "2025-06-10"]),
          buildRecord([45, "Keller, Joseph", "0616901744", "044997326", "Rectal needle biopsy of ...", "attended", "2025-04-06", "2025-04-06", "2025-04-06", null, 3, "Chase Imaging Report", "2025-06-12"]),
          buildRecord([45, "Keller, Joseph", "0616901744", "044997326", "Open biopsy of lesion of ...", "attended", "2025-04-02", "2025-04-03", "2025-04-04", null, 3, "Chase Imaging Report", "2025-06-12"]),
          buildRecord([41, "Russell, Heather", "5962641131", "044852259", "Diagnostic extraction of ...", "attended", "2025-04-05", "2025-04-05", "2025-04-05", null, 2, "Chase Histology Report", "2025-06-16"]),
          buildRecord([41, "Nicholson, Stephanie", "0729596400", "046766454", "Open biopsy of lesion of ...", "attended", "2025-03-31", "2025-03-31", "2025-03-31", null, 2, "Chase Histology Report", "2025-06-16"]),
        ],
        scheduled: [
          buildRecord([19, "Porter, Ian", "3520198774", "073119540", "Diagnostic extraction of ...", "scheduled", "2025-05-01", "2025-05-04", null, null, 1, "Clinical Review Required", "2025-05-20"]),
        ],
        unscheduled: [
          buildRecord([17, "Crawford, Millie", "0812298733", "025167884", "Brain Diagnostic", "unscheduled", "2025-05-03", null, null, null, 0, "No value", "2025-05-22"]),
        ],
        cancelled: [
          buildRecord([12, "Sullivan, Perry", "5701909246", "055884392", "Drainage of lesion of breast", "cancelled", "2025-05-06", "2025-05-08", null, null, 1, "Update Tracking Note", "2025-05-27"]),
        ],
      },
      op_diagnostics: {
        attended: [
          buildRecord([89, "Wilkins, Christine", "7289866432", "091565157", "Derm Minor OP F/Up", "attended", "2025-02-10", "2025-02-11", "2025-02-12", null, 3, "Enquiry of Sample Status", "2025-04-08"]),
          buildRecord([89, "Wilkins, Christine", "7289866432", "091565157", "Derm Biopsy F/Up", "attended", "2025-02-12", "2025-02-13", "2025-02-14", null, 3, "Enquiry of Sample Status", "2025-04-08"]),
          buildRecord([72, "Hines, Maria", "8739197151", "057197609", "CWF Non Theatre ...", "attended", "2025-03-09", "2025-03-09", "2025-03-09", null, 0, "No value", "2025-04-18"]),
          buildRecord([72, "Hines, Maria", "8739197151", "057197609", "CWF Non Theatre ...", "attended", "2025-03-06", "2025-03-07", "2025-03-08", null, 0, "No value", "2025-04-18"]),
          buildRecord([72, "Hines, Maria", "8739197151", "057197609", "CWF Non Theatre ...", "attended", "2025-03-07", "2025-03-08", "2025-03-09", null, 0, "No value", "2025-04-18"]),
          buildRecord([67, "Fisher, William", "6500360045", "093621271", "Urol Flexi Cystoscopy Diag", "attended", "2025-02-26", "2025-02-27", "2025-02-28", null, 2, "Order Endoscopy", "2025-04-23"]),
          buildRecord([62, "George, Sara", "1671773570", "028305214", "Gynae-Colposcopy W...", "attended", "2025-03-18", "2025-03-18", "2025-03-18", null, 0, "No value", "2025-04-28"]),
          buildRecord([59, "Patterson, Jim", "5903594723", "040939866", "Derm Biopsy F/Up", "attended", "2025-03-15", "2025-03-15", "2025-03-15", null, 2, "Cancel OP Diagnostic", "2025-05-01"]),
          buildRecord([59, "Salas, Darius", "9114797721", "057163694", "Urol Flexi Cystoscopy Diag", "attended", "2025-03-17", "2025-03-17", "2025-03-17", null, 3, "Cancel OP Diagnostic", "2025-05-01"]),
          buildRecord([58, "Rose, John", "7970920286", "014430106", "Urol Flexi Cystoscopy Diag", "attended", "2025-03-17", "2025-03-17", "2025-03-17", null, 3, "Clinical Review Required", "2025-05-02"]),
          buildRecord([57, "Cooper, Jason", "5026073022", "011830209", "Derm Biopsy F/Up", "attended", "2025-03-18", "2025-03-18", "2025-03-18", null, 2, "Enquiry of Sample Status", "2025-05-03"]),
          buildRecord([57, "Reed, Steven", "7948556008", "036477041", "Urol Flexi Cystoscopy Diag", "attended", "2025-03-21", "2025-03-21", "2025-03-21", null, 0, "No value", "2025-05-03"]),
        ],
        scheduled: [
          buildRecord([18, "Ng, Aaron", "7705106421", "094174620", "Derm Minor OP F/Up", "scheduled", "2025-05-01", "2025-05-06", null, null, 1, "Bring Forward Endoscopy", "2025-05-20"]),
        ],
        unscheduled: [
          buildRecord([14, "Boyd, Flora", "6044177310", "039164880", "Gynae-Colposcopy W...", "unscheduled", "2025-05-04", null, null, null, 0, "No value", "2025-05-23"]),
        ],
        cancelled: [
          buildRecord([11, "Fitzgerald, Max", "4905102271", "056118473", "Derm Biopsy F/Up", "cancelled", "2025-05-06", "2025-05-08", null, null, 2, "Cancel OP Diagnostic", "2025-05-27"]),
        ],
      },
      endoscopy: {
        unscheduled: [
          buildRecord([7, "King, Benjamin", "4910122467", "068958046", "Other specified other ...", "ordered", "2025-05-11", null, null, null, 1, "Chase Histology Report", "2025-06-08"]),
          buildRecord([4, "Rogers, Andrew", "4242402267", "075930502", "Endoscopic resection of ...", "unscheduled", "2025-05-11", null, null, null, 0, "No value", "2025-06-11"]),
          buildRecord([4, "Sweeney, Diana", "6600531920", "090370503", "Diagnostic fibreoptic ...", "ordered", "2025-05-11", null, null, null, 2, "Update Tracking Note", "2025-06-11"]),
          buildRecord([2, "Barajas, Sharon", "2091197090", "087493363", "Unspecified diagnostic ...", "unscheduled", "2025-05-11", null, null, null, 1, "Book GA Diagnostic", "2025-06-13"]),
        ],
        scheduled: [
          buildRecord([22, "Patel, Daria", "6311442980", "064003281", "Diagnostic fibreoptic ...", "scheduled", "2025-04-28", "2025-05-06", null, null, 1, "Bring Forward Endoscopy", "2025-05-28"]),
        ],
        attended: [
          buildRecord([33, "Russell, Mae", "7355114408", "094171933", "Endoscopic resection of ...", "attended", "2025-04-21", "2025-04-24", "2025-04-25", null, 1, "Review Diagnostic Results", "2025-05-19"]),
        ],
        cancelled: [
          buildRecord([16, "Green, Steven", "1733019422", "049100827", "Other specified other ...", "cancelled", "2025-05-02", "2025-05-05", null, null, 0, "No value", "2025-05-24"]),
        ],
      },
      histology: {
        report_available: [
          buildRecord([53, "Morse, Steven", "0142666986", "052041979", "Histology, tissue", "reported", null, null, "2025-04-14", "2025-05-10", 1, "Chase Endoscopy Report", "2025-04-16", "2025-04-19", "2025-05-20"]),
          buildRecord([47, "Warren, Todd", "1097622003", "069675854", "Non-gynaecology ...", "reported", null, null, "2025-04-18", "2025-04-23", 3, "Enquiry of Sample Status", "2025-04-22", "2025-04-25", "2025-05-26"]),
          buildRecord([47, "Watkins, Tammy", "7918795971", "051604617", "Histopathology, tissue", "reported", null, null, "2025-03-30", "2025-04-07", 3, "Clinical Review Required", "2025-04-22", "2025-04-25", "2025-05-26"]),
          buildRecord([47, "Warren, Todd", "1097622003", "069675854", "Non-gynaecology ...", "reported", null, null, "2025-04-19", "2025-04-25", 3, "Enquiry of Sample Status", "2025-04-22", "2025-04-25", "2025-05-26"]),
          buildRecord([47, "Watkins, Tammy", "7918795971", "051604617", "Histopathology, tissue", "reported", null, null, "2025-03-30", "2025-04-07", 3, "Clinical Review Required", "2025-04-22", "2025-04-25", "2025-05-26"]),
          buildRecord([47, "Warren, Todd", "1097622003", "069675854", "Non-gynaecology ...", "reported", null, null, "2025-04-18", "2025-04-24", 3, "Enquiry of Sample Status", "2025-04-22", "2025-04-25", "2025-05-26"]),
          buildRecord([44, "Thomas, Mary", "1816943609", "077540773", "Histology, tissue", "reported", null, null, "2025-04-10", "2025-05-11", 0, "No value", "2025-04-25", "2025-04-28", "2025-05-29"]),
          buildRecord([34, "Clark, David", "9359939251", "045164987", "Non-gynaecology ...", "reported", null, null, "2025-04-21", "2025-04-23", 2, "Update Tracking Note", "2025-05-05", "2025-05-08", "2025-06-08"]),
          buildRecord([34, "Clark, David", "9359939251", "045164987", "Histology, tissue", "reported", null, null, "2025-04-21", "2025-04-23", 2, "Update Tracking Note", "2025-05-05", "2025-05-08", "2025-06-08"]),
          buildRecord([24, "Morris, Michael", "0706239887", "032378006", "Histology, tissue", "reported", null, null, "2025-04-26", "2025-05-02", 3, "Chase Histology Report", "2025-05-15", "2025-05-18", "2025-06-18"]),
          buildRecord([24, "Morris, Michael", "0706239887", "032378006", "Non-gynaecology ...", "reported", null, null, "2025-04-25", "2025-04-30", 3, "Chase Histology Report", "2025-05-15", "2025-05-18", "2025-06-18"]),
          buildRecord([22, "Black, Christina", "1370251496", "087875357", "Non-gynaecology ...", "reported", null, null, "2025-04-19", "2025-04-28", 1, "Bring Forward Endoscopy", "2025-05-17", "2025-05-20", "2025-06-20"]),
        ],
        attended: [
          buildRecord([52, "Lowe, Gary", "6055114808", "045008731", "Histology, tissue", "attended", null, null, "2025-04-14", null, 1, "Enquiry of Sample Status", "2025-04-18", "2025-04-21", "2025-05-22"]),
        ],
        scheduled: [
          buildRecord([29, "Ramsey, Janet", "8900557714", "063401182", "Histopathology, tissue", "scheduled", null, null, null, null, 0, "No value", "2025-05-10", "2025-05-13", "2025-06-13"]),
        ],
        unscheduled: [],
        cancelled: [
          buildRecord([17, "Ross, Kelvin", "4302517663", "022951880", "Non-gynaecology ...", "did not attend", null, null, null, null, 2, "Update Tracking Note", "2025-05-20", "2025-05-23", "2025-06-23"]),
        ],
      },
      treatment: {
        attended: [
          buildRecord([55, "Howard, Jeffrey", "8922358377", "047857233", "Medical termination of pregnancy | Medic", "attended", null, null, "2025-03-22", null, 2, "Order Endoscopy", "2025-05-12"]),
          buildRecord([53, "Freeman, Angela", "4026641544", "027155649", "Left hemicolectomy and ileostomy HFQ", "attended", null, null, "2025-03-20", null, 2, "Chase Imaging Report", "2025-05-14"]),
          buildRecord([50, "Bruce, Haley", "3026322790", "045602732", "Insertion of prosthesis for breast", "attended", null, null, "2025-03-22", null, 1, "Clinical Review Required", "2025-05-17"]),
          buildRecord([47, "Warren, Todd", "1097622003", "069675854", "Excision of lesion of salivary gland NEC", "attended", null, null, "2025-04-24", null, 3, "Enquiry of Sample Status", "2025-05-20"]),
          buildRecord([40, "Barton, David", "1177493672", "013271950", "Left hemicolectomy and end to end anastomosis of colon to rectum", "attended", null, null, "2025-04-08", null, 0, "No value", "2025-05-27"]),
          buildRecord([35, "Love, Brandon", "4282917189", "038851561", "Excision of lesion of tongue", "attended", null, null, "2025-04-11", null, 3, "Review Diagnostic Results", "2025-06-01"]),
          buildRecord([35, "Day, Jesse", "6867728133", "056436942", "Lipofilling of breast", "attended", null, null, "2025-04-15", null, 1, "Chase Endoscopy Report", "2025-06-01"]),
          buildRecord([30, "Lewis, Autumn", "7377960550", "035852110", "Elective lower uterine segment caesarean delivery", "attended", null, null, "2025-04-15", null, 1, "Book Surgery", "2025-06-06"]),
          buildRecord([29, "Tate, Katherine", "7697785891", "070526428", "Excision of substernal thyroid tissue", "attended", null, null, "2025-04-18", null, 3, "Reschedule GA Diagnostic", "2025-06-07"]),
          buildRecord([29, "Mitchell, Charles", "1194536123", "093107933", "Insertion of prosthesis for breast", "attended", null, null, "2025-04-15", null, 2, "Enquiry of Sample Status", "2025-06-07"]),
          buildRecord([27, "Rios, Laura", "5308283864", "099159085", "Left hemicolectomy and end to end anastomosis of colon to rectum", "attended", null, null, "2025-04-20", null, 2, "Review Diagnostic Results", "2025-06-09"]),
          buildRecord([24, "Garcia, Jay", "5161875433", "085647698", "Left hemicolectomy and anastomosis NEC", "attended", null, null, "2025-04-25", null, 0, "No value", "2025-06-12"]),
        ],
        scheduled: [],
        unscheduled: [],
        cancelled: [
          buildRecord([13, "Humphrey, Elsie", "7216684042", "046778510", "Insertion of prosthesis for breast", "cancelled", null, null, null, null, 1, "Reschedule GA Diagnostic", "2025-06-21"]),
        ],
      },
    };
  }

  function iptRows() {
    const received = [
      [11, "Jones, Trevor", "8903046389", "076563438", "2025-05-03", "Treatment", "ST HELIER HOSPITAL", "Notional Hospital", "MRI Consistent With Cancer", "surgery done", "2025-05-03", "2025-05-03"],
      [74, "Jones, Amy", "0453590270", "051229462", "2025-05-05", "MDT Discussion and Subsequ...", "IMPERIAL - QUEEN ...", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-05", "2025-05-05"],
      [20, "Bowen, Rebecca", "6904980265", "007422120", "2025-05-01", "Staging", "HILLINGDON HOSPITAL", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-01", "2025-05-01"],
      [4, "Carlson, Jacob", "0570128456", "020037494", "2025-05-11", "Diagnosis", "BART'S HEALTH NHS TRUST", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-11", "2025-05-11"],
      [88, "Spencer, Robert", "0026324057", "075946128", "2025-03-18", "MDT Discussion", "ST THOMAS' HOSPITAL (GUY'...", "Notional Hospital", "MRI Consistent With Cancer", "surgery done", "2025-03-18", "2025-03-18"],
      [18, "Carpenter, Michele", "6742178846", "017285398", "2025-05-08", "Diagnosis", "BART'S HEALTH NHS TRUST", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-08", "2025-05-08"],
      [14, "Johnson, Michelle", "1335558335", "032703869", "2025-05-07", "Primary Treatment", "ST PETER'S HOSPITAL", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-07", "2025-05-07"],
      [0, "Tyler, Jerome", "5539692458", "060266347", "2025-05-11", "Primary Treatment", "ST PETER'S HOSPITAL", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-11", "2025-05-11"],
      [20, "Hall, Stacey", "7492408039", "000381803", "2025-05-08", "Diagnosis", "IMPERIAL - ST MARY'S HOSPITAL", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-08", "2025-05-08"],
      [10, "Cooper, Ronnie", "1588685651", "050322252", "2025-05-04", "Treatment", "ROYAL SHREWSBURY ...", "Notional Hospital", "MRI Consistent With Cancer", "surgery done", "2025-05-04", "2025-05-04"],
      [42, "Harper, Kristin", "3001499317", "093530193", "2025-04-21", "Staging", "Meadow House Hospice (Ealing)", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-04-21", "2025-04-21"],
      [34, "Hart, Gina", "2156251208", "096917870", "2025-05-03", "Primary Treatment", "East Suffolk and North Essex NH...", "Notional Hospital", "Diagnosis & Treatment", "patient seen privately", "2025-05-03", "2025-05-03"],
    ].map((row) => ({
      pathway_day: row[0],
      full_name: row[1],
      nhs_number: row[2],
      mrn: row[3],
      tertiary_date: row[4],
      tertiary_reason: row[5],
      sending_org: row[6],
      receiving_org: row[7],
      sending_comment: row[8],
      return_comment: row[9],
      sent_date: row[10],
      received_date: row[11],
    }));

    const sent = [
      [19, "Bond, Anna", "0403118280", "040311828", "2025-05-06", "Treatment", "Notional Hospital", "ST HELIER HOSPITAL", "Diagnosis & Treatment", "accepted", "2025-05-06", "2025-05-09"],
      [31, "Mcguire, Josh", "8422903155", "051182420", "2025-05-08", "Staging", "Notional Hospital", "BART'S HEALTH NHS TRUST", "MRI Consistent With Cancer", "accepted", "2025-05-08", "2025-05-12"],
      [12, "Stewart, Alice", "7172205149", "084410220", "2025-05-10", "Diagnosis", "Notional Hospital", "IMPERIAL - QUEEN ...", "Diagnosis & Treatment", "accepted", "2025-05-10", "2025-05-14"],
    ].map((row) => ({
      pathway_day: row[0],
      full_name: row[1],
      nhs_number: row[2],
      mrn: row[3],
      tertiary_date: row[4],
      tertiary_reason: row[5],
      sending_org: row[6],
      receiving_org: row[7],
      sending_comment: row[8],
      return_comment: row[9],
      sent_date: row[10],
      received_date: row[11],
    }));

    return { received, sent };
  }

  function buildMetrics() {
    if (window.C360.__monthlyMetricsCache) return window.C360.__monthlyMetricsCache;

    // TODO: move this deterministic monthly performance layer to a backend snapshot API
    // once warehouse snapshot tables exist for OPA, diagnostics, IPT, histology, and treatment metrics.
    const rows = standardRows();
    const iptData = iptRows();

    const metrics = {
      first_opa: {
        key: "first_opa",
        name: "First OPA",
        chips: ["First OPA"],
        kpis: [
          ["Order Day", "Day 3", "Mean ordered day for first outpatient appointments completed in the last month"],
          ["Scheduled Day", "Day 4", "Mean scheduled day for first outpatient appointments completed in the last month"],
          ["Attended Day", "Day 10", "Mean attended day for first outpatient appointments completed in the last month"],
          ["Turn Around Time", "7 Days", "Mean turn around time between order and attendance in the last month"],
        ],
        tabs: [["unscheduled", "Unscheduled", 0], ["scheduled", "Scheduled", 263], ["attended", "Attended", 744], ["cancelled", "Cancelled/DNA", 1526]],
        defaultTab: "attended",
        tableType: "standard",
        rows: rows.first_opa,
        summaryRows: [["Day 3", "Order Day"], ["Day 4", "Scheduled Day"], ["Day 10", "Attended Day"], ["7 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [3.5, 3.0, 4.0, 3.8, 3.0, 3.7, 3.1, 3.15, 3.2, 3.2, 2.8, 2.9],
          scheduled: [4.5, 3.9, 4.95, 4.8, 4.0, 4.75, 4.1, 4.1, 4.15, 4.15, 3.75, 3.9],
          attended: [10.1, 9.6, 10.35, 10.15, 9.65, 10.1, 9.6, 10.3, 9.8, 9.7, 9.85, 9.6],
          turnaround: [6.6, 6.6, 6.35, 6.35, 6.65, 6.4, 6.5, 6.55, 6.65, 6.5, 6.8, 6.7],
        }),
      },
      radiology: {
        key: "radiology",
        name: "Radiology",
        chips: ["CT", "MRI", "US", "X-ray"],
        kpis: [["Order Day", "Day 2", "Mean ordered day"], ["Scheduled Day", "Day 3", "Mean scheduled day"], ["Attended Day", "Day 8", "Mean attended day"], ["Report Day", "Day 16", "Mean report day"], ["Report Turn Around Time", "8 Days", "Mean days from attendance to report"], ["Turn Around Time", "14 Days", "Mean days from order to report"]],
        tabs: [["unscheduled", "Unscheduled", 594], ["scheduled", "Scheduled", 2331], ["attended", "Attended", 3133], ["report_available", "Report Available", 129], ["cancelled", "Cancelled/DNA", 1112]],
        defaultTab: "report_available",
        tableType: "standard",
        rows: rows.radiology,
        summaryRows: [["Day 2", "Order Day"], ["Day 3", "Scheduled Day"], ["Day 8", "Attended Day"], ["Day 16", "Report Day"], ["8 Days", "Report Turn Around Time"], ["14 Days", "Turn Around Time"]],
        summaryChips: ["CT", "MRI", "US", "X-ray"],
        chart: combinedSeries({
          order: [2.0, 4.6, 1.7, 1.9, 1.8, 1.9, 2.8, 2.0, 2.0, 2.1, 1.9, 1.1],
          scheduled: [3.3, 5.8, 2.9, 3.1, 3.0, 3.1, 4.0, 3.2, 3.3, 3.5, 3.1, 1.4],
          attended: [9.1, 11.4, 8.0, 8.4, 8.3, 7.8, 9.1, 8.7, 8.8, 9.6, 8.7, 2.9],
          report: [18.2, 20.3, 16.2, 16.9, 16.8, 15.6, 16.0, 17.5, 17.6, 19.4, 17.6, 4.9],
          turnaround: [14.1, 14.5, 13.2, 13.8, 13.7, 12.9, 14.2, 13.8, 13.7, 14.9, 14.0, 5.1],
          report_turnaround: [7.9, 8.9, 8.2, 8.5, 8.5, 7.8, 8.4, 8.8, 8.8, 9.8, 8.9, 2.0],
        }),
      },
      ip_diagnostics: {
        key: "ip_diagnostics",
        name: "IP Diagnostics",
        chips: ["IP Diagnostic"],
        kpis: [["Order Day", "Day 4", "Mean ordered day"], ["Scheduled Day", "Day 5", "Mean scheduled day for diagnostics completed in the last month"], ["Attended Day", "Day 5", "Mean attended day"], ["Turn Around Time", "1 Days", "Mean turn around time"]],
        tabs: [["unscheduled", "Unscheduled", 7], ["scheduled", "Scheduled", 3], ["attended", "Attended", 176], ["cancelled", "Cancelled/DNA", 283]],
        defaultTab: "attended",
        tableType: "standard",
        rows: rows.ip_diagnostics,
        summaryRows: [["Day 4", "Order Day"], ["Day 5", "Scheduled Day"], ["Day 5", "Attended Day"], ["1 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [3.55, 5.55, 4.45, 5.45, 4.28, 4.02, 5.28, 5.40, 5.00, 5.10, 4.30, 4.98],
          scheduled: [4.18, 5.50, 4.85, 5.90, 4.65, 4.55, 5.60, 5.82, 5.42, 5.55, 4.28, 5.32],
          attended: [4.82, 6.00, 5.30, 6.35, 5.08, 5.04, 5.92, 6.24, 5.85, 5.98, 4.62, 5.63],
          turnaround: [1.27, 0.45, 0.85, 0.90, 0.80, 1.05, 0.64, 0.42, 0.85, 0.88, 0.32, 0.65],
        }),
      },
      op_diagnostics: {
        key: "op_diagnostics",
        name: "OP Diagnostics",
        chips: ["OP Diagnostic"],
        kpis: [["Order Day", "Day 4", "Mean ordered day"], ["Scheduled Day", "Day 5", "Mean scheduled day"], ["Attended Day", "Day 5", "Mean attended day"], ["Turn Around Time", "1 Days", "Mean turn around time"]],
        tabs: [["unscheduled", "Unscheduled", 8], ["scheduled", "Scheduled", 11], ["attended", "Attended", 375], ["cancelled", "Cancelled/DNA", 509]],
        defaultTab: "attended",
        tableType: "standard",
        rows: rows.op_diagnostics,
        summaryRows: [["Day 4", "Order Day"], ["Day 5", "Scheduled Day"], ["Day 5", "Attended Day"], ["1 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [4.52, 4.15, 4.75, 4.15, 4.88, 4.56, 5.26, 4.75, 5.40, 4.48, 4.72, 4.20],
          scheduled: [5.00, 4.56, 5.15, 4.46, 5.40, 4.90, 5.52, 5.05, 5.75, 5.00, 5.01, 4.52],
          attended: [5.48, 4.98, 5.56, 4.84, 5.88, 5.33, 5.98, 5.38, 6.08, 5.52, 5.34, 4.86],
          turnaround: [0.96, 0.83, 0.81, 0.69, 0.99, 0.77, 0.72, 0.63, 0.95, 0.69, 0.62, 0.66],
        }),
      },
      endoscopy: {
        key: "endoscopy",
        name: "Endoscopy",
        chips: ["Endoscopy"],
        kpis: [["Order Day", "Day 4", "Mean ordered day"], ["Scheduled Day", "Day 5", "Mean scheduled day"], ["Attended Day", "Day 5", "Mean attended day"], ["Turn Around Time", "1 Days", "Mean turn around time"]],
        tabs: [["unscheduled", "Unscheduled", 4], ["scheduled", "Scheduled", 7], ["attended", "Attended", 183], ["cancelled", "Cancelled/DNA", 305]],
        defaultTab: "unscheduled",
        tableType: "standard",
        rows: rows.endoscopy,
        summaryRows: [["Day 4", "Order Day"], ["Day 5", "Scheduled Day"], ["Day 5", "Attended Day"], ["1 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [2.95, 6.22, 4.65, 5.00, 5.72, 4.36, 4.55, 4.00, 5.15, 4.60, 4.05, 5.20],
          scheduled: [3.42, 5.78, 5.20, 5.38, 6.08, 4.72, 5.00, 4.48, 5.50, 4.76, 4.41, 5.50],
          attended: [3.95, 5.98, 5.75, 5.78, 6.45, 5.15, 5.40, 4.98, 5.88, 5.08, 4.76, 5.86],
          turnaround: [0.86, 0.20, 1.10, 0.78, 0.72, 0.79, 0.85, 0.98, 0.74, 0.48, 0.71, 0.66],
        }),
      },
      histology: {
        key: "histology",
        name: "Histology",
        chips: ["Histology"],
        kpis: [["Order Day", "—", "No reliable ordered-day snapshot is available for histology"], ["Scheduled Day", "—", "No reliable scheduled-day snapshot is available for histology"], ["Attended Day", "Day 8", "Mean attended day"], ["Report Day", "Day 16", "Mean report day"], ["Report Turn Around Time", "8 Days", "Mean days from attendance to report"], ["Turn Around Time", "—", "No reliable end-to-end turn around time is available"]],
        tabs: [["unscheduled", "Unscheduled", 0], ["scheduled", "Scheduled", 1451], ["attended", "Attended", 1925], ["report_available", "Report Available", 76], ["cancelled", "Cancelled/DNA", 611]],
        defaultTab: "report_available",
        tableType: "histology",
        rows: rows.histology,
        summaryRows: [["—", "Order Day"], ["—", "Scheduled Day"], ["Day 8", "Attended Day"], ["Day 16", "Report Day"], ["8 Days", "Report Turn Around Time"], ["—", "Turn Around Time"]],
        chart: combinedSeries({
          attended: [7.8, 9.7, 8.4, 8.2, 8.9, 7.7, 8.5, 8.4, 8.9, 8.9, 9.5, 2.8],
          report: [15.7, 19.4, 16.8, 16.3, 17.8, 15.4, 17.0, 16.8, 17.8, 17.6, 19.1, 5.1],
          report_turnaround: [7.9, 9.7, 8.4, 8.1, 8.9, 7.7, 8.5, 8.4, 8.9, 8.7, 9.6, 2.3],
        }),
      },
      follow_up_opa: {
        key: "follow_up_opa",
        name: "Follow-up OPA",
        chips: ["Follow-up OPA"],
        kpis: [["Order Day", "Day 4", "Mean ordered day"], ["Scheduled Day", "Day 5", "Mean scheduled day"], ["Attended Day", "Day 9", "Mean attended day"], ["Turn Around Time", "5 Days", "Mean turn around time"]],
        tabs: [["unscheduled", "Unscheduled", 1], ["scheduled", "Scheduled", 102], ["attended", "Attended", 411], ["cancelled", "Cancelled/DNA", 618]],
        defaultTab: "attended",
        tableType: "standard",
        rows: rows.follow_up_opa,
        summaryRows: [["Day 4", "Order Day"], ["Day 5", "Scheduled Day"], ["Day 9", "Attended Day"], ["5 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [4.0, 3.9, 4.1, 4.0, 4.2, 4.1, 4.3, 4.0, 4.2, 4.2, 4.1, 4.0],
          scheduled: [5.0, 4.8, 5.1, 5.0, 5.2, 5.1, 5.3, 5.0, 5.1, 5.2, 5.0, 5.0],
          attended: [8.8, 8.6, 9.0, 8.9, 9.1, 8.8, 9.2, 8.9, 9.0, 9.0, 8.8, 8.9],
          turnaround: [4.8, 4.7, 4.9, 4.9, 4.9, 4.7, 4.9, 4.9, 4.8, 4.8, 4.7, 4.9],
        }),
      },
      ipt: {
        key: "ipt",
        name: "IPT",
        type: "ipt",
        summaryRows: [["239", "# of received IPTs"], ["230", "# of received IPTs before day 38"], ["9", "# of received IPTs after day 38"], ["96%", "% of IPTs received before day 38"]],
        receivedKpis: [["# of received IPTs", "239"], ["# of received IPTs before day 38", "230"], ["# of received IPTs after day 38", "9"], ["% of IPTs received before day 38", "96%"]],
        sentKpis: [["# of sent IPTs", "63"], ["# of sent IPTs before day 38", "60"], ["# of sent IPTs after day 38", "3"], ["% of IPTs sent before day 38", "95%"]],
        summaryTabs: ["received", "sent"],
        trendData: Array.from({ length: 44 }, (_, index) => {
          const year = 2022 + Math.floor(index / 12);
          const month = (index % 12) + 1;
          const date = `${year}-${String(month).padStart(2, "0")}-01`;
          let before = (index % 5) + (index > 24 ? 2 : 0);
          let after = index % 11 === 0 ? 1 : 0;
          if (index > 34) before += (index - 34);
          if (index === 41) before = 38;
          if (index === 42) before = 55;
          if (index === 43) { before = 125; after = 5; }
          return { date, label: year === 2025 && month === 1 ? "2025" : month === 1 ? String(year) : "", before, after, sent_before: Math.max(0, Math.round(before * 0.28)), sent_after: Math.max(0, Math.round(after * 0.3)) };
        }),
        rows: iptData,
      },
      treatment: {
        key: "treatment",
        name: "Treatment",
        chips: ["IP Treatment"],
        kpis: [["Order Day", "Day 10", "Mean ordered day"], ["Scheduled Day", "Day 10", "Mean scheduled day"], ["Attended Day", "Day 39", "Mean attended day"], ["Turn Around Time", "29 Days", "Mean turn around time"]],
        tabs: [["unscheduled", "Unscheduled", 0], ["scheduled", "Scheduled", 0], ["attended", "Attended", 45], ["cancelled", "Cancelled/DNA", 69]],
        defaultTab: "attended",
        tableType: "treatment",
        rows: rows.treatment,
        summaryRows: [["Day 10", "Order Day"], ["Day 10", "Scheduled Day"], ["Day 39", "Attended Day"], ["29 Days", "Turn Around Time"]],
        chart: combinedSeries({
          order: [12.7, 11.5, 14.5, 14.2, 16.1, 13.5, 12.8, 14.8, 18.9, 13.0, 9.7, 10.8],
          scheduled: [13.0, 12.0, 14.7, 14.1, 16.8, 13.2, 12.7, 15.0, 19.0, 13.1, 9.9, 10.7],
          attended: [22.2, 14.8, 17.3, 24.9, 19.4, 22.4, 15.5, 25.2, 27.8, 17.6, 12.1, 66.0],
          turnaround: [9.2, 3.3, 2.6, 10.7, 3.3, 8.9, 2.7, 10.4, 8.8, 4.6, 2.4, 55.2],
        }),
      },
    };

    window.C360.__monthlyMetricsCache = metrics;
    return metrics;
  }

  function monthlyColumns() {
    const metrics = buildMetrics();
    return [
      [metrics.first_opa, metrics.radiology],
      [metrics.ip_diagnostics, metrics.op_diagnostics, metrics.endoscopy],
      [metrics.histology, metrics.follow_up_opa],
      [metrics.ipt, metrics.treatment],
    ];
  }

  function renderSummaryMetric(metric) {
    const colors = colorFor(metric.key);
    const collapsed = isSectionCollapsed(metric.key);
    const monthly = state.service.monthlyPerformance;
    const summaryMode = metric.key === "ipt" ? monthly.iptSummaryMode : null;
    const rows = metric.key === "ipt"
      ? (summaryMode === "sent" ? metric.sentKpis : metric.receivedKpis)
      : metric.summaryRows;
    const chips = metric.summaryChips || [];
    return `
      <section class="monthly-section-card">
        <div class="monthly-section-header" style="background:${colors.tint}; color:${colors.accent}">
          <button class="monthly-section-title" type="button" data-action="monthly-open-metric" data-metric="${metric.key}">
            <span class="monthly-section-icon" style="background:${colors.accent}; color:#fff">${metricIcon(metric.key)}</span>
            <span>${esc(metric.name)}</span>
          </button>
          <button class="monthly-section-chevron ${collapsed ? "collapsed" : ""}" type="button" data-action="monthly-toggle-section" data-metric="${metric.key}" aria-label="Toggle ${esc(metric.name)}">
            ${window.C360.icon("chevron-down")}
          </button>
        </div>
        ${collapsed ? "" : `
          <div class="monthly-section-body">
            ${chips.length ? `<div class="monthly-chip-row">${chips.map((chip) => `<span class="monthly-chip">${esc(chip)} <button type="button" aria-label="Remove ${esc(chip)}">x</button></span>`).join("")}</div>` : ""}
            ${metric.summaryTabs ? `
              <div class="monthly-inline-tabs">
                <button class="monthly-inline-tab ${summaryMode === "received" ? "active" : ""}" type="button" data-action="monthly-ipt-summary-mode" data-value="received">Received</button>
                <button class="monthly-inline-tab ${summaryMode === "sent" ? "active" : ""}" type="button" data-action="monthly-ipt-summary-mode" data-value="sent">Sent</button>
              </div>
            ` : ""}
            <div class="monthly-summary-rows">
              ${rows.map(([value, label]) => `
                <div class="monthly-summary-row">
                  <div class="monthly-summary-value">${esc(value)}</div>
                  <div class="monthly-summary-label">${esc(label)} ${infoIcon(`Monthly performance summary for ${label}`)}</div>
                </div>
              `).join("")}
            </div>
          </div>
        `}
      </section>
    `;
  }

  function renderExpandedMonthlyOverview() {
    return `
      <div class="monthly-board-wrap">
        <div class="monthly-board-grid">
          ${monthlyColumns().map((column) => `
            <section class="monthly-column-card">
              <div class="monthly-column-header">
                <div class="monthly-column-title-wrap">
                  <span class="monthly-column-icon">${window.C360.icon("gear")}</span>
                  <span class="monthly-column-title">Monthly performance</span>
                </div>
                <button class="monthly-column-expand" type="button" aria-label="Expand monthly performance">
                  ${window.C360.serviceUI?.serviceIcon ? window.C360.serviceUI.serviceIcon("expand-diagonal") : window.C360.icon("plus")}
                </button>
              </div>
              <div class="monthly-column-body">
                ${column.map((metric) => renderSummaryMetric(metric)).join("")}
              </div>
            </section>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderMetricHeader(metric) {
    const colors = colorFor(metric.key);
    return `
      <div class="monthly-drill-header" style="background:${colors.strong}">
        <div class="monthly-drill-header-main">
          <button class="monthly-back-button" type="button" data-action="monthly-back-overview">Back</button>
          <span class="monthly-drill-icon" style="background:${colors.accent}; color:#fff">${metricIcon(metric.key)}</span>
          <span class="monthly-drill-title" style="color:${colors.accent}">${esc(metric.name)}</span>
        </div>
        <button class="service-card-menu" type="button" aria-label="${esc(metric.name)} menu">${window.C360.serviceUI?.serviceIcon ? window.C360.serviceUI.serviceIcon("hamburger") : window.C360.icon("grid")}</button>
      </div>
    `;
  }

  function renderMetricCategory(metric) {
    if (!metric.chips?.length) return "";
    return `
      <div class="monthly-metric-category">
        <span>Metric Category:</span>
        <div class="monthly-metric-chip-wrap">
          ${metric.chips.map((chip) => `<span class="monthly-metric-chip">${esc(chip)} <button type="button" aria-label="Clear ${esc(chip)}">x</button></span>`).join("")}
        </div>
      </div>
    `;
  }

  function renderKpiCards(metric) {
    return `
      <div class="monthly-kpi-strip">
        ${metric.kpis.map(([label, value, help]) => `
          <div class="monthly-kpi-card">
            <div class="monthly-kpi-card-head">
              <span>${esc(label)}</span>
              ${infoIcon(help)}
            </div>
            <div class="monthly-kpi-card-value ${value === "—" || value === "â€”" ? "empty" : ""}">${esc(value === "â€”" ? "—" : value)}</div>
          </div>
        `).join("")}
      </div>
    `;
  }

  function metricChartOptions(metric, singleSeries) {
    const byMetric = {
      first_opa: { min: 2, max: 11, step: 1, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => String(v) },
      radiology: { min: 0, max: 22, step: 2, yTitle: "Pathway Day", xTitle: "Date", tickFormatter: (v) => String(v) },
      ip_diagnostics: { min: 3.4, max: 6.6, step: 0.4, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => Number(v).toFixed(1) },
      op_diagnostics: { min: 4.0, max: 6.2, step: 0.2, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => Number(v).toFixed(1) },
      endoscopy: { min: 3.0, max: 6.8, step: 0.5, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => Number(v).toFixed(1) },
      histology: { min: 2, max: 20, step: 2, yTitle: "Pathway Day", xTitle: "Date", tickFormatter: (v) => String(v) },
      follow_up_opa: { min: 3.5, max: 9.5, step: 0.5, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => Number(v).toFixed(1) },
      treatment: { min: 5, max: 65, step: 10, yTitle: "Mean Pathway Day", xTitle: "Date", tickFormatter: (v) => String(v) },
    }[metric.key] || { min: 0, max: 10, step: 1, yTitle: "Count", xTitle: "Date", tickFormatter: (v) => String(v) };
    if (singleSeries) return { ...byMetric, min: 0, tickFormatter: (v) => String(Math.round(Number(v))) };
    return byMetric;
  }

  function renderTrendToggles(metric) {
    const mode = activeTrend(metric.key);
    return `
      <div class="monthly-inline-tabs">
        <button class="monthly-inline-tab ${mode === "key-events" ? "active" : ""}" type="button" data-action="monthly-toggle-trend" data-metric="${metric.key}" data-value="key-events">Key events</button>
        <button class="monthly-inline-tab ${mode === "turnaround-time" ? "active" : ""}" type="button" data-action="monthly-toggle-trend" data-metric="${metric.key}" data-value="turnaround-time">Turn around time</button>
      </div>
    `;
  }

  function renderMetricPanelHeader(title, toggleHtml, extraClass = "") {
    return `
      <div class="monthly-metric-panel-header ${extraClass}">
        <div class="monthly-metric-panel-title">${title}</div>
        <div class="monthly-metric-panel-tools">
          ${toggleHtml || ""}
          <button class="service-export-button" type="button" aria-label="Export chart">${window.C360.serviceUI?.serviceIcon ? window.C360.serviceUI.serviceIcon("export") : window.C360.icon("grid")}</button>
        </div>
      </div>
    `;
  }

  function renderMetricChart(metric) {
    const serviceUI = window.C360.serviceUI || {};
    if (!serviceUI.lineChart) return `<div class="error-state">Chart renderer unavailable.</div>`;
    const mode = activeTrend(metric.key);
    const chart = metric.chart || [];
    let series = [];
    let options = metricChartOptions(metric, mode === "turnaround-time");
    if (mode === "turnaround-time") {
      const useReportTurnaround = metric.key === "radiology" || metric.key === "histology";
      series = [{
        key: useReportTurnaround ? "report_turnaround" : "turnaround",
        label: useReportTurnaround ? "Report Turn Around Time" : "Turn Around Time",
        color: "#4f83ff",
        width: 3.2,
      }];
    } else {
      if (chart.some((row) => row.order != null)) series.push({ key: "order", label: "Order Day", color: "#e56a9f", width: 3 });
      if (chart.some((row) => row.scheduled != null)) series.push({ key: "scheduled", label: "Scheduled Day", color: "#c1d85d", width: 3 });
      if (chart.some((row) => row.attended != null)) series.push({ key: "attended", label: "Attended Day", color: "#58b8ac", width: 3 });
      if (chart.some((row) => row.report != null)) series.push({ key: "report", label: "Report Day", color: "#af79c2", width: 3 });
    }
    return `
      <section class="monthly-metric-panel">
        ${renderMetricPanelHeader(`<span class="monthly-trending-label">Trending:</span>`, renderTrendToggles(metric))}
        <div class="monthly-metric-panel-body">
          ${serviceUI.lineChart(chart, series, options)}
        </div>
      </section>
    `;
  }

  function renderMetricStatusTabs(metric) {
    const current = activeStatus(metric);
    return `
      <div class="monthly-status-row">
        <div class="monthly-status-tabs">
          ${metric.tabs.map(([key, label, count]) => `
            <button class="monthly-status-tab ${current === key ? "active" : ""} ${key === "report_available" ? "report-tab" : ""}" type="button" data-action="monthly-set-status" data-metric="${metric.key}" data-value="${key}">
              <span>${esc(label)}</span>
              <span class="monthly-status-count">${esc(count)}</span>
            </button>
          `).join("")}
        </div>
        <button class="monthly-create-action" type="button" data-action="monthly-create-action">
          <span>Create Action</span>
          <span class="monthly-create-action-chevron">${window.C360.icon("chevron-down")}</span>
        </button>
      </div>
    `;
  }

  function formatMetricValue(key, value) {
    if (key === "select") return `<input type="checkbox" class="row-checkbox" aria-label="Select row">`;
    if (key === "open_actions") {
      const n = Number(value || 0);
      const tone = n >= 3 ? "tone-high" : n >= 2 ? "tone-mid" : "tone-low";
      return `<span class="monthly-open-actions ${tone}">${n}</span>`;
    }
    if (["ordered_date", "scheduled_date", "attended_date", "reported_date", "breach_28", "breach_31", "breach_62", "tertiary_date", "sent_date", "received_date"].includes(key)) {
      if (!value) return `<span class="muted-italic">No value</span>`;
      return esc(formatDate(value));
    }
    if (!value || value === "No value") return `<span class="muted-italic">No value</span>`;
    return esc(value);
  }

  function filteredMetricRows(metric) {
    ensureState();
    if (metric.type === "ipt") {
      const monthly = state.service.monthlyPerformance;
      const mode = monthly.iptTableMode === "sent" ? "sent" : "received";
      let rows = metric.rows[mode] || [];
      const reasonFilter = (monthly.iptReasonFilter || "").trim().toLowerCase();
      if (reasonFilter) {
        rows = rows.filter((row) => String(row.tertiary_reason || "").toLowerCase().includes(reasonFilter));
      }
      return rows;
    }
    return metric.rows[activeStatus(metric)] || [];
  }

  function monthlyColumnsFor(metric) {
    if (metric.tableType === "histology") return TABLE_SET.histology;
    if (metric.tableType === "treatment") return TABLE_SET.treatment;
    if (metric.tableType === "ipt") return TABLE_SET.ipt;
    return TABLE_SET.standard;
  }

  function renderMetricTable(metric) {
    const rows = filteredMetricRows(metric);
    const columns = monthlyColumnsFor(metric);
    return `
      <div class="monthly-table-shell">
        <div class="monthly-metric-table-wrap ptl-table-wrap">
          <table class="ptl-table monthly-metric-table">
            <thead>
              <tr>
                ${columns.map((column) => `
                  <th class="sticky-head ${column.sticky ? `sticky-col ${column.sticky}` : ""}" style="min-width:${column.width}px; width:${column.width}px">
                    ${esc(column.label)}
                  </th>
                `).join("")}
              </tr>
            </thead>
            <tbody>
              ${rows.map((row) => `
                <tr>
                  ${columns.map((column) => `
                    <td class="${column.sticky ? `sticky-col ${column.sticky}` : ""}" style="min-width:${column.width}px; width:${column.width}px">
                      ${formatMetricValue(column.key, row[column.key])}
                    </td>
                  `).join("")}
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderIptKpis(metric) {
    return `
      <div class="monthly-ipt-kpis">
        <section class="monthly-ipt-kpi-col">
          <div class="monthly-ipt-kpi-title">Received IPTs</div>
          ${metric.receivedKpis.map(([label, value]) => `
            <div class="monthly-ipt-stat-card">
              <div class="monthly-ipt-stat-label">${esc(label)}</div>
              <div class="monthly-ipt-stat-value">${esc(value)}</div>
            </div>
          `).join("")}
        </section>
        <section class="monthly-ipt-kpi-col">
          <div class="monthly-ipt-kpi-title">Sent IPTs</div>
          ${metric.sentKpis.map(([label, value]) => `
            <div class="monthly-ipt-stat-card">
              <div class="monthly-ipt-stat-label">${esc(label)}</div>
              <div class="monthly-ipt-stat-value">${esc(value)}</div>
            </div>
          `).join("")}
        </section>
      </div>
    `;
  }

  function renderIptBarChart(metric) {
    const monthly = state.service.monthlyPerformance;
    const mode = monthly.iptTrendMode === "sent" ? "sent" : "received";
    const width = 1180;
    const height = 430;
    const margins = { top: 22, right: 220, bottom: 72, left: 84 };
    const plotW = width - margins.left - margins.right;
    const plotH = height - margins.top - margins.bottom;
    const maxValue = 130;
    const slot = plotW / Math.max(metric.trendData.length, 1);
    const barW = Math.max(3, Math.min(14, slot * 0.72));
    const y = (value) => margins.top + plotH - (Number(value || 0) / maxValue) * plotH;
    const grid = Array.from({ length: 14 }, (_, index) => {
      const value = index * 10;
      const pos = y(value);
      return `
        <line x1="${margins.left}" y1="${pos}" x2="${margins.left + plotW}" y2="${pos}" stroke="#dbe2ec" stroke-width="1" />
        <text x="${margins.left - 10}" y="${pos + 4}" text-anchor="end" class="service-axis-tick">${value}</text>
      `;
    }).join("");

    const yearMarkers = ["2022", "2023", "2024", "2025"].map((year) => {
      const idx = metric.trendData.findIndex((point) => point.date.startsWith(`${year}-01`));
      if (idx < 0) return "";
      const xx = margins.left + idx * slot;
      return `<text x="${xx}" y="${height - 20}" class="service-axis-label">${year}</text>`;
    }).join("");

    const bars = metric.trendData.map((point, index) => {
      const before = mode === "sent" ? point.sent_before : point.before;
      const after = mode === "sent" ? point.sent_after : point.after;
      const x = margins.left + index * slot + (slot - barW) / 2;
      const beforeH = (before / maxValue) * plotH;
      const afterH = (after / maxValue) * plotH;
      const afterY = margins.top + plotH - afterH;
      const beforeY = margins.top + plotH - afterH - beforeH;
      return `
        <rect x="${x}" y="${beforeY}" width="${barW}" height="${beforeH}" fill="#7fc0ee" rx="1.5"></rect>
        <rect x="${x}" y="${afterY}" width="${barW}" height="${afterH}" fill="#e78ab0" rx="1.5"></rect>
      `;
    }).join("");

    const legendLabelA = mode === "sent" ? "Sent On or Before Day 38" : "Received On or Before Day 38";
    const legendLabelB = mode === "sent" ? "Sent After Day 38" : "Received After Day 38";

    return `
      <section class="monthly-metric-panel">
        ${renderMetricPanelHeader(`<span class="monthly-trending-label">Trending:</span><div class="monthly-inline-tabs"><button class="monthly-inline-tab ${mode === "received" ? "active" : ""}" type="button" data-action="monthly-ipt-trend-mode" data-value="received">Received IPTs</button><button class="monthly-inline-tab ${mode === "sent" ? "active" : ""}" type="button" data-action="monthly-ipt-trend-mode" data-value="sent">Sent IPTs</button></div>`)}
        <div class="monthly-metric-panel-body">
          <svg class="service-chart-svg" viewBox="0 0 ${width} ${height}">
            ${grid}
            ${bars}
            ${yearMarkers}
            <text x="24" y="${margins.top + plotH / 2}" transform="rotate(-90 24 ${margins.top + plotH / 2})" class="service-axis-title"># of Inter Provider Transfers</text>
            <text x="${margins.left + plotW / 2}" y="${height - 10}" text-anchor="middle" class="service-axis-label">Tertiary Received Date</text>
            <text x="${width - 180}" y="${margins.top + 36}" class="service-legend-title">LEGEND</text>
            <rect x="${width - 80}" y="${margins.top + 16}" width="64" height="24" fill="#f2f4f7" rx="3"></rect>
            <text x="${width - 70}" y="${margins.top + 32}" class="service-dropdown-label">Default</text>
            <rect x="${width - 180}" y="${margins.top + 62}" width="18" height="10" fill="#7fc0ee" rx="2"></rect>
            <text x="${width - 152}" y="${margins.top + 71}" class="service-legend-item">${legendLabelA}</text>
            <rect x="${width - 180}" y="${margins.top + 92}" width="18" height="10" fill="#e78ab0" rx="2"></rect>
            <text x="${width - 152}" y="${margins.top + 101}" class="service-legend-item">${legendLabelB}</text>
          </svg>
        </div>
      </section>
    `;
  }

  function renderStandardDrillDown(metric) {
    return `
      <div class="monthly-drill-shell">
        ${renderMetricHeader(metric)}
        <div class="monthly-drill-body">
          <div class="monthly-top-meta-row">
            <div class="monthly-drill-subtitle">Rolling Monthly Averages</div>
            ${renderMetricCategory(metric)}
          </div>
          ${renderKpiCards(metric)}
          ${renderMetricChart(metric)}
          ${renderMetricStatusTabs(metric)}
          ${renderMetricTable(metric)}
        </div>
      </div>
    `;
  }

  function renderIptDrillDown(metric) {
    const monthly = state.service.monthlyPerformance;
    const tableMode = monthly.iptTableMode === "sent" ? "sent" : "received";
    return `
      <div class="monthly-drill-shell">
        ${renderMetricHeader(metric)}
        <div class="monthly-drill-body">
          <div class="monthly-top-meta-row">
            <div class="monthly-drill-subtitle">Rolling Monthly Averages</div>
          </div>
          ${renderIptKpis(metric)}
          ${renderIptBarChart(metric)}
          <section class="monthly-metric-panel">
            ${renderMetricPanelHeader(`
              <span class="monthly-trending-label">IPTs for open Pathways</span>
              <div class="monthly-inline-tabs">
                <button class="monthly-inline-tab ${tableMode === "received" ? "active" : ""}" type="button" data-action="monthly-ipt-table-mode" data-value="received">Received IPTs</button>
                <button class="monthly-inline-tab ${tableMode === "sent" ? "active" : ""}" type="button" data-action="monthly-ipt-table-mode" data-value="sent">Sent IPTs</button>
              </div>
              <div class="monthly-ipt-table-toolbar">
                <label for="monthly-ipt-reason">Reason(s) for IPT:</label>
                <input id="monthly-ipt-reason" class="monthly-reason-filter" value="${esc(monthly.iptReasonFilter || "")}" placeholder="Search options...">
                <button class="monthly-create-action" type="button" data-action="monthly-create-action">
                  <span>Create Action</span>
                  <span class="monthly-create-action-chevron">${window.C360.icon("chevron-down")}</span>
                </button>
              </div>
            `)}
            <div class="monthly-metric-panel-body">
              ${renderMetricTable(metric)}
            </div>
          </section>
        </div>
      </div>
    `;
  }

  function renderDrillDown(metricKey) {
    const metric = buildMetrics()[metricKey];
    if (!metric) return "";
    return metric.type === "ipt" ? renderIptDrillDown(metric) : renderStandardDrillDown(metric);
  }

  function renderServiceContent({ overviewHeaderHtml, overviewBodyHtml }) {
    ensureState();
    const activeMetric = getActiveMetric();
    if (activeMetric) return renderDrillDown(activeMetric);
    if (state.service.sidebarExpanded) {
      return `
        ${overviewHeaderHtml}
        <div class="service-card-body">
          ${renderExpandedMonthlyOverview()}
        </div>
      `;
    }
    return `${overviewHeaderHtml}${overviewBodyHtml}`;
  }

  async function handleClick(dataset) {
    ensureState();
    const monthly = state.service.monthlyPerformance;
    switch (dataset.action) {
      case "toggle-service-rail":
        state.service.sidebarExpanded = !state.service.sidebarExpanded;
        if (!state.service.sidebarExpanded) monthly.activeMetric = null;
        window.C360.renderApp();
        return true;
      case "monthly-open-metric":
        state.service.sidebarExpanded = true;
        monthly.activeMetric = dataset.metric;
        window.C360.renderApp();
        return true;
      case "monthly-toggle-section":
        monthly.collapsedSections[dataset.metric] = !monthly.collapsedSections[dataset.metric];
        window.C360.renderApp();
        return true;
      case "monthly-back-overview":
        monthly.activeMetric = null;
        state.service.sidebarExpanded = false;
        window.C360.renderApp();
        return true;
      case "monthly-toggle-trend":
        monthly.chartMode[dataset.metric] = dataset.value;
        window.C360.renderApp();
        return true;
      case "monthly-set-status":
        monthly.statusTab[dataset.metric] = dataset.value;
        window.C360.renderApp();
        return true;
      case "monthly-ipt-summary-mode":
        monthly.iptSummaryMode = dataset.value;
        window.C360.renderApp();
        return true;
      case "monthly-ipt-trend-mode":
        monthly.iptTrendMode = dataset.value;
        window.C360.renderApp();
        return true;
      case "monthly-ipt-table-mode":
        monthly.iptTableMode = dataset.value;
        window.C360.renderApp();
        return true;
      case "monthly-create-action":
        window.location.href = "/actions";
        return true;
      default:
        return false;
    }
  }

  async function handleChange(event) {
    ensureState();
    if (event.target?.id === "monthly-ipt-reason") {
      state.service.monthlyPerformance.iptReasonFilter = event.target.value;
      window.C360.renderApp();
      return true;
    }
    return false;
  }

  window.C360.serviceMonthly = {
    ensureState,
    renderServiceContent,
    handleClick,
    handleChange,
  };
})();
