(() => {
  const { state, dom, hydrateIcons, authenticate, loadPtl, openPathwayDrawer, closePathwayDrawer, syncPtlUrl } = window.C360;
  const { renderLandingPage, renderPtlPage, renderFilterDrawer, renderPlaceholderPage } = window.C360.views;
  const { renderDrawer } = window.C360.drawer;
  const actionsUI = window.C360.actionsUI || {};
  const serviceUI = window.C360.serviceUI || {};
  const teamUI = window.C360.teamUI || {};

  function updateNavState() {
    document.querySelectorAll(".c360-nav-tab").forEach((link) => {
      const active =
        (state.route === "ptl" && link.dataset.route === "ptl") ||
        (state.route === "actions" && link.dataset.route === "actions") ||
        (state.route === "service" && link.dataset.route === "service") ||
        (state.route === "team" && link.dataset.route === "team");
      link.classList.toggle("active", active);
    });
  }

  function renderApp() {
    updateNavState();

    if (state.route === "landing") {
      dom.routeRoot.innerHTML = renderLandingPage();
    } else if (state.route === "ptl") {
      dom.routeRoot.innerHTML = renderPtlPage();
    } else if (state.route === "actions") {
      dom.routeRoot.innerHTML = actionsUI.renderActionsPage ? actionsUI.renderActionsPage() : renderPlaceholderPage("Cancer Actions", "Cancer Actions is loading.");
    } else if (state.route === "service") {
      dom.routeRoot.innerHTML = serviceUI.renderServiceOverviewPage ? serviceUI.renderServiceOverviewPage() : renderPlaceholderPage("Service Overview", "Service Overview is loading.");
    } else if (state.route === "team") {
      dom.routeRoot.innerHTML = teamUI.renderTeamPage ? teamUI.renderTeamPage() : renderPlaceholderPage("Team Overview", "Team Performance is loading.");
    }

    dom.filterRoot.innerHTML = state.route === "actions" && actionsUI.renderActionsFilterDrawer ? actionsUI.renderActionsFilterDrawer() : renderFilterDrawer();
    const ptlDrawer = state.route === "ptl" ? renderDrawer() : "";
    const teamDrawer = state.route === "team" && teamUI.renderTeamOverlay ? teamUI.renderTeamOverlay() : "";
    const actionDrawer = (state.route === "actions" || state.route === "team") && actionsUI.renderActionOverlay ? actionsUI.renderActionOverlay() : "";
    dom.drawerRoot.innerHTML = `${ptlDrawer}${teamDrawer}${actionDrawer}`;
    hydrateIcons(document);
  }

  async function init() {
    window.C360.renderApp = renderApp;
    renderApp();

    document.addEventListener("click", async (event) => {
      const actionNode = event.target.closest("[data-action]");
      if (!actionNode) return;
      if (!["actions", "team"].includes(state.route) && event.target.closest(".row-checkbox")) return;

      const { action, value, key, pathwayId, actionId } = actionNode.dataset;
      if (serviceUI.handleClick && await serviceUI.handleClick(event, actionNode.dataset)) {
        return;
      }
      if (teamUI.handleClick && await teamUI.handleClick(event, actionNode.dataset)) {
        return;
      }
      if (actionsUI.handleClick && await actionsUI.handleClick(event, actionNode.dataset)) {
        return;
      }
      switch (action) {
        case "open-filter":
          state.ptl.sidebarOpen = true;
          renderApp();
          break;
        case "close-filter":
          state.ptl.sidebarOpen = false;
          renderApp();
          break;
        case "reset-ptl-filters":
          state.ptl.filters = { search: "", cancerSite: "", hospitalSite: "", pathwayType: "", pathwayTag: "" };
          state.ptl.activeTab = "full";
          state.ptl.sidebarOpen = false;
          syncPtlUrl();
          loadPtl();
          break;
        case "toggle-filter-section":
          state.ptl.filterSections[key] = !state.ptl.filterSections[key];
          renderApp();
          break;
        case "set-ptl-tab":
          state.ptl.activeTab = value;
          renderApp();
          break;
        case "refresh-ptl":
          loadPtl();
          break;
        case "open-pathway":
          openPathwayDrawer(pathwayId);
          break;
        case "close-drawer":
          closePathwayDrawer();
          break;
        case "drawer-section":
          state.drawer.activeSection = value;
          state.drawer.selectedActionId = null;
          state.drawer.selectedReportKey = null;
          renderApp();
          break;
        case "select-drawer-action":
          state.drawer.selectedActionId = actionId;
          renderApp();
          break;
        case "clear-selected-action":
          state.drawer.selectedActionId = "__none__";
          renderApp();
          break;
        case "select-report":
          state.drawer.selectedReportKey = key;
          renderApp();
          break;
        case "clear-selected-report":
          state.drawer.selectedReportKey = "__none__";
          renderApp();
          break;
        case "set-patient-tab":
          state.drawer.patientTab = value;
          renderApp();
          break;
        default:
          break;
      }
    });

    document.addEventListener("submit", async (event) => {
      if (serviceUI.handleSubmit) {
        const handled = await serviceUI.handleSubmit(event);
        if (handled) return;
      }
      if (actionsUI.handleSubmit) {
        const handled = await actionsUI.handleSubmit(event);
        if (handled) return;
      }
      if (event.target.id === "landing-search-form") {
        event.preventDefault();
        const search = event.target.search.value.trim();
        window.location.href = search ? `/ptl?search=${encodeURIComponent(search)}` : "/ptl";
      }
      if (event.target.id === "ptl-search-form") {
        event.preventDefault();
        const searchInput = document.getElementById("ptl-search-input");
        state.ptl.filters.search = (searchInput?.value || "").trim();
        syncPtlUrl();
        loadPtl();
      }
    });

    document.addEventListener("change", async (event) => {
      if (serviceUI.handleChange) {
        const handled = await serviceUI.handleChange(event);
        if (handled) return;
      }
      if (teamUI.handleChange) {
        const handled = await teamUI.handleChange(event);
        if (handled) return;
      }
      if (actionsUI.handleChange) {
        const handled = await actionsUI.handleChange(event);
        if (handled) return;
      }
      if (event.target.id === "ptl-cancer-site") {
        state.ptl.filters.cancerSite = event.target.value;
        syncPtlUrl();
        loadPtl();
      }
      if (event.target.id === "ptl-hospital-site") {
        state.ptl.filters.hospitalSite = event.target.value;
        syncPtlUrl();
        loadPtl();
      }
      if (event.target.id === "ptl-pathway-tags") {
        state.ptl.filters.pathwayTag = event.target.value;
        syncPtlUrl();
        renderApp();
      }
      if (event.target.id === "ptl-pathway-type") {
        state.ptl.filters.pathwayType = event.target.value;
        syncPtlUrl();
        loadPtl();
      }
      if (event.target.id === "ptl-recent-days") {
        state.ptl.recentDays = Number(event.target.value || 2);
      }
    });

    document.addEventListener("focusout", async (event) => {
      if (serviceUI.handleBlur) {
        await serviceUI.handleBlur(event);
      }
    });

    try {
      await authenticate();
      if (state.route === "ptl") {
        await loadPtl();
      } else if (state.route === "actions" && actionsUI.initActionsRoute) {
        await actionsUI.initActionsRoute();
      } else if (state.route === "service" && serviceUI.initServiceRoute) {
        await serviceUI.initServiceRoute();
      } else if (state.route === "team" && teamUI.initTeamRoute) {
        await teamUI.initTeamRoute();
      } else {
        renderApp();
      }
    } catch (error) {
      dom.routeRoot.innerHTML = `<div class="view-shell"><div class="error-state">${window.C360.esc(error.message || "Unable to authorise demo user.")}</div></div>`;
    }
  }

  init();
})();
