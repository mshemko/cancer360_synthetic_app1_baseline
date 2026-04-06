const { useEffect, useMemo, useState } = React
const {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} = ReactRouterDOM
const {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  ScatterChart,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} = Recharts

const API_BASE = `${window.location.origin}/api/v1`
const DATE_FORMATTER = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  month: "short",
  day: "numeric",
  year: "numeric",
})
const DATETIME_FORMATTER = new Intl.DateTimeFormat("en-GB", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
})

const MODULES = [
  {
    key: "ptl",
    label: "Cancer PTL",
    route: "/ptl",
    subtitle: "Cancer PTL Management tool",
    color: "#7b61c4",
    icon: "list",
  },
  {
    key: "actions",
    label: "Cancer Actions",
    route: "/actions",
    subtitle: "Action Management Tool",
    color: "#5bb5d5",
    icon: "clipboard",
  },
  {
    key: "service",
    label: "Service Overview",
    route: "/service-overview",
    subtitle: "Bottleneck Analysis and Performance Dashboard",
    color: "#d4467a",
    icon: "grid",
  },
  {
    key: "team",
    label: "Team Overview",
    route: "/team-overview",
    subtitle: "Actions overview and team performance analysis",
    color: "#5b6dad",
    icon: "people",
  },
]

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return response.json()
}

async function fetchAllPTL(filters) {
  const perPage = 200
  let page = 1
  let items = []

  while (true) {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
      sort_by: filters.sortBy || "days",
    })
    if (filters.search) params.set("search", filters.search)
    if (filters.cancerSite) params.set("cancer_site", filters.cancerSite)
    if (filters.hospitalSite) params.set("hospital_site", filters.hospitalSite)
    if (filters.pathwayType) params.set("pathway_type", filters.pathwayType)

    const data = await apiGet(`/ptl?${params.toString()}`)
    items = items.concat(data.items || [])
    if (items.length >= (data.total || 0) || !data.items?.length) {
      return { ...data, items }
    }
    page += 1
  }
}

function formatDate(value) {
  if (!value) return "No value"
  try {
    return DATE_FORMATTER.format(new Date(value))
  } catch (error) {
    return "No value"
  }
}

function formatDateTime(value) {
  if (!value) return "No value"
  try {
    return DATETIME_FORMATTER.format(new Date(value))
  } catch (error) {
    return "No value"
  }
}

function classNames(...values) {
  return values.filter(Boolean).join(" ")
}

function LogoMark() {
  return (
    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-brand">
      <div className="relative h-4 w-4 rounded-full border-[3px] border-brand">
        <div className="absolute right-[-4px] top-[5px] h-[3px] w-[7px] rounded-full bg-brand" />
      </div>
    </div>
  )
}

function Icon({ name, className = "h-4 w-4" }) {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
  }

  switch (name) {
    case "list":
      return <svg {...common}><path d="M8 6h12" /><path d="M8 12h12" /><path d="M8 18h12" /><path d="M3 6h.01" /><path d="M3 12h.01" /><path d="M3 18h.01" /></svg>
    case "clipboard":
      return <svg {...common}><rect x="8" y="3" width="8" height="4" rx="1" /><path d="M16 5h2a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2" /><path d="M8 12h8" /><path d="M8 16h6" /></svg>
    case "grid":
      return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
    case "people":
      return <svg {...common}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
    case "gear":
      return <svg {...common}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.54V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.54 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.63 15a1.7 1.7 0 0 0-1.54-1H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.54-1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.63 1.7 1.7 0 0 0 10 3.09V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.54 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.37 9c.36.61.76 1 1.54 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1z" /></svg>
    case "book":
      return <svg {...common}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>
    case "help":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4" /><path d="M12 17h.01" /></svg>
    case "bell":
      return <svg {...common}><path d="M15 17h5l-1.4-1.4a2 2 0 0 1-.6-1.42V11a6 6 0 0 0-12 0v3.18a2 2 0 0 1-.59 1.41L4 17h5" /><path d="M10 21a2 2 0 0 0 4 0" /></svg>
    case "pencil":
      return <svg {...common}><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>
    case "refresh":
      return <svg {...common}><path d="M21 2v6h-6" /><path d="M3 12a9 9 0 0 1 15-6l3 2" /><path d="M3 22v-6h6" /><path d="M21 12a9 9 0 0 1-15 6l-3-2" /></svg>
    case "filter":
      return <svg {...common}><path d="M3 5h18" /><path d="M6 12h12" /><path d="M10 19h4" /></svg>
    case "plus":
      return <svg {...common}><path d="M12 5v14" /><path d="M5 12h14" /></svg>
    case "link":
      return <svg {...common}><path d="M10 13a5 5 0 0 0 7.07 0l1.41-1.41a5 5 0 0 0-7.07-7.07L10 6" /><path d="M14 11a5 5 0 0 0-7.07 0L5.5 12.43a5 5 0 0 0 7.07 7.07L14 18" /></svg>
    case "clock":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></svg>
    case "chevron-down":
      return <svg {...common}><path d="m6 9 6 6 6-6" /></svg>
    case "x":
      return <svg {...common}><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
    case "search":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
    case "bars":
      return <svg viewBox="0 0 120 90" className={className}><rect x="16" y="52" width="20" height="22" rx="5" fill="currentColor" /><rect x="50" y="36" width="20" height="38" rx="5" fill="currentColor" /><rect x="84" y="18" width="20" height="56" rx="5" fill="currentColor" /><text x="26" y="47" fill="currentColor" fontSize="12" textAnchor="middle">1</text><text x="60" y="31" fill="currentColor" fontSize="12" textAnchor="middle">2</text><text x="94" y="13" fill="currentColor" fontSize="12" textAnchor="middle">3</text></svg>
    case "donut":
      return <svg viewBox="0 0 100 100" className={className}><circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="18" fill="none" opacity="0.35" /><path d="M50 20a30 30 0 0 1 30 30" stroke="currentColor" strokeWidth="18" fill="none" strokeLinecap="round" /></svg>
    case "network":
      return <svg {...common}><circle cx="6" cy="12" r="3" /><circle cx="18" cy="6" r="3" /><circle cx="18" cy="18" r="3" /><path d="M8.7 10.6 15.3 7.4" /><path d="m8.7 13.4 6.6 3.2" /></svg>
    default:
      return <span className={className} />
  }
}

function LoadingCard({ label = "Loading…" }) {
  return <div className="surface flex h-40 items-center justify-center text-sm text-slate-500">{label}</div>
}

function ErrorCard({ message, retry }) {
  return (
    <div className="surface flex flex-col items-start gap-3 p-6">
      <div className="text-sm font-semibold text-red-700">Something went wrong</div>
      <div className="text-sm text-slate-600">{message}</div>
      {retry ? (
        <button onClick={retry} className="rounded-xl bg-brand px-4 py-2 text-sm font-medium text-white">
          Try again
        </button>
      ) : null}
    </div>
  )
}

function GlobalNav() {
  const location = useLocation()
  return (
    <header className="sticky top-0 z-40 flex h-12 items-center justify-between bg-brand px-4 shadow-lg">
      <div className="flex items-center gap-3">
        <NavLink to="/" className="flex items-center gap-2 rounded-xl px-2 py-1 text-white no-underline hover:bg-white/10">
          <LogoMark />
          <span className="text-sm font-semibold">Cancer 360</span>
          <Icon name="chevron-down" className="h-4 w-4 text-white/70" />
        </NavLink>
        <nav className="flex items-center gap-1">
          {MODULES.map((module) => {
            const active = location.pathname === module.route
            return (
              <NavLink
                key={module.key}
                to={module.route}
                className={classNames("nav-tab no-underline", active && "nav-tab-active")}
              >
                <Icon name={module.icon === "bars" ? "list" : module.icon} className="h-4 w-4" />
                {module.label}
              </NavLink>
            )
          })}
          <button className="ml-1 rounded-xl border border-white/20 p-2 text-white/80 hover:bg-white/10">
            <Icon name="plus" className="h-4 w-4" />
          </button>
        </nav>
      </div>
      <div className="flex items-center gap-2">
        <button className="hidden items-center gap-2 rounded-full border border-sky-200/70 px-3 py-1 text-xs font-semibold text-white md:flex">
          <Icon name="pencil" className="h-3.5 w-3.5" />
          Edit
        </button>
        <button className="rounded-full p-2 text-white/80 hover:bg-white/10"><Icon name="help" className="h-4 w-4" /></button>
        <button className="rounded-full p-2 text-white/80 hover:bg-white/10"><Icon name="bell" className="h-4 w-4" /></button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 text-xs font-semibold text-white">DU</div>
      </div>
    </header>
  )
}

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-page">
      <GlobalNav />
      {children}
    </div>
  )
}

function LandingPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [metrics, setMetrics] = useState(null)
  const [integration, setIntegration] = useState(null)

  useEffect(() => {
    Promise.all([apiGet("/dashboard/performance"), apiGet("/integration/status")])
      .then(([dashboard, integrationStatus]) => {
        setMetrics(dashboard)
        setIntegration(integrationStatus)
      })
      .catch(() => {
        setMetrics(null)
        setIntegration(null)
      })
  }, [])

  const cancerTypeChart = useMemo(() => {
    const rows = metrics?.by_cancer_type || []
    return rows.slice(0, 5).map((row) => ({ name: row.label || row.code, count: row.count }))
  }, [metrics])

  function submitSearch(event) {
    event.preventDefault()
    navigate(search ? `/ptl?search=${encodeURIComponent(search)}` : "/ptl")
  }

  return (
    <main className="mx-auto flex max-w-[1500px] gap-8 px-6 py-8">
      <section className="min-w-0 flex-1">
        <div className="surface mx-auto mb-6 flex max-w-xl flex-col items-center gap-4 px-8 py-8 text-center">
          <div className="rounded-full bg-brand px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-white">NHS Federated Data Platform</div>
          <div>
            <h1 className="m-0 text-3xl font-semibold text-slate-900">Cancer 360</h1>
            <p className="mt-2 text-sm text-slate-500">Synthetic patient tracking, pathway management, and service insights on one platform.</p>
          </div>
          <form onSubmit={submitSearch} className="flex w-full items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <select className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none">
              <option>All</option>
            </select>
            <Icon name="search" className="h-4 w-4 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search object types and properties..."
              className="min-w-0 flex-1 border-0 bg-transparent text-sm outline-none"
            />
            <button type="button" className="rounded-full border border-slate-200 p-2 text-slate-500">
              <Icon name="help" className="h-4 w-4" />
            </button>
          </form>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {MODULES.map((module) => (
            <button
              key={module.key}
              onClick={() => navigate(module.route)}
              className="surface overflow-hidden border border-slate-100 text-left transition hover:-translate-y-0.5 hover:shadow-2xl"
            >
              <div className="flex h-44 items-center justify-center" style={{ backgroundColor: module.color, color: "#fff" }}>
                <Icon name={module.icon === "list" ? "bars" : module.icon} className="h-20 w-20" />
              </div>
              <div className="space-y-2 px-6 py-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Icon name={module.icon === "list" ? "list" : module.icon} className="h-4 w-4 text-slate-500" />
                  {module.label}
                </div>
                <div className="text-sm text-slate-500">{module.subtitle}</div>
              </div>
            </button>
          ))}
        </div>

        <div className="surface mt-6 p-6">
          <div className="mb-4">
            <h2 className="m-0 text-lg font-semibold text-slate-900">Live platform snapshot</h2>
            <p className="mt-1 text-sm text-slate-500">Current pathway mix from the existing Cancer 360 API.</p>
          </div>
          {cancerTypeChart.length ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cancerTypeChart} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#7b61c4" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">Dashboard metrics will appear here when the API is available.</div>
          )}
        </div>
      </section>

      <aside className="hidden w-80 shrink-0 xl:block">
        <div className="surface p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Icon name="gear" className="h-4 w-4 text-slate-500" />
            Cancer Settings
          </div>
          <div className="text-sm text-slate-500">Configure cancer module</div>
        </div>
        <div className="surface mt-4 p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Icon name="book" className="h-4 w-4 text-slate-500" />
            User Guides
          </div>
          <div className="text-sm text-slate-500">User guides and documentation for Cancer 360</div>
        </div>
        <div className="surface mt-4 p-5">
          <div className="text-sm font-semibold text-slate-900">Integration health</div>
          <div className="mt-4 space-y-3">
            {(integration?.source_status || []).slice(0, 4).map((source) => (
              <div key={source.source_system} className="rounded-2xl bg-slate-50 p-3">
                <div className="flex items-center justify-between text-sm font-medium text-slate-800">
                  <span>{source.source_system}</span>
                  <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-700">{source.success_count} ok</span>
                </div>
                <div className="mt-1 text-xs text-slate-500">{source.error_count} errors recorded</div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </main>
  )
}

function PlaceholderPage({ title, subtitle }) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="surface p-8">
        <h1 className="m-0 text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
        <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
          This route is ready for the next screen build. The global navigation bar and reusable pathway drawer are already in place for future pages.
        </div>
      </div>
    </main>
  )
}

