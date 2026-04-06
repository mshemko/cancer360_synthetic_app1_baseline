(() => {
  const DATE_FORMATTER = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const DATETIME_FORMATTER = new Intl.DateTimeFormat("en-GB", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  const MODULES = [
    {
      key: "ptl",
      title: "Cancer PTL",
      subtitle: "Cancer PTL Management tool",
      route: "/ptl",
      color: "#7b61c4",
      heroIcon: "bars",
      miniIcon: "list",
    },
    {
      key: "actions",
      title: "Cancer Actions",
      subtitle: "Action Management Tool",
      route: "/actions",
      color: "#5bb5d5",
      heroIcon: "clipboard",
      miniIcon: "clipboard",
    },
    {
      key: "service",
      title: "Service Overview",
      subtitle: "Bottleneck Analysis and Performance Dashboard",
      route: "/service-overview",
      color: "#d4467a",
      heroIcon: "donut",
      miniIcon: "grid",
    },
    {
      key: "team",
      title: "Team Overview",
      subtitle: "Actions overview and team performance analysis",
      route: "/team-overview",
      color: "#5b6dad",
      heroIcon: "network",
      miniIcon: "people",
    },
  ];

  function getRouteFromPath(pathname) {
    if (pathname === "/" || pathname === "/app") return "landing";
    if (pathname === "/ptl") return "ptl";
    if (pathname === "/actions") return "actions";
    if (pathname === "/service-overview") return "service";
    if (pathname === "/team-overview") return "team";
    return "landing";
  }

  function getInitialPtlFilters() {
    const params = new URLSearchParams(window.location.search);
    return {
      search: params.get("search") || "",
      cancerSite: params.get("cancer_site") || "",
      hospitalSite: params.get("hospital_site") || "",
      pathwayType: params.get("pathway_type") || "",
      pathwayTag: params.get("pathway_tag") || "",
    };
  }

  const state = {
    token: null,
    route: getRouteFromPath(window.location.pathname),
    ptl: {
      loading: false,
      error: "",
      rows: [],
      summary: null,
      sidebarOpen: false,
      activeTab: "full",
      recentDays: 2,
      filterSections: {},
      filters: getInitialPtlFilters(),
    },
    drawer: {
      pathwayId: null,
      loading: false,
      error: "",
      data: null,
      activeSection: "pathway-details",
      selectedActionId: null,
      selectedReportKey: null,
      patientTab: "overview",
    },
  };

  const dom = {
    routeRoot: document.getElementById("route-root"),
    filterRoot: document.getElementById("filter-root"),
    drawerRoot: document.getElementById("drawer-root"),
    avatar: document.getElementById("nav-avatar"),
  };

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatDate(value) {
    if (!value) return "No value";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "No value";
    return DATE_FORMATTER.format(date);
  }

  function formatDateTime(value) {
    if (!value) return "No value";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "No value";
    return DATETIME_FORMATTER.format(date);
  }

  function icon(name) {
    const base = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
    switch (name) {
      case "list":
        return `<svg ${base}><path d="M8 6h12"></path><path d="M8 12h12"></path><path d="M8 18h12"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>`;
      case "clipboard":
        return `<svg ${base}><rect x="8" y="3" width="8" height="4" rx="1"></rect><path d="M16 5h2a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2"></path><path d="M8 12h8"></path><path d="M8 16h6"></path></svg>`;
      case "grid":
        return `<svg ${base}><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg>`;
      case "people":
        return `<svg ${base}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`;
      case "gear":
        return `<svg ${base}><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.54V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.54 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.63 15a1.7 1.7 0 0 0-1.54-1H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.54-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.63 1.7 1.7 0 0 0 10 3.09V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.54 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.37 9c.36.61.76 1 1.54 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1z"></path></svg>`;
      case "book":
        return `<svg ${base}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>`;
      case "help":
        return `<svg ${base}><circle cx="12" cy="12" r="9"></circle><path d="M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4"></path><path d="M12 17h.01"></path></svg>`;
      case "bell":
        return `<svg ${base}><path d="M15 17h5l-1.4-1.4a2 2 0 0 1-.6-1.42V11a6 6 0 0 0-12 0v3.18a2 2 0 0 1-.59 1.41L4 17h5"></path><path d="M10 21a2 2 0 0 0 4 0"></path></svg>`;
      case "pencil":
        return `<svg ${base}><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>`;
      case "refresh":
        return `<svg ${base}><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6l3 2"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6l-3-2"></path></svg>`;
      case "filter":
        return `<svg ${base}><path d="M3 5h18"></path><path d="M6 12h12"></path><path d="M10 19h4"></path></svg>`;
      case "plus":
        return `<svg ${base}><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>`;
      case "link":
        return `<svg ${base}><path d="M10 13a5 5 0 0 0 7.07 0l1.41-1.41a5 5 0 0 0-7.07-7.07L10 6"></path><path d="M14 11a5 5 0 0 0-7.07 0L5.5 12.43a5 5 0 0 0 7.07 7.07L14 18"></path></svg>`;
      case "clock":
        return `<svg ${base}><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 3"></path></svg>`;
      case "chevron-down":
        return `<svg ${base}><path d="m6 9 6 6 6-6"></path></svg>`;
      case "x":
        return `<svg ${base}><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>`;
      case "search":
        return `<svg ${base}><circle cx="11" cy="11" r="7"></circle><path d="m21 21-4.3-4.3"></path></svg>`;
      case "bars":
        return `<svg viewBox="0 0 120 90" fill="none"><rect x="18" y="54" width="68" height="12" rx="2" fill="currentColor"></rect><rect x="18" y="31" width="68" height="12" rx="2" fill="currentColor"></rect><rect x="18" y="8" width="68" height="12" rx="2" fill="currentColor"></rect><text x="8" y="65" font-size="22" fill="currentColor" font-weight="700">3</text><text x="8" y="42" font-size="22" fill="currentColor" font-weight="700">2</text><text x="8" y="19" font-size="22" fill="currentColor" font-weight="700">1</text></svg>`;
      case "donut":
        return `<svg viewBox="0 0 120 120" fill="none"><circle cx="60" cy="60" r="28" stroke="currentColor" stroke-width="20" opacity="0.35"></circle><path d="M60 32a28 28 0 0 1 24.2 14" stroke="currentColor" stroke-width="20" stroke-linecap="round"></path><path d="M84.2 46A28 28 0 0 1 70 86" stroke="currentColor" stroke-width="20" stroke-linecap="round" opacity="0.8"></path></svg>`;
      case "network":
        return `<svg ${base}><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="6" r="3"></circle><circle cx="18" cy="18" r="3"></circle><circle cx="12" cy="12" r="3"></circle><path d="M8.7 10.6 15.3 7.4"></path><path d="m8.7 13.4 6.6 3.2"></path><path d="M13.6 10.6 16.4 7.4"></path><path d="m13.6 13.4 2.8 3.2"></path></svg>`;
      default:
        return "";
    }
  }

  function hydrateIcons(root = document) {
    root.querySelectorAll("[data-icon]").forEach((node) => {
      node.innerHTML = icon(node.dataset.icon);
    });
  }

  async function apiFetch(path, options = {}, auth = true) {
    const headers = new Headers(options.headers || {});
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    if (auth && state.token) headers.set("Authorization", `Bearer ${state.token}`);
    const response = await fetch(`${window.location.origin}/api/v1${path}`, { ...options, headers });
    if (!response.ok) throw new Error(await response.text() || `Request failed with status ${response.status}`);
    const type = response.headers.get("content-type") || "";
    return type.includes("application/json") ? response.json() : response.text();
  }

  async function authenticate() {
    const token = await apiFetch("/auth/token", {
      method: "POST",
      body: JSON.stringify({ username: "workspace.user", password: "cancer360" }),
    }, false);
    state.token = token.access_token;
    if (dom.avatar) dom.avatar.textContent = "DU";
  }

  async function fetchAllPTL(filters) {
    const items = [];
    const perPage = 200;
    let page = 1;
    let total = 0;
    let summary = null;
    for (;;) {
      const params = new URLSearchParams({ page: String(page), per_page: String(perPage), sort_by: "days" });
      if (filters.search) params.set("search", filters.search);
      if (filters.cancerSite) params.set("cancer_site", filters.cancerSite);
      if (filters.hospitalSite) params.set("hospital_site", filters.hospitalSite);
      if (filters.pathwayType) params.set("pathway_type", filters.pathwayType);
      const data = await apiFetch(`/ptl?${params.toString()}`);
      items.push(...(data.items || []));
      total = data.total || items.length;
      summary = data.summary || summary;
      if (!data.items?.length || items.length >= total) break;
      page += 1;
    }
    return { items, total: items.length || total, summary };
  }

  async function loadPtl() {
    state.ptl.loading = true;
    state.ptl.error = "";
    window.C360.renderApp();
    try {
      const data = await fetchAllPTL(state.ptl.filters);
      state.ptl.rows = data.items || [];
      state.ptl.summary = data.summary || null;
    } catch (error) {
      state.ptl.error = error.message || "Unable to load PTL.";
    } finally {
      state.ptl.loading = false;
      window.C360.renderApp();
    }
  }

  async function openPathwayDrawer(pathwayId) {
    if (!pathwayId) return;
    state.drawer.pathwayId = pathwayId;
    state.drawer.loading = true;
    state.drawer.error = "";
    state.drawer.data = null;
    state.drawer.activeSection = "pathway-details";
    state.drawer.selectedActionId = null;
    state.drawer.selectedReportKey = null;
    state.drawer.patientTab = "overview";
    window.C360.renderApp();
    try {
      state.drawer.data = await apiFetch(`/pathways/${pathwayId}`);
    } catch (error) {
      state.drawer.error = error.message || "Unable to load pathway.";
    } finally {
      state.drawer.loading = false;
      window.C360.renderApp();
    }
  }

  function closePathwayDrawer() {
    state.drawer.pathwayId = null;
    state.drawer.loading = false;
    state.drawer.error = "";
    state.drawer.data = null;
    window.C360.renderApp();
  }

  function syncPtlUrl() {
    if (state.route !== "ptl") return;
    const params = new URLSearchParams();
    if (state.ptl.filters.search) params.set("search", state.ptl.filters.search);
    if (state.ptl.filters.cancerSite) params.set("cancer_site", state.ptl.filters.cancerSite);
    if (state.ptl.filters.hospitalSite) params.set("hospital_site", state.ptl.filters.hospitalSite);
    if (state.ptl.filters.pathwayType) params.set("pathway_type", state.ptl.filters.pathwayType);
    if (state.ptl.filters.pathwayTag) params.set("pathway_tag", state.ptl.filters.pathwayTag);
    const query = params.toString();
    window.history.replaceState({}, "", query ? `/ptl?${query}` : "/ptl");
  }

  window.C360 = {
    API_BASE: `${window.location.origin}/api/v1`,
    PTL_LAST_UPDATED: "Sat, May 10, 2025, 7:46:50 PM",
    MODULES,
    state,
    dom,
    esc,
    formatDate,
    formatDateTime,
    icon,
    hydrateIcons,
    apiFetch,
    authenticate,
    loadPtl,
    openPathwayDrawer,
    closePathwayDrawer,
    syncPtlUrl,
  };
})();