function FilterSidebar({ open, onClose, stats, recentDays, setRecentDays }) {
  const sections = [
    { label: "PATIENT", detail: `[CDM] Patient ${stats.total || 0}`, icon: "people" },
    { label: "CANCER PATHWAY", detail: `[Cancer 360] Cancer Pathway ${stats.total || 0}`, icon: "list" },
    { label: "PATHWAY TAGS", detail: `[Cancer 360] Tagging Rule ${stats.tagCount || 0}`, icon: "grid" },
    { label: "WATCHLIST", detail: `[Cancer 360] Cancer Watchlist ${stats.watchlist || 0}`, icon: "grid" },
    { label: "TRACKING COMMENTS", detail: `[Cancer 360] Tracking Comment ${stats.trackingCount || 0}`, icon: "clipboard" },
    { label: "CANCER ACTIONS", detail: `[Cancer 360] Cancer PTL Action ${stats.actionCount || 0}`, icon: "clipboard" },
    { label: "OUTPATIENT APPOINTMENTS", detail: `[Sho-Like][Cancer 360] Outpatient Appointment ${stats.outpatientCount || 0}`, icon: "list" },
    { label: "INPATIENT PROCEDURES", detail: `[Sho-Like][Cancer 360] Inpatient Procedure ${stats.inpatientCount || 0}`, icon: "list" },
    { label: "RADIOLOGY EXAMS", detail: `[Cancer 360] Radiology ${stats.radiologyCount || 0}`, icon: "grid" },
    { label: "HISTOLOGY", detail: `[Cancer 360] Histology ${stats.histologyCount || 0}`, icon: "grid" },
    { label: "TEST RESULTS", detail: `[Sho-Like][Cancer 360] Test Result ${stats.testCount || 0}`, icon: "grid" },
    { label: "IPT", detail: `[Cancer 360] ITR ${stats.iptCount || 0}`, icon: "grid" },
  ]

  return (
    <>
      {open ? <button onClick={onClose} className="fixed inset-0 z-30 bg-slate-900/20" /> : null}
      <aside className={classNames("fixed inset-y-12 left-0 z-40 w-[360px] transform overflow-y-auto border-r border-slate-200 bg-white p-5 shadow-2xl transition duration-300", open ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-900">Filters &amp; Config</div>
          <button className="rounded-full border border-red-200 px-3 py-1 text-xs font-medium text-red-600">Reset Filters</button>
        </div>
        <div className="mt-6 space-y-5 text-sm">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Excluded users for recent action updates</div>
            <input className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" placeholder="Updates from selected users won't be counted" />
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Flag recent action updates for the last N days</div>
            <div className="flex items-center gap-2">
              <input type="number" min="1" value={recentDays} onChange={(event) => setRecentDays(event.target.value)} className="w-24 rounded-xl border border-slate-200 px-3 py-2 outline-none" />
              <button className="rounded-xl border border-slate-200 p-2 text-slate-500"><Icon name="refresh" className="h-4 w-4" /></button>
            </div>
          </div>
          <div>
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Pathway is open</div>
            <div className="space-y-3">
              <label className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <input type="checkbox" />
                <div className="flex-1">
                  <div className="flex items-center justify-between text-sm text-slate-700"><span>No</span><span>{stats.closedCount || 0}</span></div>
                  <div className="mt-2 h-2 rounded-full bg-sky-100"><div className="h-2 rounded-full bg-sky-400" style={{ width: `${Math.min(100, (stats.closedCount || 0) * 5)}%` }} /></div>
                </div>
              </label>
              <label className="flex items-center gap-3 rounded-xl bg-slate-50 p-3">
                <input type="checkbox" checked readOnly />
                <div className="flex-1">
                  <div className="flex items-center justify-between text-sm text-slate-700"><span>Yes</span><span>{stats.openCount || 0}</span></div>
                  <div className="mt-2 h-2 rounded-full bg-sky-100"><div className="h-2 rounded-full bg-sky-500" style={{ width: `${Math.min(100, (stats.openCount || 0) * 5)}%` }} /></div>
                </div>
              </label>
            </div>
          </div>
          {sections.map((section) => (
            <div key={section.label} className="rounded-2xl border border-slate-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <Icon name={section.icon} className="h-4 w-4 text-brand" />
                  {section.label}
                </div>
                <Icon name="chevron-down" className="h-4 w-4 text-slate-400" />
              </div>
              <div className="mt-2 text-xs text-slate-500">{section.detail}</div>
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}

function PTLPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search])
  const [rows, setRows] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [filterSidebarOpen, setFilterSidebarOpen] = useState(false)
  const [selectedPathwayId, setSelectedPathwayId] = useState(null)
  const [recentDays, setRecentDays] = useState(2)
  const [filters, setFilters] = useState({
    search: searchParams.get("search") || "",
    cancerSite: "",
    hospitalSite: "",
    pathwayType: "",
    sortBy: "days",
  })
  const [activeTab, setActiveTab] = useState("full")

  function loadData(nextFilters = filters) {
    setLoading(true)
    setError("")
    fetchAllPTL(nextFilters)
      .then((data) => {
        setRows(data.items || [])
        setSummary(data.summary || null)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || "Unable to load PTL data")
        setLoading(false)
      })
  }

  useEffect(() => {
    loadData(filters)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams()
    if (filters.search) params.set("search", filters.search)
    navigate({ pathname: "/ptl", search: params.toString() ? `?${params.toString()}` : "" }, { replace: true })
  }, [filters.search])

  const cancerSiteOptions = useMemo(() => Array.from(new Set(rows.map((row) => row.cancer_site).filter(Boolean))).sort(), [rows])
  const hospitalSiteOptions = useMemo(() => Array.from(new Set(rows.map((row) => row.hospital_site).filter(Boolean))).sort(), [rows])
  const pathwayTypeOptions = ["28 Day", "31 Day", "62 Day"]

  const tabCounts = useMemo(() => ({
    full: rows.length,
    zeroTwentyEight: rows.filter((row) => (row.days_on_pathway || 0) <= 28).length,
    twentyNineSixtyTwo: rows.filter((row) => {
      const value = row.days_on_pathway || 0
      return value >= 29 && value <= 62
    }).length,
    sixtyThreePlus: rows.filter((row) => (row.days_on_pathway || 0) >= 63).length,
    oneHundredFivePlus: rows.filter((row) => (row.days_on_pathway || 0) >= 105).length,
    watchlist: rows.filter((row) => row.watchlist_reason).length,
  }), [rows])

  const filteredRows = useMemo(() => {
    let nextRows = [...rows]
    if (activeTab === "zeroTwentyEight") nextRows = nextRows.filter((row) => (row.days_on_pathway || 0) <= 28)
    if (activeTab === "twentyNineSixtyTwo") nextRows = nextRows.filter((row) => (row.days_on_pathway || 0) >= 29 && (row.days_on_pathway || 0) <= 62)
    if (activeTab === "sixtyThreePlus") nextRows = nextRows.filter((row) => (row.days_on_pathway || 0) >= 63)
    if (activeTab === "oneHundredFivePlus") nextRows = nextRows.filter((row) => (row.days_on_pathway || 0) >= 105)
    if (activeTab === "watchlist") nextRows = nextRows.filter((row) => row.watchlist_reason)
    return nextRows
  }, [activeTab, rows])

  const sidebarStats = useMemo(() => ({
    total: rows.length,
    openCount: rows.filter((row) => row.pathway_status !== "completed").length,
    closedCount: rows.filter((row) => row.pathway_status === "completed").length,
    watchlist: rows.filter((row) => row.watchlist_reason).length,
    actionCount: rows.reduce((sum, row) => sum + (row.open_action_count || 0), 0),
    outpatientCount: rows.filter((row) => row.first_outpatient_attended_date || row.next_outpatient_attended_date).length,
    inpatientCount: rows.filter((row) => row.latest_inpatient_encounter_tci_date).length,
    radiologyCount: rows.filter((row) => row.latest_radiology_attended_date).length,
    histologyCount: rows.filter((row) => row.latest_histology_attended_date).length,
    testCount: rows.filter((row) => row.latest_histology_attended_date || row.latest_radiology_attended_date).length,
    iptCount: rows.filter((row) => row.latest_ipt_date).length,
    trackingCount: rows.filter((row) => row.latest_tracking_comment).length,
    tagCount: Array.from(new Set(rows.flatMap((row) => row.tags || []))).length,
  }), [rows])

  const ptlTabs = [
    { key: "full", label: "Full PTL", count: tabCounts.full },
    { key: "zeroTwentyEight", label: "0-28 Days", count: tabCounts.zeroTwentyEight },
    { key: "twentyNineSixtyTwo", label: "29-62 Days", count: tabCounts.twentyNineSixtyTwo },
    { key: "sixtyThreePlus", label: "63+ Days", count: tabCounts.sixtyThreePlus },
    { key: "oneHundredFivePlus", label: "105+ Days", count: tabCounts.oneHundredFivePlus },
    { key: "watchlist", label: "Watchlist", count: tabCounts.watchlist },
  ]

  function refreshData() {
    loadData(filters)
  }

  function updateFilter(name, value) {
    const nextFilters = { ...filters, [name]: value }
    setFilters(nextFilters)
    loadData(nextFilters)
  }

  return (
    <main className="relative">
      <FilterSidebar open={filterSidebarOpen} onClose={() => setFilterSidebarOpen(false)} stats={sidebarStats} recentDays={recentDays} setRecentDays={setRecentDays} />
      <div className="mx-auto max-w-[1600px] px-6 py-6">
        <div className="surface mb-4 p-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="flex items-start gap-3">
              <button onClick={() => setFilterSidebarOpen(true)} className="rounded-xl border border-slate-200 p-2 text-slate-600 hover:bg-slate-50">
                <Icon name="filter" className="h-4 w-4" />
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <Icon name="list" className="h-4 w-4 text-brand" />
                  <h1 className="m-0 text-xl font-semibold text-slate-900">Cancer PTL</h1>
                </div>
                <button className="mt-2 flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  Saved module states
                  <Icon name="chevron-down" className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
              <button className="rounded-xl border border-slate-200 p-2 text-slate-500"><Icon name="gear" className="h-4 w-4" /></button>
              <LabeledSelect label="Pathway Tags" value="" onChange={() => {}} options={["Search..."]} />
              <LabeledSelect label="Cancer Sites" value={filters.cancerSite} onChange={(value) => updateFilter("cancerSite", value)} options={cancerSiteOptions} />
              <LabeledSelect label="Hospital Sites" value={filters.hospitalSite} onChange={(value) => updateFilter("hospitalSite", value)} options={hospitalSiteOptions} />
            </div>
          </div>
        </div>

        <div className="surface overflow-hidden">
          <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2">
              {ptlTabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={classNames("flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium", activeTab === tab.key ? "bg-brand text-white" : "bg-slate-100 text-slate-700")}
                >
                  {activeTab === tab.key ? <Icon name="filter" className="h-4 w-4" /> : null}
                  {tab.label}
                  <span className={classNames("rounded-full px-2 py-0.5 text-xs", activeTab === tab.key ? "bg-white/20 text-white" : "bg-white text-slate-600")}>{tab.count}</span>
                </button>
              ))}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Icon name="clock" className="h-4 w-4" />
                PTL Last Updated: {formatDateTime(new Date().toISOString())}
              </div>
              <button onClick={refreshData} className="rounded-xl border border-slate-200 p-2 text-slate-600">
                <Icon name="refresh" className="h-4 w-4" />
              </button>
              <button className="flex items-center gap-2 rounded-xl bg-success px-4 py-2 text-sm font-semibold text-white">
                <Icon name="plus" className="h-4 w-4" />
                Create Action
                <Icon name="chevron-down" className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="border-b border-slate-200 px-5 py-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="text-sm text-slate-600">
                {summary ? `${summary.total} pathways available, ${summary.breached} breached, ${summary.high_risk} high risk.` : "Loading summary…"}
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative">
                  <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    value={filters.search}
                    onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") refreshData()
                    }}
                    placeholder="Search by patient, NHS, or MRN"
                    className="w-80 rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm outline-none"
                  />
                </div>
                <LabeledSelect label="Pathway Type" compact value={filters.pathwayType} onChange={(value) => updateFilter("pathwayType", value)} options={pathwayTypeOptions} />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="p-5"><LoadingCard label="Loading PTL…" /></div>
          ) : error ? (
            <div className="p-5"><ErrorCard message={error} retry={refreshData} /></div>
          ) : (
            <PTLTable rows={filteredRows} onOpenDrawer={setSelectedPathwayId} />
          )}
        </div>
      </div>

      <PathwayDrawer pathwayId={selectedPathwayId} onClose={() => setSelectedPathwayId(null)} />
    </main>
  )
}

function LabeledSelect({ label, value, onChange, options, compact = false }) {
  return (
    <label className={classNames("flex items-center gap-2 text-sm text-slate-600", compact ? "" : "rounded-xl border border-slate-200 bg-white px-3 py-2")}>
      <span className="whitespace-nowrap text-xs font-medium uppercase tracking-wide text-slate-500">{label}:</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="min-w-[140px] border-0 bg-transparent text-sm outline-none">
        <option value="">Search...</option>
        {options.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </label>
  )
}

function PTLTable({ rows, onOpenDrawer }) {
  const columns = [
    { key: "select", label: "", width: 52, sticky: 0 },
    { key: "days_on_pathway", label: "Pathway Day", width: 110, sticky: 52 },
    { key: "patient_name", label: "Full Name", width: 220, sticky: 162 },
    { key: "nhs_number", label: "NHS Number", width: 140 },
    { key: "hospital_number", label: "MRN", width: 140 },
    { key: "age", label: "Age", width: 90 },
    { key: "cancer_site", label: "Cancer Site", width: 150 },
    { key: "cancer_sub_site", label: "Cancer Sub Site", width: 150 },
    { key: "hospital_site", label: "Hospital Site", width: 120 },
    { key: "open_action_count", label: "# Open Actions", width: 120 },
    { key: "latest_action", label: "Latest Action", width: 220 },
    { key: "recent_action_update", label: "Recent Action Update", width: 150 },
    { key: "latest_tracking_comment", label: "Latest Tracking Comment", width: 320 },
    { key: "pathway_status_display", label: "Pathway Status", width: 140 },
    { key: "breach_date_28", label: "28 Day Breach Date", width: 170 },
    { key: "breach_date_31", label: "31 Day Breach Date", width: 170 },
    { key: "breach_date_62", label: "62 Day Breach Date", width: 170 },
    { key: "first_outpatient_attended_date", label: "First Op Appt Attended Date", width: 180 },
    { key: "next_outpatient_attended_date", label: "Next Op Appt Attended Date", width: 180 },
    { key: "latest_histology_attended_date", label: "Latest Histology Attended Date", width: 180 },
    { key: "latest_radiology_attended_date", label: "Latest Radiology Attended Date", width: 180 },
    { key: "latest_inpatient_encounter_tci_date", label: "Latest Inpatient Encounter TCI Date", width: 220 },
    { key: "latest_mdt_status", label: "Latest MDT Status", width: 150 },
    { key: "latest_ipt_date", label: "Latest IPT", width: 140 },
    { key: "tags", label: "Tags", width: 340 },
    { key: "watchlist_reason", label: "Watchlist Reason", width: 220 },
  ]

  function renderCell(row, column) {
    if (column.key === "select") return <input type="checkbox" onClick={(event) => event.stopPropagation()} />
    if (column.key === "days_on_pathway") {
      return <span className={classNames("font-semibold", (row.days_on_pathway || 0) >= 105 ? "text-red-700" : (row.days_on_pathway || 0) >= 63 ? "text-amber-700" : "text-slate-800")}>{row.days_on_pathway ?? "No value"}</span>
    }
    if (column.key === "recent_action_update") return <span className={row.recent_action_update ? "font-medium text-emerald-600" : "text-slate-400"}>{row.recent_action_update ? "Yes" : "No"}</span>
    if (column.key === "pathway_status_display") {
      const label = row.pathway_status === "completed" || row.pathway_status === "active_monitoring" ? "Benign" : "Suspected"
      return <StatusPill tone={label === "Benign" ? "neutral" : "warning"}>{label}</StatusPill>
    }
    if (["breach_date_28", "breach_date_31", "breach_date_62"].includes(column.key)) return <DateCell value={row[column.key]} warn={row[column.key] && new Date(row[column.key]) < new Date()} />
    if (["first_outpatient_attended_date", "next_outpatient_attended_date", "latest_histology_attended_date", "latest_radiology_attended_date", "latest_inpatient_encounter_tci_date"].includes(column.key)) return <NullableDate value={row[column.key]} />
    if (column.key === "latest_ipt_date") {
      return row.latest_ipt_date ? (
        <div className="inline-flex items-center gap-2 rounded-full bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700">
          <span className="h-2 w-2 rounded-sm bg-rose-600" />
          {row.latest_ipt_date}
        </div>
      ) : <span className="italic text-slate-400">No value</span>
    }
    if (column.key === "tags") return row.tags?.length ? row.tags.join(" | ") : <span className="italic text-slate-400">No value</span>
    if (column.key === "latest_tracking_comment") return <div className="max-w-[300px] truncate">{row.latest_tracking_comment || <span className="italic text-slate-400">No value</span>}</div>
    const value = row[column.key]
    return value ?? <span className="italic text-slate-400">No value</span>
  }

  return (
    <div className="scrollbar-thin overflow-auto">
      <table className="min-w-[3200px] border-separate border-spacing-0">
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th key={column.key} className="table-head sticky top-0 z-20 whitespace-nowrap underline decoration-slate-300 underline-offset-4" style={column.sticky !== undefined ? { left: column.sticky, minWidth: column.width, width: column.width, zIndex: 25 + (10 - index) } : { minWidth: column.width, width: column.width }}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row.pathway_id} onClick={() => onOpenDrawer(row.pathway_id)} className={classNames("cursor-pointer", rowIndex % 2 === 0 ? "bg-white" : "bg-slate-50/70")}>
              {columns.map((column, index) => (
                <td key={column.key} className="table-cell" style={column.sticky !== undefined ? { left: column.sticky, position: "sticky", background: rowIndex % 2 === 0 ? "#fff" : "#f8fafc", zIndex: 15 + (10 - index), minWidth: column.width, width: column.width } : { minWidth: column.width, width: column.width }}>
                  {renderCell(row, column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusPill({ children, tone = "neutral" }) {
  const tones = {
    neutral: "bg-slate-200 text-slate-700",
    warning: "bg-amber-100 text-amber-700",
    success: "bg-emerald-100 text-emerald-700",
  }
  return <span className={classNames("inline-flex rounded-full px-3 py-1 text-xs font-medium", tones[tone] || tones.neutral)}>{children}</span>
}

function DateCell({ value, warn }) {
  if (!value) return <span className="italic text-slate-400">No value</span>
  return <span className={classNames("inline-flex rounded-xl border px-3 py-1 text-xs font-medium", warn ? "border-amber-300 bg-amber-50 text-amber-700" : "border-slate-200 bg-white text-slate-700")}>{formatDate(value)}</span>
}

function NullableDate({ value }) {
  return value ? <span>{formatDate(value)}</span> : <span className="italic text-slate-400">No value</span>
}

function PathwayDrawer({ pathwayId, onClose, embedded = false }) {
  const [data, setData] = useState(null)
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [activeSection, setActiveSection] = useState("pathway-details")
  const [selectedAction, setSelectedAction] = useState(null)
  const [selectedReport, setSelectedReport] = useState(null)
  const [patientTab, setPatientTab] = useState("overview")

  useEffect(() => {
    if (!pathwayId) return
    setLoading(true)
    setError("")
    setSelectedAction(null)
    setSelectedReport(null)
    Promise.all([apiGet(`/pathways/${pathwayId}`), apiGet(`/actions?pathway_id=${pathwayId}`)])
      .then(([drawer, actionRows]) => {
        setData(drawer)
        setActions(actionRows || [])
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || "Unable to load pathway")
        setLoading(false)
      })
  }, [pathwayId])

  if (!pathwayId) return null

  const sectionCounts = Object.fromEntries((data?.section_counts || []).map((item) => [item.key, item.count]))

  return (
    <>
      {!embedded ? <button onClick={onClose} className="fixed inset-0 z-40 bg-slate-900/30" /> : null}
      <aside className={classNames(
        embedded
          ? "flex max-h-[960px] flex-col overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm"
          : "fixed inset-y-12 right-0 z-50 flex w-[min(65vw,1080px)] max-w-full flex-col border-l border-slate-200 bg-white shadow-2xl"
      )}>
        {loading ? <div className="p-6"><LoadingCard label="Loading pathway drawer…" /></div> : null}
        {error ? <div className="p-6"><ErrorCard message={error} retry={() => {}} /></div> : null}
        {!loading && !error && data ? (
          <>
            <div className="flex items-center gap-3 bg-brand px-5 py-4 text-white">
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold">{data.pathway.patient_name} | MRN: {data.pathway.hospital_number || "No value"} | {data.pathway.cancer_site || "Cancer pathway"} | Day {data.pathway.days_on_pathway || 0}</div>
              </div>
              <button className="flex items-center gap-2 rounded-xl bg-success px-3 py-2 text-sm font-semibold text-white"><Icon name="link" className="h-4 w-4" />External Links<Icon name="chevron-down" className="h-4 w-4" /></button>
              <div className="rounded-full bg-white/15 px-3 py-1 text-xs">PTL Last Updated: {formatDateTime(data.last_updated)}</div>
              <button className="flex items-center gap-2 rounded-xl bg-success px-3 py-2 text-sm font-semibold text-white">Create Action<Icon name="chevron-down" className="h-4 w-4" /></button>
              {!embedded ? <button onClick={onClose} className="rounded-full p-2 hover:bg-white/10"><Icon name="x" className="h-4 w-4" /></button> : null}
            </div>
            <div className="flex min-h-0 flex-1 overflow-hidden">
              <div className="w-64 shrink-0 border-r border-slate-200 bg-slate-50 p-3">
                {[
                  ["pathway-details", "Pathway Details"],
                  ["actions", "Actions"],
                  ["outpatient", "Outpatient Appointments"],
                  ["inpatient", "Inpatient Procedures"],
                  ["histology", "Histology"],
                  ["radiology", "Radiology"],
                  ["mdt", "MDT Notes"],
                  ["tests", "Test Results"],
                  ["ipt", "IPT"],
                  ["tracking", "Tracking Comments"],
                  ["patient", "Patient"],
                ].map(([key, label]) => (
                  <button key={key} onClick={() => { setActiveSection(key); setSelectedAction(null); setSelectedReport(null) }} className={classNames("mb-2 flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm", activeSection === key ? "bg-indigo-100 text-brand" : "text-slate-700 hover:bg-white")}>
                    <span>{label}</span>
                    <span className={classNames("inline-flex min-w-[26px] items-center justify-center rounded-full px-2 py-0.5 text-xs font-semibold", (sectionCounts[key] || 0) > 0 ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-600")}>
                      {key === "pathway-details" || key === "patient" ? "" : sectionCounts[key] || 0}
                    </span>
                  </button>
                ))}
              </div>
              <div className="min-w-0 flex-1 overflow-y-auto bg-white p-5">
                {activeSection === "pathway-details" ? <PathwayDetailsSection data={data} /> : null}
                {activeSection === "actions" ? <ActionsSection data={data.actions} externalActions={actions} selectedAction={selectedAction} setSelectedAction={setSelectedAction} /> : null}
                {activeSection === "outpatient" ? <SimpleTableSection title="Outpatient Appointments" rows={data.outpatient_appointments} columns={[["name", "Appointment Name"], ["status", "Appointment Status"], ["ordered_date", "Ordered Date"], ["scheduled_date", "Scheduled Date"], ["attended_date", "Attended Date"]]} /> : null}
                {activeSection === "inpatient" ? <SimpleTableSection title="Inpatient Procedures" rows={data.inpatient_procedures} columns={[["name", "Procedure Name"], ["status", "Encounter Status"], ["ordered_date", "Ordered Date"], ["scheduled_date", "Scheduled Date"], ["attended_date", "Attended Date"]]} /> : null}
                {activeSection === "histology" ? <ReportSection title="Histology" rows={data.histology} selectedReport={selectedReport} setSelectedReport={setSelectedReport} /> : null}
                {activeSection === "radiology" ? <ReportSection title="Radiology" rows={data.radiology} selectedReport={selectedReport} setSelectedReport={setSelectedReport} /> : null}
                {activeSection === "mdt" ? <MDTSection meetings={data.mdt_notes} /> : null}
                {activeSection === "tests" ? <TestResultsSection rows={data.test_results} /> : null}
                {activeSection === "ipt" ? <SimpleTableSection title="IPT" rows={data.ipt} columns={[["reason_for_ipt", "Reason for IPT"], ["sent_or_received", "Sent or Received"], ["ipt_date", "IPT Date"], ["ipt_on_day", "IPT on Day"], ["sending_org_name", "Sending Org Name"], ["receiving_org_name", "Receiving Org Name"]]} /> : null}
                {activeSection === "tracking" ? <TrackingCommentsSection rows={data.tracking_comments} /> : null}
                {activeSection === "patient" ? <PatientSection data={data.patient_360} patientTab={patientTab} setPatientTab={setPatientTab} appointments={data.outpatient_appointments} inpatient={data.inpatient_procedures} testResults={data.test_results} /> : null}
              </div>
            </div>
          </>
        ) : null}
      </aside>
    </>
  )
}

function PathwayDetailsSection({ data }) {
  const milestoneRows = useMemo(() => data.milestones.map((item, index) => ({ ...item, x: new Date(item.event_date).getTime(), y: index })), [data.milestones])
  const yLabels = data.milestones.map((item) => item.label)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-2">
        <DetailCard title="Pathway">
          <KeyValue label="Pathway Status" value={<StatusPill tone={data.details.pathway_status === "Benign" ? "neutral" : "warning"}>{data.details.pathway_status}</StatusPill>} />
          <KeyValue label="Days Since Adjusted Pathway Start" value={data.details.days_since_adjusted_pathway_start ?? "No value"} />
          <KeyValue label="Pathway Type" value={data.details.pathway_type} />
          <KeyValue label="Cancer Site" value={data.details.cancer_site} />
          <KeyValue label="Cancer Sub Site" value={data.details.cancer_sub_site} />
          <KeyValue label="Hospital Site" value={data.details.hospital_site} />
        </DetailCard>
        <DetailCard title="Dates">
          <KeyValue label="Adjusted Pathway Start Date" value={formatDate(data.details.adjusted_pathway_start_date)} />
          <KeyValue label="Pathway Closed Date" value={data.details.pathway_closed_date ? formatDate(data.details.pathway_closed_date) : <span className="italic text-slate-400">No value</span>} />
          <KeyValue label="28 Day Breach Date" value={<DateCell value={data.details.breach_date_28} warn={data.details.breach_date_28 && new Date(data.details.breach_date_28) < new Date()} />} />
          <KeyValue label="31 Day Breach Date" value={<DateCell value={data.details.breach_date_31} warn={data.details.breach_date_31 && new Date(data.details.breach_date_31) < new Date()} />} />
          <KeyValue label="62 Day Breach Date" value={<DateCell value={data.details.breach_date_62} warn={data.details.breach_date_62 && new Date(data.details.breach_date_62) < new Date()} />} />
          <KeyValue label="Original Pathway Start Date" value={formatDate(data.details.original_pathway_start_date)} />
        </DetailCard>
        <DetailCard title="Patient">
          <KeyValue label="Full Name" value={data.details.full_name} />
          <KeyValue label="NHS Number" value={data.details.nhs_number} />
          <KeyValue label="MRN" value={data.details.mrn || "No value"} />
          <KeyValue label="Phone Number" value={data.details.phone_number || "No value"} />
          <KeyValue label="Date Of Birth" value={formatDate(data.details.date_of_birth)} />
          <KeyValue label="Hospital Site" value={data.details.hospital_site} />
        </DetailCard>
        <DetailCard title="Tags">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm font-semibold text-slate-900">Active pathway tags</div>
            <button className="rounded-lg border border-slate-200 p-2 text-slate-500"><Icon name="grid" className="h-4 w-4" /></button>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.details.tags?.length ? data.details.tags.map((tag) => <span key={tag} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">{tag}</span>) : <span className="italic text-slate-400">No tags</span>}
          </div>
          <div className="mt-4 text-sm text-slate-500">Watchlist reason: {data.details.watchlist_reason || "No value"}</div>
        </DetailCard>
      </div>
      <div className="surface border border-slate-200 p-5 shadow-none">
        <div className="mb-4 text-lg font-semibold text-slate-900">Pathway Milestones</div>
        {milestoneRows.length ? (
          <div className="h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, left: 30, bottom: 20 }}>
                <CartesianGrid stroke="#e5e7eb" />
                <XAxis type="number" dataKey="x" domain={["dataMin", "dataMax"]} tickFormatter={(value) => new Date(value).toLocaleString("en-GB", { month: "short" })} tick={{ fontSize: 12 }} />
                <YAxis type="number" dataKey="y" tickFormatter={(value) => yLabels[value] || ""} tick={{ fontSize: 12 }} width={220} allowDecimals={false} />
                <Tooltip formatter={(value, name, entry) => [formatDate(entry.payload.event_date), entry.payload.label]} labelFormatter={() => ""} />
                <Scatter data={milestoneRows} fill="#64748b" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        ) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">No milestone data available for this pathway.</div>}
      </div>
    </div>
  )
}

function DetailCard({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-4 text-sm font-semibold text-slate-900">{title}</div>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function KeyValue({ label, value }) {
  return (
    <div className="grid grid-cols-[180px,1fr] gap-3 text-sm">
      <div className="text-slate-500">{label}</div>
      <div className="text-slate-800">{value}</div>
    </div>
  )
}

function ActionsSection({ data, externalActions, selectedAction, setSelectedAction }) {
  const rows = useMemo(() => data?.length ? data : (externalActions || []).map((action) => ({
    action_id: action.action_id,
    title: action.action_type,
    due_date: action.due_date,
    status: action.status,
    detail: action.action_description || action.notes,
    owner: action.assigned_user || action.assigned_team,
    priority: action.priority,
    history: [],
  })), [data, externalActions])

  return (
    <div className="grid gap-5 xl:grid-cols-[1.2fr,0.8fr]">
      <div className="overflow-hidden rounded-2xl border border-slate-200">
        <table className="w-full border-separate border-spacing-0">
          <thead><tr><th className="table-head w-12">!</th><th className="table-head">Title</th><th className="table-head">Due Date</th><th className="table-head">Action Status</th><th className="table-head">Action Detail</th><th className="table-head">Owner</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.action_id} onClick={() => setSelectedAction(row)} className="cursor-pointer hover:bg-slate-50">
                <td className="table-cell"><span className={classNames("inline-block h-3 w-3 rounded-sm", row.priority === "high" ? "bg-red-500" : "bg-amber-400")} /></td>
                <td className="table-cell">{row.title}</td>
                <td className="table-cell">{row.due_date ? formatDate(row.due_date) : "No value"}</td>
                <td className="table-cell">{(row.status || "").toLowerCase() === "completed" ? <span>Completed</span> : <span className="font-medium text-emerald-600">Open</span>}</td>
                <td className="table-cell">{row.detail || "No value"}</td>
                <td className="table-cell">{row.owner || "Unassigned"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        {selectedAction ? (
          <>
            <div className="mb-4 flex items-start justify-between gap-3">
              <div><div className="text-base font-semibold text-slate-900">{selectedAction.title}</div><div className="mt-1 text-sm text-slate-500">Due: {selectedAction.due_date ? formatDate(selectedAction.due_date) : "No value"}</div></div>
              <div className="flex items-center gap-2"><button className="rounded-xl bg-success px-3 py-2 text-sm font-semibold text-white">Update</button><button onClick={() => setSelectedAction(null)} className="rounded-full p-2 text-slate-500 hover:bg-slate-100"><Icon name="x" className="h-4 w-4" /></button></div>
            </div>
            <div className="space-y-4">
              {(selectedAction.history || []).map((entry, index) => (
                <div key={`${entry.event_type}-${index}`} className="relative pl-6">
                  <div className={classNames("absolute left-0 top-1 h-3 w-3 rounded-full", entry.tone === "success" ? "bg-emerald-500" : entry.tone === "info" ? "bg-sky-500" : "bg-violet-500")} />
                  <div className="text-xs uppercase tracking-wide text-slate-400">{entry.event_type}</div>
                  <div className="mt-1 text-sm font-semibold text-slate-900">{entry.title}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatDateTime(entry.timestamp)}</div>
                  <div className="mt-1 text-sm text-slate-600">{entry.detail || "No additional detail recorded."}</div>
                  <div className="mt-1 text-xs text-slate-500">{entry.actor ? `Created By - ${entry.actor}` : "System generated event"}</div>
                </div>
              ))}
            </div>
          </>
        ) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">Select an action to inspect its update timeline.</div>}
      </div>
    </div>
  )
}

function SimpleTableSection({ title, rows, columns }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4"><div className="text-lg font-semibold text-slate-900">{title}</div><button className="rounded-xl border border-slate-200 p-2 text-slate-500"><Icon name="grid" className="h-4 w-4" /></button></div>
      <table className="w-full border-separate border-spacing-0">
        <thead><tr>{columns.map(([key, label]) => <th key={key} className="table-head">{label}</th>)}</tr></thead>
        <tbody>
          {rows?.length ? rows.map((row) => (
            <tr key={row.record_id}>
              {columns.map(([key]) => <td key={key} className="table-cell">{String(key).includes("date") ? (row[key] ? formatDate(row[key]) : <span className="italic text-slate-400">No value</span>) : (row[key] || <span className="italic text-slate-400">No value</span>)}</td>)}
            </tr>
          )) : <tr><td className="table-cell text-slate-500" colSpan={columns.length}>No records found for this section.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function ReportSection({ title, rows, selectedReport, setSelectedReport }) {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr,0.9fr]">
      <div className="overflow-hidden rounded-2xl border border-slate-200">
        <table className="w-full border-separate border-spacing-0">
          <thead><tr><th className="table-head">{title === "Histology" ? "Histology Type" : "Radiology Exam Type"}</th><th className="table-head">Exam Status</th><th className="table-head">Priority</th><th className="table-head">{title === "Histology" ? "Report Date" : "Ordered Date"}</th></tr></thead>
          <tbody>
            {rows?.length ? rows.map((row) => (
              <tr key={row.record_id} onClick={() => setSelectedReport(row)} className="cursor-pointer hover:bg-slate-50">
                <td className="table-cell">{row.name}</td>
                <td className="table-cell">{(row.status || "").toLowerCase() === "reported" ? <span className="font-medium text-emerald-600">reported</span> : row.status}</td>
                <td className="table-cell">{row.priority || "Normal"}</td>
                <td className="table-cell">{row.report_date ? formatDate(row.report_date) : row.ordered_date ? formatDate(row.ordered_date) : "No value"}</td>
              </tr>
            )) : <tr><td className="table-cell text-slate-500" colSpan={4}>No reports found for this section.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        {selectedReport ? (
          <>
            <div className="mb-4 flex items-start justify-between gap-3"><div><div className="text-base font-semibold text-slate-900">{selectedReport.name}</div><div className="mt-1 text-sm text-slate-500">Report Authorised: {selectedReport.report_date ? formatDate(selectedReport.report_date) : "No value"}</div></div><button onClick={() => setSelectedReport(null)} className="rounded-full p-2 text-slate-500 hover:bg-slate-100"><Icon name="x" className="h-4 w-4" /></button></div>
            <div className="rounded-2xl border-l-4 border-emerald-700 bg-slate-50 p-5 text-sm text-slate-700">
              <div className="font-semibold text-slate-900">Notional Hospital</div>
              <div className="mt-2">Referral Source: General Practitioner</div>
              <div className="mt-3 font-semibold text-slate-900">Clinical Question</div>
              <div className="mt-1">{selectedReport.summary || "Review diagnostic findings and correlate clinically."}</div>
              <div className="mt-3 font-semibold text-slate-900">Findings</div>
              <div className="mt-1 whitespace-pre-wrap">{selectedReport.report_text || "No report text available."}</div>
              <div className="mt-3 font-semibold text-slate-900">Conclusion</div>
              <div className="mt-1">{selectedReport.summary || "Conclusion not recorded."}</div>
              <div className="mt-4 text-xs text-slate-500">This is a synthetic report view generated from the current Cancer 360 payloads.</div>
            </div>
          </>
        ) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">Select a report row to inspect the full report card.</div>}
      </div>
    </div>
  )
}

function MDTSection({ meetings }) {
  return (
    <div className="space-y-4">
      {meetings?.length ? meetings.map((meeting) => (
        <div key={meeting.meeting_id} className="overflow-hidden rounded-2xl border border-slate-200">
          <div className="flex items-center justify-between bg-amber-100 px-5 py-4"><div className="text-sm font-semibold text-amber-900">{formatDate(meeting.meeting_date)} | {meeting.status}</div><div className="flex items-center gap-2 text-xs font-semibold text-amber-800">MDT Notes {meeting.note_count}<Icon name="chevron-down" className="h-4 w-4" /></div></div>
          <div className="space-y-3 bg-white p-5">
            {meeting.notes.map((note, index) => <div key={index} className="rounded-xl border border-slate-200 p-4"><div className="mb-2 flex items-center gap-2"><span className={classNames("rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-wide", note.note_type === "outcome" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600")}>{note.note_type}</span><span className="text-xs text-slate-400">{formatDateTime(note.created_at)}</span></div><div className="text-sm text-slate-700">{note.text}</div></div>)}
          </div>
        </div>
      )) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">No MDT meetings recorded for this pathway.</div>}
    </div>
  )
}

function TestResultsSection({ rows }) {
  return (
    <div className="space-y-3">
      {rows?.length ? rows.map((row) => <div key={row.record_id} className="rounded-2xl border border-slate-200 bg-white p-4"><div className="flex items-start justify-between gap-4"><div className="flex gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100 text-xs font-bold text-amber-700">ba</div><div><div className="text-sm font-semibold text-slate-900">{row.test_name}</div><div className="mt-2 grid gap-1 text-sm text-slate-600 md:grid-cols-2"><div>Test Date: {row.test_date ? formatDate(row.test_date) : "No value"}</div><div>Value: {row.value || "No value"}</div><div>Unit: {row.unit || "No value"}</div><div>Test Value Type: {row.value_type || row.test_name}</div></div></div></div><button className="rounded-xl border border-slate-200 p-2 text-slate-500"><Icon name="grid" className="h-4 w-4" /></button></div></div>) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">No test results available.</div>}
    </div>
  )
}

function TrackingCommentsSection({ rows }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><button className="flex items-center gap-2 rounded-xl bg-success px-4 py-2 text-sm font-semibold text-white"><Icon name="pencil" className="h-4 w-4" />Prepare an Example Tracking Comment</button></div>
      {rows?.length ? rows.map((row) => <div key={row.record_id} className="rounded-2xl border border-slate-200 bg-white p-4"><div className="grid gap-3 text-sm md:grid-cols-3"><div><span className="font-medium text-slate-800">Created At:</span> <span className="text-slate-600">{formatDateTime(row.created_at)}</span></div><div><span className="font-medium text-slate-800">Created By:</span> <span className="text-slate-600">{row.created_by || "System"}</span></div><div><span className="font-medium text-slate-800">Source:</span> <span className="text-slate-600">{row.source_system || "Cancer 360"}</span></div></div><div className="mt-3 text-sm text-slate-700">{row.comment_text}</div></div>) : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">No tracking comments available.</div>}
    </div>
  )
}

function PatientSection({ data, patientTab, setPatientTab, appointments, inpatient, testResults }) {
  const activityRows = useMemo(() => (data?.timeline || []).map((item, index) => ({ x: new Date(item.event_date).getTime(), y: index, label: item.label, type: item.event_type })), [data])
  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex items-center gap-3"><Icon name="people" className="h-5 w-5 text-brand" /><div><div className="text-lg font-semibold text-slate-900">{data.patient.surname}, {data.patient.forename}</div><div className="text-sm text-slate-500">[CDM] Patient</div></div></div>
        <div className="mt-4 flex gap-2">{[["overview", "Overview"], ["diagnosis", "Diagnosis History"], ["tests", "Test Results"]].map(([key, label]) => <button key={key} onClick={() => setPatientTab(key)} className={classNames("rounded-full px-4 py-2 text-sm font-medium", patientTab === key ? "bg-brand text-white" : "bg-slate-100 text-slate-700")}>{label}</button>)}</div>
      </div>
      {patientTab === "overview" ? <>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <DetailCard title="Patient Details"><KeyValue label="Full Name" value={`${data.patient.surname}, ${data.patient.forename}`} /><KeyValue label="Deceased" value={<StatusPill tone="neutral">{data.patient.deceased_date ? "Yes" : "No"}</StatusPill>} /><KeyValue label="MRN" value={data.patient.hospital_number || "No value"} /><KeyValue label="NHS Number" value={data.patient.nhs_number} /><KeyValue label="Sex" value={data.patient.sex === "F" ? "female" : "male"} /><KeyValue label="Age" value={data.patient.age ?? "No value"} /></DetailCard>
          <DetailCard title="Demographics"><KeyValue label="Date Of Birth" value={formatDate(data.patient.date_of_birth)} /><KeyValue label="Date Of Death" value={data.patient.deceased_date ? formatDate(data.patient.deceased_date) : <span className="italic text-slate-400">No value</span>} /><KeyValue label="Phone Number" value={data.patient.phone || "No value"} /><KeyValue label="Address Line 1" value="No value" /><KeyValue label="Address Line 2" value="No value" /><KeyValue label="Postcode" value={data.patient.postcode || "No value"} /></DetailCard>
          <DetailCard title="Referral Summary"><KeyValue label="Cancer Type" value={data.pathway?.cancer_site || data.pathway?.cancer_type_desc || "No value"} /><KeyValue label="Pathway Status" value={data.pathway?.pathway_status || "No value"} /><KeyValue label="Next Action" value={data.pathway?.next_action || "No value"} /><KeyValue label="Assigned Team" value={data.pathway?.assigned_team || "No value"} /></DetailCard>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between"><div className="text-lg font-semibold text-slate-900">Activity Timeline</div><LabeledSelect label="Specialties" value="" onChange={() => {}} options={["All specialties"]} compact /></div>
          {activityRows.length ? <div className="h-72"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 20, right: 20, left: 20, bottom: 20 }}><CartesianGrid stroke="#e5e7eb" /><XAxis type="number" dataKey="x" tickFormatter={(value) => new Date(value).toLocaleString("en-GB", { month: "short" })} tick={{ fontSize: 12 }} /><YAxis type="number" dataKey="y" tickFormatter={(value) => activityRows[value]?.label || ""} tick={{ fontSize: 12 }} width={220} allowDecimals={false} /><Tooltip formatter={(value, name, entry) => [formatDate(new Date(entry.payload.x)), entry.payload.type]} labelFormatter={() => ""} /><Scatter data={activityRows} fill="#2563eb" /></ScatterChart></ResponsiveContainer></div> : <div className="rounded-2xl bg-slate-50 p-6 text-sm text-slate-500">No activity timeline available.</div>}
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500"><span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-slate-700" /> Inpatient Encounter</span><span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-emerald-600" /> First/New Outpatient Appointment</span><span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-blue-600" /> Follow-Up Outpatient Appointment</span></div>
        </div>
        <div className="grid gap-5 xl:grid-cols-2"><SimpleTableSection title="Outpatient Appointments" rows={appointments} columns={[["name", "Appointment Name"], ["status", "Appointment Status"], ["scheduled_date", "Scheduled Date"], ["attended_date", "Attended Date"]]} /><SimpleTableSection title="Inpatient Encounters" rows={inpatient} columns={[["name", "Encounter"], ["scheduled_date", "TCI Date"], ["specialty_name", "Specialty Name"], ["consultant_name", "Primary Consultant Name"]]} /></div>
      </> : null}
      {patientTab === "diagnosis" ? <div className="rounded-2xl border border-slate-200 bg-white p-5">{/* TODO: replace with a dedicated diagnosis history endpoint when available. */}<div className="text-lg font-semibold text-slate-900">Diagnosis History</div><div className="mt-4 space-y-4"><div className="rounded-2xl bg-slate-50 p-4"><div className="text-sm font-semibold text-slate-900">Primary diagnosis</div><div className="mt-2 text-sm text-slate-600">{data.diagnosis?.icd10_description || "No diagnosis history available."}</div><div className="mt-2 text-xs text-slate-500">Diagnosis date: {data.diagnosis?.diagnosis_date ? formatDate(data.diagnosis.diagnosis_date) : "No value"}</div></div><div className="rounded-2xl bg-slate-50 p-4"><div className="text-sm font-semibold text-slate-900">Staging snapshot</div><div className="mt-2 text-sm text-slate-600">{data.staging ? `${data.staging.tnm_t || "Tx"} ${data.staging.tnm_n || "Nx"} ${data.staging.tnm_m || "Mx"} - Stage ${data.staging.stage_group || "Unknown"}` : "No staging data available."}</div></div></div></div> : null}
      {patientTab === "tests" ? <TestResultsSection rows={testResults} /> : null}
    </div>
  )
}

function formatDateTimeInputValue(value) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  const offset = date.getTimezoneOffset()
  const local = new Date(date.getTime() - (offset * 60000))
  return local.toISOString().slice(0, 16)
}

function ActionToolbar({ compact = false }) {
  const buttons = [
    { label: "Add Comment", className: "bg-slate-200 text-slate-700" },
    { label: "Assign", className: "bg-sky-600 text-white" },
    { label: "Complete", className: "bg-success text-white" },
    { label: "Escalate", className: "bg-red-600 text-white" },
    { label: "Revoke", className: "bg-rose-500 text-white" },
    { label: "Reassign team", className: "border border-sky-500 bg-white text-sky-600" },
  ]
  return (
    <div className={classNames("flex flex-wrap items-center gap-2", compact ? "" : "justify-end")}>
      {buttons.map((button) => (
        <button key={button.label} className={classNames("rounded-xl px-3 py-2 text-sm font-semibold", button.className)}>
          {button.label}
        </button>
      ))}
    </div>
  )
}

function MetricCard({ title, value, subtitle, tone = "neutral" }) {
  const tones = {
    neutral: "bg-white text-slate-900",
    amber: "bg-amber-100 text-amber-950",
    danger: "bg-red-100 text-red-900",
  }
  return (
    <div className={classNames("rounded-[24px] border border-slate-200 p-5 shadow-sm", tones[tone] || tones.neutral)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{title}</div>
          <div className="mt-3 text-3xl font-semibold">{value}</div>
          {subtitle ? <div className="mt-2 text-sm opacity-80">{subtitle}</div> : null}
        </div>
        <div className="rounded-full bg-white/70 p-2 text-brand">
          <Icon name="help" className="h-4 w-4" />
        </div>
      </div>
    </div>
  )
}

function ActionsFilterSidebar({ open, onClose, filters, setFilters, counts }) {
  const sections = [
    { label: "PATIENT", detail: `[CDM] Patient ${counts.patientCount}` },
    { label: "CANCER PATHWAY", detail: `[Cancer 360] Cancer Pathway ${counts.pathwayCount}` },
    { label: "ACTION COMMENTS", detail: `[Cancer 360] Cancer PTL Action Comment ${counts.commentCount}` },
    { label: "ALL ACTION HISTORY", detail: `[Cancer 360] Cancer PTL Action Changelog ${counts.historyCount}` },
    { label: "LINKED TRACKING AND DIAGNOSTICS TO PATHWAY", detail: `[Cancer 360] Cancer PTL Helper ${counts.helperCount}` },
  ]
  return (
    <>
      {open ? <button onClick={onClose} className="fixed inset-0 z-30 bg-slate-900/20" /> : null}
      <aside className={classNames("fixed inset-y-12 left-0 z-40 w-[360px] transform overflow-y-auto border-r border-slate-200 bg-white p-5 shadow-2xl transition duration-300", open ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-900">Filters &amp; Config</div>
          <button onClick={() => setFilters((current) => ({ ...current, search: "", detailSearch: "", cancerSite: "", hospitalSite: "", actionIsOpen: "true", actionStatus: "", teamName: "", owner: "", dueAfter: "", dueBefore: "", createdAfter: "", createdBefore: "" }))} className="rounded-full border border-red-200 px-3 py-1 text-xs font-medium text-red-600">Reset Filters</button>
        </div>
        <div className="mt-6 space-y-5 text-sm">
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Action Description</div>
            <input value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Search action descriptions" className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Action Detail</div>
            <input value={filters.detailSearch} onChange={(event) => setFilters((current) => ({ ...current, detailSearch: event.target.value }))} placeholder="Search detail summary" className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Action Is Open</div>
            <select value={filters.actionIsOpen} onChange={(event) => setFilters((current) => ({ ...current, actionIsOpen: event.target.value }))} className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none">
              <option value="true">True</option>
              <option value="false">False</option>
              <option value="">All</option>
            </select>
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Action Status</div>
            <input value={filters.actionStatus} onChange={(event) => setFilters((current) => ({ ...current, actionStatus: event.target.value }))} placeholder="Search status" className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Team Name</div>
            <input value={filters.teamName} onChange={(event) => setFilters((current) => ({ ...current, teamName: event.target.value }))} placeholder="Search team name" className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
          </div>
          <div>
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Owner</div>
            <input value={filters.owner} onChange={(event) => setFilters((current) => ({ ...current, owner: event.target.value }))} placeholder="Search owner" className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Due Date</div>
              <label className="flex items-center gap-2 text-xs text-slate-500"><input type="checkbox" checked readOnly /> Relative to today</label>
            </div>
            <div className="mt-3 grid gap-3">
              <input type="date" value={filters.dueAfter} onChange={(event) => setFilters((current) => ({ ...current, dueAfter: event.target.value }))} className="rounded-xl border border-slate-200 px-3 py-2 outline-none" />
              <input type="date" value={filters.dueBefore} onChange={(event) => setFilters((current) => ({ ...current, dueBefore: event.target.value }))} className="rounded-xl border border-slate-200 px-3 py-2 outline-none" />
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Action Created Date</div>
            <div className="mt-1 text-xs text-slate-400">GMT+1</div>
            <div className="mt-3 grid gap-3">
              <input type="datetime-local" value={filters.createdAfter} onChange={(event) => setFilters((current) => ({ ...current, createdAfter: event.target.value }))} className="rounded-xl border border-slate-200 px-3 py-2 outline-none" />
              <input type="datetime-local" value={filters.createdBefore} onChange={(event) => setFilters((current) => ({ ...current, createdBefore: event.target.value }))} className="rounded-xl border border-slate-200 px-3 py-2 outline-none" />
            </div>
          </div>
          {sections.map((section) => (
            <button key={section.label} className="flex w-full items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-left hover:bg-slate-50">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{section.label}</div>
                <div className="mt-1 text-sm text-slate-700">{section.detail}</div>
              </div>
              <Icon name="chevron-down" className="h-4 w-4 text-slate-400" />
            </button>
          ))}
          <button className="w-full rounded-xl border border-dashed border-slate-300 px-4 py-3 text-sm font-semibold text-slate-600">Add filter</button>
        </div>
      </aside>
    </>
  )
}

function ActionsTable({ rows, onOpenAction, selectedActionIds, setSelectedActionIds }) {
  const columns = [
    { key: "select", label: "", width: 52, sticky: 0 },
    { key: "due_date", label: "Due Date", width: 145, sticky: 52 },
    { key: "title", label: "Title", width: 210, sticky: 197 },
    { key: "action_detail_summary", label: "Action Detail Summary", width: 240, sticky: 407 },
    { key: "pathway_day", label: "Pathway Day", width: 110 },
    { key: "patient_name", label: "Patient", width: 220 },
    { key: "cancer_site", label: "Cancer Site", width: 150 },
    { key: "mrn", label: "MRN", width: 130 },
    { key: "nhs_number", label: "NHS Number", width: 150 },
    { key: "action_status", label: "Action Status", width: 130 },
    { key: "days_open", label: "Days Open", width: 110 },
    { key: "pathway_is_open", label: "Pathway Is Open", width: 130 },
    { key: "pathway_status", label: "Pathway Status", width: 140 },
    { key: "latest_action_comment", label: "Latest Action Comment", width: 260 },
    { key: "owner", label: "Owner", width: 150 },
    { key: "team_name", label: "Team Name", width: 180 },
    { key: "breach_date_28", label: "28 Day Breach Date", width: 170 },
    { key: "breach_date_31", label: "31 Day Breach Date", width: 170 },
    { key: "breach_date_62", label: "62 Day Breach Date", width: 170 },
    { key: "first_op_appt_attended_date", label: "First Op Appt Attended Date", width: 180 },
    { key: "next_op_appt_attended_date", label: "Next Op Appt", width: 160 },
    { key: "latest_radiology_attended_date", label: "Latest Radiology Attended Date", width: 190 },
    { key: "latest_histology_attended_date", label: "Latest Histology Attended Date", width: 190 },
    { key: "latest_ip_procedure_tci_date", label: "Latest IP Procedure TCI Date", width: 190 },
  ]

  function toggleRow(id) {
    setSelectedActionIds((current) => current.includes(id) ? current.filter((value) => value !== id) : current.concat(id))
  }

  function renderCell(row, column) {
    if (column.key === "select") {
      return <input type="checkbox" checked={selectedActionIds.includes(row.action_id)} onChange={() => toggleRow(row.action_id)} onClick={(event) => event.stopPropagation()} />
    }
    if (column.key === "due_date") return <DateCell value={row.due_date} warn={row.due_date && new Date(row.due_date) < new Date()} />
    if (column.key === "title") {
      return <div className="flex items-center gap-3"><span className={classNames("inline-block h-3 w-3 rounded-sm", row.priority === "high" ? "bg-red-600" : row.priority === "medium" ? "bg-amber-500" : "bg-slate-300")} /><span className="font-medium text-slate-900">{row.title}</span></div>
    }
    if (column.key === "action_status") return <span className={row.action_status === "Escalated" ? "font-semibold text-red-600" : row.action_status === "Completed" ? "text-slate-500" : "font-semibold text-emerald-600"}>{row.action_status}</span>
    if (column.key === "pathway_is_open") return row.pathway_is_open ? "True" : "False"
    if (column.key === "pathway_status") return row.pathway_status ? <StatusPill tone={row.pathway_status === "Suspected" ? "warning" : "neutral"}>{row.pathway_status}</StatusPill> : <span className="italic text-slate-400">No value</span>
    if (["breach_date_28", "breach_date_31", "breach_date_62"].includes(column.key)) return <DateCell value={row[column.key]} warn={row[column.key] && new Date(row[column.key]) < new Date()} />
    if (["first_op_appt_attended_date", "next_op_appt_attended_date", "latest_radiology_attended_date", "latest_histology_attended_date", "latest_ip_procedure_tci_date"].includes(column.key)) return <NullableDate value={row[column.key]} />
    if (column.key === "latest_action_comment" || column.key === "action_detail_summary") return <div className="max-w-[260px] truncate">{row[column.key] || <span className="italic text-slate-400">No value</span>}</div>
    return row[column.key] ?? <span className="italic text-slate-400">No value</span>
  }

  return (
    <div className="scrollbar-thin overflow-auto">
      <table className="min-w-[3300px] border-separate border-spacing-0">
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th key={column.key} className="table-head sticky top-0 z-20 whitespace-nowrap underline decoration-slate-300 underline-offset-4" style={column.sticky !== undefined ? { left: column.sticky, minWidth: column.width, width: column.width, zIndex: 25 + (10 - index) } : { minWidth: column.width, width: column.width }}>
                {column.key === "due_date" ? <div className="flex items-center gap-1">{column.label}<span className="text-slate-400">▲▼</span></div> : column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row.action_id} onClick={() => onOpenAction(row.action_id)} className={classNames("cursor-pointer", rowIndex % 2 === 0 ? "bg-white" : "bg-slate-50/70")}>
              {columns.map((column, index) => (
                <td key={column.key} className="table-cell" style={column.sticky !== undefined ? { left: column.sticky, position: "sticky", background: rowIndex % 2 === 0 ? "#fff" : "#f8fafc", zIndex: 15 + (10 - index), minWidth: column.width, width: column.width } : { minWidth: column.width, width: column.width }}>
                  {renderCell(row, column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ActionHistoryTimeline({ history }) {
  return (
    <div className="space-y-4">
      {history?.length ? history.map((entry, index) => (
        <div key={`${entry.event_type}-${index}`} className="relative pl-6">
          <div className={classNames("absolute left-0 top-1 h-3 w-3 rounded-full", entry.event_type === "CREATE ACTION" ? "bg-emerald-500" : entry.event_type === "ASSIGN TO USER" ? "bg-sky-500" : entry.event_type === "COMMENT" && /escal/i.test(entry.title || "") ? "bg-red-500" : "bg-violet-500")} />
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{entry.event_type}</div>
          <div className="mt-1 text-sm font-semibold text-slate-900">{entry.title}</div>
          <div className="mt-1 text-xs text-slate-500">{formatDateTime(entry.timestamp)}</div>
          <div className="mt-1 text-sm text-slate-700">{entry.detail || "No additional detail recorded."}</div>
          <div className="mt-1 text-xs text-slate-500">{entry.actor ? `Created By - ${entry.actor}` : "System generated event"}</div>
        </div>
      )) : <div className="rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">No action history available.</div>}
    </div>
  )
}

function ActionDetailsPanel({ action }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white p-5">
      <div className="mb-4 text-sm font-semibold text-slate-900">Action Details</div>
      <div className="space-y-3">
        <KeyValue label="Pathway" value={action.pathway_id || "No linked pathway"} />
        <KeyValue label="Status" value={action.action_status} />
        <KeyValue label="Team" value={action.team_name || "Unassigned"} />
        <KeyValue label="Owner" value={action.owner || "Unassigned"} />
        <KeyValue label="Due Date" value={action.due_date ? formatDate(action.due_date) : "No value"} />
        <KeyValue label="Last Updated" value={action.last_updated ? formatDateTime(action.last_updated) : "No value"} />
        <KeyValue label="Last Updated By" value={action.last_updated_by || "No value"} />
      </div>
    </div>
  )
}

function ActionDetailView({ detail, showEmbeddedPathway = true }) {
  if (!detail) return null
  return (
    <div className="space-y-5">
      <ActionToolbar />
      <div className="grid gap-4 xl:grid-cols-[1.4fr,0.6fr,0.8fr]">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Title</div>
          <div className="mt-2 text-lg font-semibold text-slate-900">{detail.action.title}</div>
          <div className="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-500">Action Detail</div>
          <div className="mt-2 text-sm text-slate-700">{detail.action.action_detail_summary || "No action detail recorded."}</div>
        </div>
        <div className="rounded-[24px] bg-emerald-100 p-5">
          <div className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Days Open</div>
          <div className="mt-3 text-3xl font-semibold text-emerald-900">{detail.action.days_open}</div>
        </div>
        <div className="rounded-[24px] bg-red-100 p-5">
          <div className="text-xs font-semibold uppercase tracking-wide text-red-700">Due Date</div>
          <div className="mt-3 text-lg font-semibold text-red-900">{detail.action.due_date ? formatDate(detail.action.due_date) : "No value"}</div>
        </div>
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.1fr,0.9fr]">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5">
          <div className="mb-4 text-sm font-semibold text-slate-900">Action History</div>
          <ActionHistoryTimeline history={detail.history} />
        </div>
        <ActionDetailsPanel action={detail.action} />
      </div>
      {showEmbeddedPathway && detail.action.pathway_id ? (
        <div>
          <div className="mb-3 text-sm font-semibold text-slate-900">Linked Pathway</div>
          <PathwayDrawer pathwayId={detail.action.pathway_id} embedded />
        </div>
      ) : null}
    </div>
  )
}

function ActionDrawer({ actionId, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!actionId) return
    setLoading(true)
    setError("")
    apiGet(`/actions/${actionId}/detail`)
      .then((payload) => {
        setDetail(payload)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || "Unable to load action detail")
        setLoading(false)
      })
  }, [actionId])

  if (!actionId) return null

  return (
    <>
      <button onClick={onClose} className="fixed inset-0 z-40 bg-slate-900/30" />
      <aside className="fixed inset-y-12 right-0 z-50 flex w-[min(74vw,1320px)] max-w-full flex-col border-l border-slate-200 bg-white shadow-2xl">
        {loading ? <div className="p-6"><LoadingCard label="Loading action drawer..." /></div> : null}
        {error ? <div className="p-6"><ErrorCard message={error} retry={() => {}} /></div> : null}
        {!loading && !error && detail ? (
          <>
            <div className="flex items-center gap-3 bg-brand px-5 py-4 text-white">
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold">{detail.action.title} - {detail.action.patient_name} | MRN: {detail.action.mrn || "No value"} | {detail.action.cancer_site || "Unknown"} | Day {detail.action.pathway_day || "No value"}</div>
              </div>
              <button className="flex items-center gap-2 rounded-xl bg-success px-3 py-2 text-sm font-semibold text-white"><Icon name="link" className="h-4 w-4" />External Links<Icon name="chevron-down" className="h-4 w-4" /></button>
              <button onClick={onClose} className="rounded-full p-2 hover:bg-white/10"><Icon name="x" className="h-4 w-4" /></button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              <ActionDetailView detail={detail} />
            </div>
          </>
        ) : null}
      </aside>
    </>
  )
}

function RecentActionUpdatesView({ updates, expandedUpdateId, setExpandedUpdateId, page, perPage, total }) {
  const end = Math.min(page * perPage, total)
  const start = total ? ((page - 1) * perPage) + 1 : 0
  return (
    <div className="space-y-4">
      {updates.map((item) => {
        const expanded = expandedUpdateId === item.update_id
        const toneClasses = item.update_tone === "green" ? "bg-emerald-100 text-emerald-700" : item.update_tone === "blue" ? "bg-sky-100 text-sky-700" : "bg-violet-100 text-violet-700"
        return (
          <div key={item.update_id} className="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm">
            <button onClick={() => setExpandedUpdateId(expanded ? null : item.update_id)} className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-slate-50">
              <div className={classNames("rounded-full px-3 py-2 text-xs font-semibold", toneClasses)}>{item.update_type}</div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-slate-900">{item.title}</div>
                <div className="mt-1 text-xs text-slate-500">{formatDateTime(item.timestamp)}</div>
              </div>
              <Icon name="chevron-down" className={classNames("h-4 w-4 text-slate-400 transition", expanded ? "rotate-180" : "")} />
            </button>
            {expanded ? (
              <div className="border-t border-slate-200 bg-slate-50/70 p-5">
                <div className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl bg-white px-4 py-3 text-sm">
                  <span className="inline-block h-3 w-3 rounded-sm bg-red-600" />
                  <span className="font-semibold text-slate-900">{item.action_detail.action.patient_name}</span>
                  <span className="text-slate-500">| MRN: {item.action_detail.action.mrn || "No value"}</span>
                  <span className="text-slate-500">| {item.action_detail.action.cancer_site || "Unknown"}</span>
                  <span className="text-slate-500">| Day {item.action_detail.action.pathway_day || "No value"}</span>
                </div>
                {item.comment_text ? (
                  <div className="mb-5 rounded-2xl border border-violet-200 bg-violet-50 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-violet-700">{item.comment_title || item.update_type}</div>
                    <div className="mt-2 text-sm text-violet-900">{item.comment_text}</div>
                  </div>
                ) : null}
                <ActionDetailView detail={item.action_detail} showEmbeddedPathway />
              </div>
            ) : null}
          </div>
        )
      })}
      <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm text-slate-600">
        <div>Showing {start}-{end} of {total} items</div>
        <div className="text-xs text-slate-400">Pagination controls will be expanded in a later pass.</div>
      </div>
    </div>
  )
}

function ActionsPage() {
  const [listData, setListData] = useState({ items: [], summary: null })
  const [updatesData, setUpdatesData] = useState({ items: [], total: 0, page: 1, per_page: 30 })
  const [loading, setLoading] = useState(true)
  const [updatesLoading, setUpdatesLoading] = useState(false)
  const [error, setError] = useState("")
  const [filterSidebarOpen, setFilterSidebarOpen] = useState(false)
  const [selectedActionId, setSelectedActionId] = useState(null)
  const [selectedActionIds, setSelectedActionIds] = useState([])
  const [activeView, setActiveView] = useState("list")
  const [worklistScope, setWorklistScope] = useState("all")
  const [expandedUpdateId, setExpandedUpdateId] = useState(null)
  const [filters, setFilters] = useState({
    search: "",
    detailSearch: "",
    cancerSite: "",
    hospitalSite: "",
    actionStatus: "",
    teamName: "",
    owner: "",
    actionIsOpen: "true",
    dueAfter: "",
    dueBefore: "",
    createdAfter: "",
    createdBefore: "",
  })
  const [updatesFilters, setUpdatesFilters] = useState({
    fromDateTime: "",
    toDateTime: "",
    updateTypes: [],
    excludeUsers: [],
  })

  function buildWorklistQuery() {
    const params = new URLSearchParams({ view_scope: "all" })
    if (worklistScope === "watchlist") params.set("watchlist_only", "true")
    if (filters.search || filters.detailSearch) params.set("search", [filters.search, filters.detailSearch].filter(Boolean).join(" "))
    if (filters.cancerSite) params.set("cancer_site", filters.cancerSite)
    if (filters.hospitalSite) params.set("hospital_site", filters.hospitalSite)
    if (filters.actionStatus) params.set("action_status", filters.actionStatus)
    if (filters.teamName) params.set("team_name", filters.teamName)
    if (filters.owner) params.set("owner", filters.owner)
    if (filters.actionIsOpen !== "") params.set("action_is_open", filters.actionIsOpen)
    if (filters.dueAfter) params.set("due_after", filters.dueAfter)
    if (filters.dueBefore) params.set("due_before", filters.dueBefore)
    if (filters.createdAfter) params.set("created_after", new Date(filters.createdAfter).toISOString())
    if (filters.createdBefore) params.set("created_before", new Date(filters.createdBefore).toISOString())
    return params.toString()
  }

  function loadWorklist() {
    setLoading(true)
    setError("")
    apiGet(`/actions/worklist?${buildWorklistQuery()}`)
      .then((payload) => {
        setListData(payload)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || "Unable to load actions")
        setLoading(false)
      })
  }

  function loadUpdates() {
    setUpdatesLoading(true)
    const params = new URLSearchParams({ page: "1", per_page: "30" })
    if (updatesFilters.fromDateTime) params.set("from_datetime", new Date(updatesFilters.fromDateTime).toISOString())
    if (updatesFilters.toDateTime) params.set("to_datetime", new Date(updatesFilters.toDateTime).toISOString())
    updatesFilters.updateTypes.forEach((value) => params.append("update_type", value))
    updatesFilters.excludeUsers.forEach((value) => params.append("exclude_user", value))
    apiGet(`/actions/updates?${params.toString()}`)
      .then((payload) => {
        setUpdatesData(payload)
        setUpdatesLoading(false)
      })
      .catch((err) => {
        setError(err.message || "Unable to load recent action updates")
        setUpdatesLoading(false)
      })
  }

  useEffect(() => {
    loadWorklist()
  }, [worklistScope, filters.search, filters.detailSearch, filters.cancerSite, filters.hospitalSite, filters.actionStatus, filters.teamName, filters.owner, filters.actionIsOpen, filters.dueAfter, filters.dueBefore, filters.createdAfter, filters.createdBefore])

  useEffect(() => {
    loadUpdates()
  }, [updatesFilters.fromDateTime, updatesFilters.toDateTime, updatesFilters.updateTypes.join("|"), updatesFilters.excludeUsers.join("|")])

  const cancerSiteOptions = useMemo(() => Array.from(new Set((listData.items || []).map((row) => row.cancer_site).filter(Boolean))).sort(), [listData.items])
  const hospitalSiteOptions = useMemo(() => Array.from(new Set((listData.items || []).map((row) => row.hospital_site).filter(Boolean))).sort(), [listData.items])
  const ownerOptions = useMemo(() => Array.from(new Set((listData.items || []).map((row) => row.owner).filter(Boolean))).sort(), [listData.items])
  const summary = listData.summary || { my_actions: 0, team_actions: 0, awaiting_assignment: 0, escalated_team_actions: 0, all_actions: 0, watchlist_only: 0 }
  const filterCounts = {
    patientCount: new Set((listData.items || []).map((row) => row.patient_id)).size,
    pathwayCount: new Set((listData.items || []).map((row) => row.pathway_id).filter(Boolean)).size,
    commentCount: updatesData.total || 0,
    historyCount: (updatesData.total || 0) + (listData.items || []).length,
    helperCount: new Set((listData.items || []).map((row) => row.pathway_id).filter(Boolean)).size,
  }

  return (
    <main className="relative">
      <ActionsFilterSidebar open={filterSidebarOpen} onClose={() => setFilterSidebarOpen(false)} filters={filters} setFilters={setFilters} counts={filterCounts} />
      <div className="mx-auto max-w-[1650px] px-6 py-6">
        <div className="mb-3 rounded-2xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-900">All data shown is synthetic and does not relate to real people.</div>
        <div className="surface mb-4 p-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="flex items-start gap-3">
              <button onClick={() => setFilterSidebarOpen(true)} className="rounded-xl border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"><Icon name="filter" className="h-4 w-4" /></button>
              <div>
                <div className="flex items-center gap-2">
                  <Icon name="clipboard" className="h-4 w-4 text-brand" />
                  <h1 className="m-0 text-xl font-semibold text-slate-900">Cancer Actions</h1>
                </div>
                <button className="mt-2 flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">Saved module states<Icon name="chevron-down" className="h-3.5 w-3.5" /></button>
              </div>
            </div>
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
              <div className="flex rounded-full bg-slate-100 p-1">
                {[["list", "Actions List"], ["updates", "Recent Action Updates"]].map(([key, label]) => (
                  <button key={key} onClick={() => setActiveView(key)} className={classNames("rounded-full px-4 py-2 text-sm font-medium", activeView === key ? "bg-brand text-white" : "text-slate-600")}>{label}</button>
                ))}
              </div>
              <LabeledSelect label="Cancer Sites" value={filters.cancerSite} onChange={(value) => setFilters((current) => ({ ...current, cancerSite: value }))} options={cancerSiteOptions} />
              <LabeledSelect label="Hospital Sites" value={filters.hospitalSite} onChange={(value) => setFilters((current) => ({ ...current, hospitalSite: value }))} options={hospitalSiteOptions} />
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="My Actions" value={summary.my_actions} />
          <MetricCard title="Actions for my team(s)" value={summary.team_actions} subtitle={`${summary.awaiting_assignment} Awaiting assignment`} tone="amber" />
          <MetricCard title="Escalated actions for my team(s)" value={summary.escalated_team_actions} tone="danger" />
          <MetricCard title="All actions" value={summary.all_actions} />
        </div>

        <div className="surface mt-4 overflow-hidden">
          <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setWorklistScope("all")} className={classNames("rounded-full px-4 py-2 text-sm font-medium", worklistScope === "all" ? "bg-brand text-white" : "bg-slate-100 text-slate-700")}>all actions <span className="ml-1 rounded-full bg-white/20 px-2 py-0.5 text-xs">{summary.all_actions}</span></button>
              <button onClick={() => setWorklistScope("watchlist")} className={classNames("rounded-full px-4 py-2 text-sm font-medium", worklistScope === "watchlist" ? "bg-brand text-white" : "bg-slate-100 text-slate-700")}>watchlist only <span className="ml-1 rounded-full bg-white/20 px-2 py-0.5 text-xs">{summary.watchlist_only}</span></button>
            </div>
            <ActionToolbar />
          </div>

          {activeView === "list" ? (
            <>
              <div className="border-b border-slate-200 px-5 py-4">
                <div className="text-sm text-slate-600">{summary.all_actions} action rows available from the current Cancer 360 API.</div>
              </div>
              {loading ? <div className="p-5"><LoadingCard label="Loading actions..." /></div> : error ? <div className="p-5"><ErrorCard message={error} retry={loadWorklist} /></div> : <ActionsTable rows={listData.items || []} onOpenAction={setSelectedActionId} selectedActionIds={selectedActionIds} setSelectedActionIds={setSelectedActionIds} />}
            </>
          ) : (
            <div className="p-5">
              <div className="mb-5 grid gap-3 xl:grid-cols-[1fr,1fr,1fr,1fr]">
                <label className="text-sm text-slate-600">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">From</div>
                  <div className="text-xs text-slate-400">GMT+1</div>
                  <input type="datetime-local" value={updatesFilters.fromDateTime} onChange={(event) => setUpdatesFilters((current) => ({ ...current, fromDateTime: event.target.value }))} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
                </label>
                <label className="text-sm text-slate-600">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">To</div>
                  <div className="text-xs text-slate-400">GMT+1</div>
                  <input type="datetime-local" value={updatesFilters.toDateTime} onChange={(event) => setUpdatesFilters((current) => ({ ...current, toDateTime: event.target.value }))} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none" />
                </label>
                <label className="text-sm text-slate-600">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Update Type</div>
                  <select multiple value={updatesFilters.updateTypes} onChange={(event) => setUpdatesFilters((current) => ({ ...current, updateTypes: Array.from(event.target.selectedOptions).map((option) => option.value) }))} className="h-[104px] w-full rounded-xl border border-slate-200 px-3 py-2 outline-none">
                    {["Comment Added", "Created", "Assigned Owner"].map((option) => <option key={option} value={option}>{option}</option>)}
                  </select>
                </label>
                <label className="text-sm text-slate-600">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Exclude Updates Made By</div>
                  <select multiple value={updatesFilters.excludeUsers} onChange={(event) => setUpdatesFilters((current) => ({ ...current, excludeUsers: Array.from(event.target.selectedOptions).map((option) => option.value) }))} className="h-[104px] w-full rounded-xl border border-slate-200 px-3 py-2 outline-none">
                    {ownerOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                  </select>
                </label>
              </div>
              {updatesLoading ? <LoadingCard label="Loading recent action updates..." /> : <RecentActionUpdatesView updates={updatesData.items || []} expandedUpdateId={expandedUpdateId} setExpandedUpdateId={setExpandedUpdateId} page={updatesData.page || 1} perPage={updatesData.per_page || 30} total={updatesData.total || 0} />}
            </div>
          )}
        </div>
      </div>

      <ActionDrawer actionId={selectedActionId} onClose={() => setSelectedActionId(null)} />
    </main>
  )
}

function App() {
  return <BrowserRouter><AppLayout><Routes><Route path="/" element={<LandingPage />} /><Route path="/ptl" element={<PTLPage />} /><Route path="/actions" element={<ActionsPage />} /><Route path="/service-overview" element={<PlaceholderPage title="Service Overview" subtitle="Performance dashboard placeholder. This route will be expanded in the next screen build." />} /><Route path="/team-overview" element={<PlaceholderPage title="Team Overview" subtitle="Team analysis placeholder. The reusable pathway drawer can be plugged in here later." />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></AppLayout></BrowserRouter>
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />)
