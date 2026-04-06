# Codex task: Build the complete Cancer 360 UI

## Context

You are building the frontend for an NHS Federated Data Platform Cancer 360 proof-of-concept application. The backend API is already running at `http://localhost:8000` with endpoints for PTL data, pathway details, actions, dashboard metrics, and team performance. The database contains synthetic cancer patient data across 16+ tables.

This document describes every screen, table, chart, filter, drawer, and interaction in the production Cancer 360 product. Build all of it as a React application. Use the existing API endpoints where they exist, and create new API endpoints where needed. Use Recharts for charts, and Tailwind CSS for styling.

The application has a Palantir Foundry visual style: dark blue-purple navigation bar (#3b4a7c), light gray page backgrounds, white card surfaces, and a clean enterprise data platform feel. All data shown is synthetic/notional.

---

## Global layout

### Top navigation bar
- Background: dark blue-purple (#3b4a7c)
- Left side: Cancer 360 logo/icon with dropdown chevron, then four main tabs:
  - "Cancer PTL" (list icon)
  - "Cancer Actions" (clipboard icon)
  - "Service Overview" (grid icon)
  - "Team Overview" (people icon)
- A "+" button after the last tab for adding custom tabs
- Right side: "Edit" button (pencil icon, blue outline), help icon (?), notifications bell, user avatar
- The active tab has a white/highlighted background within the nav bar
- This nav bar is persistent across all screens — it never changes

### Sub-navigation
- Each main module has its own sub-header below the nav bar with:
  - Module title and "Saved module states" dropdown on the left
  - Filter controls on the right: Pathway Tags (search dropdown), Cancer Sites (search dropdown), Hospital Sites (search dropdown)
  - Some modules have additional filters like Pathway Type

### Left-hand filter/config panel
- A collapsible sidebar on the left edge of the screen (toggled by a filter icon button)
- Contains "Filters & Config" header with "Reset Filters" button
- The filter panel content varies per module (detailed below per screen)

---

## Screen 1: Landing page

When the user first opens Cancer 360 or clicks the Cancer 360 logo, show a landing page with:

- NHS Federated Data Platform logo centered at top
- A universal search bar: "Search object types and properties..." with "All" dropdown and help icon
- Four module cards in a 2x2 grid:
  - **Cancer PTL** — purple card with horizontal bar chart icon (three white bars labeled 1, 2, 3). Subtitle: "Cancer PTL Management tool"
  - **Cancer Actions** — light blue card with checklist/clipboard icon. Subtitle: "Action Management Tool"
  - **Service Overview** — pink/magenta card with donut chart icon. Subtitle: "Bottleneck Analysis and Performance Dashboard"
  - **Team Overview** — medium blue card with people/network icon. Subtitle: "Actions overview and team performance analysis"
- Right sidebar on landing page:
  - "Cancer Settings" — gear icon, subtitle "Configure cancer module"
  - "User Guides" — book icon, subtitle "User guides and documentation for Cancer 360"
- Clicking any card navigates to that module and highlights the corresponding tab in the nav bar

---

## Screen 2: Cancer PTL

This is the most complex screen. It is a wide data table with horizontally scrollable columns. The table shows one row per cancer pathway.

### PTL sub-header
- Left: "Cancer PTL" title with list icon, "Saved module states" dropdown
- Right: Pathway Tags (search), Cancer Sites (search dropdown), Hospital Sites (search dropdown)

### PTL tab bar (below sub-header)
- Horizontal tabs with counts: "Full PTL 2698", "0-28 Days 2070", "29-62 Days 574", "63+ Days 40", "105+ Days 8", "Watchlist 32"
- These are filters — clicking one filters the table to show only pathways in that age range
- Right side of tab bar: "PTL Last Updated: Sat, May 10, 2025, 7:46:50 PM" with clock icon
- Refresh button (circular arrow icon)
- "Create Action" button (green, with plus icon and dropdown chevron)

### PTL table
The table is horizontally scrollable with many columns. The user can scroll right to see additional columns. The screenshots show four different horizontal scroll positions of the same table. All these columns exist simultaneously — they are revealed by scrolling right:

**Scroll position 1 (leftmost columns):**
- Checkbox (row selector)
- Pathway Day (sortable, with sort arrows) — shows integer like 1325, 747, 467, 185
- Full Name — "Chavez, Robert", "Lucero, Stephen", etc.
- NHS Number — 10-digit number like 5936996311
- MRN — like 006736951
- Age — integer like 84, 74, 16, 31
- Cancer Site — "Gynaecology", "Colorectal", "Sarcoma", etc.
- Cancer Sub Site — "Cervix", "Ovarian", "Colon", "Soft Tissue", "Anal", etc.
- Hospital Site — "Site 1", "Site 2"
- # Open Actions — integer count like 1, 2, 3
- Latest Action — text like "Update Tracking Note", "Clinical Review Required", "Review Diagnostic Results", "Chase Histology Report", "Reschedule GA Diagnostic", "Enquiry of Sample Status"
- Recent Action Update — "Yes" (in green) or "No"
- Latest Tracking Comment — truncated text like "Patient's medication list reviewed for potential contraindications.", "MRI scan completed on 03/10; radiologist review in progress."

**Scroll position 2 (middle columns):**
- Pathway Day, Full Name, NHS Number, MRN (same as above, for context)
- Latest Tracking Comment (full text visible)
- Pathway Status — "Benign" or "Suspected" (displayed as styled badge/pill)
- 28 Day Breach Date — formatted as "Fri, Oct 22, 2021", "Tue, May 23, 2023", etc.
- 31 Day Breach Date — similarly formatted
- 62 Day Breach Date — similarly formatted. Dates that are in the past should have a subtle warning styling

**Scroll position 3 (more columns):**
- First Op Appt Attended Date — "Sun, Oct 10, 2021", "Tue, Apr 25, 2023", etc. or "No value"
- Next Op Appt Attended Date — date or "No value"
- Latest Histology Attended Date — date or "No value"
- Latest Radiology Attended Date — date or "No value"
- Latest Inpatient Encounter TCI Date — date or "No value"
- Latest MDT Status — "MDT Attended" or "MDT Booked"
- Latest IPT — date with red/brown icon badge like "2023-12-11", or "No value"

**Scroll position 4 (rightmost columns):**
- Latest Radiology Attended Date, Latest Inpatient Encounter TCI Date (continued)
- Latest MDT Status
- Latest IPT
- Tags — text like "Open actions > 5 days", "Open actions > 5 days | Actions updated in the last 48h", "Open actions > 5 days | Unreported Histology On >12 Day Old Pathway"
- Watchlist Reason — "No value" or reason text

### PTL left-hand filter panel
When the filter sidebar is open, it shows these expandable filter sections (each with a chevron to expand/collapse):

- **Excluded users for recent action updates** — text input "Updates from selected users won't be counted"
- **Flag recent action updates for the last N days** — number input (default 2) with refresh button
- **Pathway is open** — checkbox list: "No 5,537" (with blue bar), "Yes 2,698" (with blue bar, checked by default)
- **Patient** — expandable, shows "[CDM] Patient 2,635"
- **Cancer Pathway** — expandable, shows "[Cancer 360] Cancer Pathway 2,698"
- **Pathway Tags** — expandable, shows "[Cancer 360] Tagging Rule 5"
- **Watchlist** — expandable, shows "[Cancer 360] Cancer Watchlist 32"
- **Tracking Comments** — expandable, shows "[Cancer 360] Tracking Comment 33,666"
- **Cancer Actions** — expandable, shows "[Cancer 360] Cancer PTL Action 17,446"
- **Outpatient Appointments** — expandable, shows "[Sho-Like][Cancer 360] Outpatient Appointment 3,482"
- **Inpatient Procedures** — expandable, shows "[Sho-Like][Cancer 360] Inpatient Procedure 1,072"
- **Radiology Exams** — expandable, shows "[Cancer 360] Radiology 7,485"
- **Histology** — expandable, shows "[Cancer 360] Histology 5,115"
- **Test Results** — expandable, shows "[Sho-Like][Cancer 360] Test Result 26,883"
- **IPT** — expandable, shows "[Cancer 360] ITR 440"

### Row click → Pathway drawer

When any row in the PTL is clicked, a **pathway drawer** slides in from the right side of the screen, overlaying the table. The drawer has:

**Drawer header bar (dark blue-purple background):**
- Patient summary: "Lucero, Stephen | MRN: 052553838 | Gynaecology | Day 747"
- "External Links" dropdown button (green, with chain icon and chevron)
- "PTL Last Updated: Sat, May 10, 2025, 7:46:50 PM" badge (gray)
- "Create Action" button (green, right side)
- Close button (X) at far right

**Left sidebar navigation** — vertical list of section links with record counts in badges. Clicking each one shows that section's content in the main panel area:
- Pathway Details
- Actions (count badge, e.g. "7")
- Outpatient Appointments (count badge, e.g. "2")
- Inpatient Procedures (count badge, e.g. "0")
- Histology (count badge, e.g. "3")
- Radiology (count badge, e.g. "3")
- MDT Notes (count badge, e.g. "0")
- Test Results (count badge, e.g. "1")
- IPT (count badge, e.g. "1")
- Tracking Comments (count badge, e.g. "10")
- Patient

The active section is highlighted with a light blue/purple background. The count badges use green circles for sections with data.

**Drawer content — Pathway Details section:**
A two-column key-value grid showing:
- Pathway Status: badge showing "Benign" (gray) or "Suspected" (amber)
- Days Since Adjusted Pathway Start: integer
- Pathway Type: "62 Day"
- Cancer Site: "Gynaecology"
- Cancer Sub Site: "Ovarian"
- Hospital Site: "Site 2"
- Full Name, NHS Number, MRN
- Phone Number, Date Of Birth
- Adjusted Pathway Start Date, Pathway Closed Date
- 28 Day Breach Date (in boxed date display), 31 Day Breach Date, 62 Day Breach Date
- Original Pathway Start Date

Below the key-value grid:
- **Tags** section (expandable, with resize icon)
- **Pathway Milestones** — a horizontal timeline showing clinical events plotted on a month axis (AM, J, J, A, S, O, N, D, J, F, M, A, M). Events listed vertically on the left like "Gynae Rapid Access New", "Gynaecology F/Up", "Breast Screening Biopsy", "CT Thorax abdomen pelvis with contrast", etc. Gray dots mark when each event occurred on the timeline.

**Drawer content — Actions section:**
A table with columns:
- Red square icon (priority indicator)
- Title — "Chase Histology Report", "Enquiry of Sample Status", "Chase Imaging Report", "Clinical Review Required", "Bring Forward Endoscopy", "Review Diagnostic...", "Reschedule GA Diagnostic"
- Due Date — formatted dates
- Action Status — "Completed" or "Open" (Open is in green text)
- Action Detail — "CT | USS", "capsule endoscopy | F...", "Transport required | POA"
- Owner — truncated names like "Elia Be...", "Ishan D..."

When an action row is clicked, a **sub-panel** opens to the right of the action list showing:
- Action title and due date header: "Clinical Review Required | Due: Mon, Nov 13, 2023"
- "Update" dropdown button (green)
- Close button (X)
- An action history timeline with color-coded entries:
  - Green circle: "CREATE ACTION" — date, created by
  - Purple circle: "COMMENT" — date, created by, comment title "Create action", comment text
  - Purple circle: "COMMENT" — date, created by, comment title "General Comment", comment text
  - Red circle: "COMMENT" — date, created by, comment text
  - Blue circle: "ASSIGN TO USER" — date, changed by, assigned to

**Drawer content — Outpatient Appointments section:**
Table with columns: Appointment Name, Appointment Status (colored: "cancelled" in red/brown), Ordered Date, Scheduled Date, Attended Date

**Drawer content — Inpatient Procedures section:**
Table with columns: Procedure Name, Encounter Status (colored: "cancelled" in red/brown), Ordered Date, Scheduled Date, Attended Date

**Drawer content — Histology section:**
Table with columns: Histology Type (e.g. "Histology, tissue", "Non-gynaecology cytology, specimen"), Exam Status (colored: "reported" in green, "did not attend" in red), Priority ("Urgent", "Normal")
When a histology row is clicked, a **report sub-panel** opens on the right showing:
- Header: "Histology, tissue | Report Authorised: Fri, Apr 18, 2025"
- Full report text in a card: hospital name, patient name, NHS number, hospital number, referral source, clinical question, findings, conclusion, reporting clinician name and role, disclaimer text

**Drawer content — Radiology section:**
Table with columns: Radiology Exam Type (e.g. "MRI Lower leg Lt", "MRI Wrist Both", "MRI Groin Right"), Exam Status ("reported" green, "cancelled" red), Priority ("Urgent", "Normal"), Ordered Date
When a radiology row is clicked, a **report sub-panel** opens (identical format to histology reports)

**Drawer content — MDT Notes section:**
Shows MDT meeting cards, each with:
- Meeting header bar (amber/orange): "Wed, Apr 16, 2025, 5:00:00 PM | MDT Attended" with "MDT Notes 1" count and expand chevron
- Inside each meeting, note cards with colored type badges:
  - "radiology" (orange badge) — Timestamp, Text (e.g. "Imaging review")
  - "histology", "outcome", "general" — similar format

**Drawer content — Test Results section:**
Scrollable list of test result cards, each showing:
- Orange "ba" icon
- Test name in bold: "INR, blood", "Haemoglobin", "Red blood cell count, blood", "Neutrophil count, blood"
- Test Date, Value (numeric), Unit ("ratio", "g/L", "x10^12/L", "x10^9/L"), Test Value Type
- A column settings icon at bottom right

**Drawer content — IPT section:**
Table with columns: Reason for IPT ("Staging"), Sent or Received ("received"), IPT Date, IPT on Day (integer like "340"), Sending Org Name ("NEWCASTLE UPON TYNE HOSPITALS NHS FOUNDATION ..."), Receiving Org Name ("Notional Hospital")

**Drawer content — Tracking Comments section:**
- "Prepare an Example Tracking Comment" button (green, top right, pencil icon)
- Scrollable list of comment cards, each showing:
  - Created At: timestamp
  - Created By: name
  - Comment Text: full text like "MRI scan completed on 03/10; radiologist review in progress.", "Insurance pre-authorization for targeted therapy obtained on 03/18.", "Patient added to waitlist for PET scan; estimated time 2 weeks.", "HIGH RISK: Patient's lab results flagged for expedited review due to abnormal findings."

**Drawer content — Patient section:**
- Patient header: name with star icon, "[CDM] Patient" subtitle
- Three tabs: "Overview", "Diagnosis History", "Test Results"
- Overview tab shows:
  - Key-value grid: Full Name, Deceased (Yes/No badge), MRN, NHS Number, Sex, Age, Date Of Birth, Date Of Death, Phone Number, Address Line 1, Address Line 2, Postcode
  - **Activity Timeline** — horizontal timeline by specialty with Specialties search dropdown. Shows events plotted as colored dots with legend:
    - Dark circle: Inpatient Encounter
    - Green circle: First/New Outpatient Appointment
    - Blue circle: Follow-Up Outpatient Appointment
  - Below the timeline: two columns:
    - **Outpatient Appointments** — list or "No outpatient appointments found for this patient"
    - **Inpatient Encounters** — cards showing encounter details: title (specialty + name), TCI Date, Priority badge (e.g. "4 (more than 12 weeks)"), Specialty Name, Primary Consultant Name (highlighted badge), Intended Primary Procedure Description, Intended Primary Procedure Free Text

---

## Screen 3: Cancer Actions

### Actions sub-header
- "Cancer Actions" title with clipboard icon, "Saved module states" dropdown
- Two sub-tabs: "Actions List" (table icon) and "Recent Action Updates" (clock icon)
- Right: Cancer Site search, Hospital Site search

### Actions KPI cards (top row)
Four cards in a horizontal row:
- **My Actions**: large number (e.g. "16") on white background with blue info icon
- **Actions for my team(s)**: large number "268" with subtitle "54 Awaiting assignment" on amber/orange background
- **Escalated actions for my team(s)**: "28" on red/coral background
- **All actions**: "5775" on white background with blue info icon

### Actions toolbar
- Tab toggles: "all actions 16", "watchlist only 1"
- Action buttons (right side, colored): "Add Comment" (gray), "Assign" (blue), "Complete" (green), "Escalate" (red), "Revoke" (coral/red), "Reassign team" (blue outline)

### Actions table (Actions List view)
Horizontally scrollable table, similar to PTL. Shows multiple scroll positions:

**Scroll position 1:**
- Checkbox, Due Date (sortable), Title (with red square priority icon), Action Detail Summary, Pathway Day, Patient (dropdown checkmark), Cancer Site, MRN, NHS Number, Action Status ("Open" or "Escalated" in colored text), Days Open (integer), Pathway Is Open (true/false), Pathway Status ("Suspected")

**Scroll position 2:**
- Due Date, Title, Action Detail Summary, Pathway Day, Patient, Pathway Status, Latest Action Comment, Owner, Team Name ("Radiology Booking"), 28 Day Breach Date

**Scroll position 3:**
- Due Date, Title, Action Detail Summary, Pathway Day, Patient, 28 Day Breach Date, 31 Day Breach Date, 62 Day Breach Date, First Op Appt Attended Date, Next Op Appt Attended Date, Latest Radiology Attended Date, Latest Histology Attended Date, Latest IP Procedure TCI Date

### Actions left-hand filter panel
When open:
- **Action Description** — search dropdown
- **Action Detail** — search dropdown
- **Action Is Open** — dropdown (default "True X")
- **Action Status** — search dropdown
- **Team Name** — search dropdown
- **Owner** — search text
- **Due Date** — Date range selector with "Relative to today" toggle, After (inclusive) start date, Before (inclusive) end date
- **Action Created Date** — same date range format with GMT+1 timezone dropdown
- **Patient** — expandable "[CDM] Patient 15"
- **Cancer Pathway** — expandable "[Cancer 360] Cancer Pathway 15"
- **Action Comments** — expandable "[Cancer 360] Cancer PTL Action Comment 33"
- **All Action History** — expandable "[Cancer 360] Cancer PTL Action Changelog 38"
- **Linked Tracking and Diagnostics to Pathway** — expandable "[Cancer 360] Cancer PTL Helper 15"
- "Add filter" button at bottom

### Recent Action Updates view
When "Recent Action Updates" sub-tab is selected:
- Filter bar at top: FROM (date+time with GMT+1), TO (date+time with GMT+1), UPDATE TYPE (multi-select "Filter to 1 or more update types..."), EXCLUDE UPDATES MADE BY (multi-select)
- List of update cards, each showing:
  - Colored icon (purple for Comment Added, green for Created, blue for Assigned Owner)
  - Title text: "Comment Added — Urgent Review Required — Bond, Anna | MRN: 040311828 | Haematology | Day -9"
  - Timestamp: "Mon, May 19, 2025, 3:30:23 PM"
  - Expand chevron on right
- When expanded, shows:
  - Patient info bar: "Bond, Anna | MRN: 040311828 | Haematology | Day -9" with red icon
  - Comment detail: type badge "General Comment", Comment Text content
  - Below the expanded card, the full action detail view opens with:
    - Action toolbar buttons: Add Comment, Assign, Complete, Reopen, Escalate, Revoke, Reassign team
    - Action summary: Title, Action Detail, Days Open (green background), Due Date (red background)
    - Two columns: **Action History** (timeline of events) and **Action Details** (Pathway, Status, Team, Owner, Due Date, Last Updated, Last Updated By)
- Pagination: "Showing 1 - 30 of 10,000 items" with page controls

### Single action view (row click from Actions List)
When a row is clicked in the Actions List, a drawer opens from the right similar to the pathway drawer, showing:
- Header: "Chase Imaging Report — Howard, Aaron | MRN: 074893555 | Head and Neck | Day 21" with "External Links" dropdown
- Action toolbar: Add Comment, Assign, Complete, Escalate, Revoke, Reassign team
- Summary card: Title ("Chase Imaging Report"), Action Detail ("Open MRI, Guided Biopsy"), Days Open ("7" on green), Due Date ("Mon, Apr 28, 2025" on red)
- Two columns:
  - **Action History** — timeline: CREATE ACTION (green), COMMENT (purple), ASSIGN TO USER (blue)
  - **Action Details** — Pathway info, Status "Open", Team "Radiology Booking", Owner, Due Date, Last Updated, Last Updated By
- Below this, the **pathway drawer** opens within the same panel (embedded), showing the same Pathway Details, Actions, Appointments, etc. sections as described above

---

## Screen 4: Service Overview

### Service Overview sub-header
- "Service Overview" title with grid icon, "Saved module states" dropdown
- Filters: Pathway Type (search), Tags (search dropdown), Cancer Site (search dropdown), Hospital Site (search dropdown)

### Left sidebar: "Monthly performance" toggle
- A vertical sidebar tab on the left edge labeled "Monthly performance" (rotated text) with expand arrows
- When expanded, shows monthly performance cards (see Monthly Performance section below)

### Overview section (main content)
Header: blue icon with "Overview" text, hamburger menu (three lines) on right

#### PTL Size KPI cards
Five cards in a row:
- PTL Size: 2698
- 0-28 Day: 2070
- 29-62 Day: 574
- 63+: 40
- Watchlist Pathways: 32

#### Charts row 1 (side by side)
**Left chart: # of Open Pathways x Cancer Site**
- Toggle buttons: "Pathway age" (selected) | "Cancer subsite"
- Stacked bar chart with cancer sites on X axis (Urology, Gynaecology, Skin, Upper GI, Colorectal, Brain, Head and Neck, Sarcoma, Haematology, Breast, Lung, ADOC, CUP, Paediatric)
- Each bar shows count at top (520, 320, 244, 243, 242, 229, 209, 193, 189, 187, 131, 125, 107, etc.)
- Stacked segments colored by pathway age: 0-28 (pink/magenta), 29-62 (olive/green), 63+ (teal), No Value (purple)
- Legend with color key, "Default" dropdown
- Export/screenshot icon

**Right chart: Trending PTL Size**
- Line chart with date range selector: "Pathways starting from: Sat, May 11, 2024" and "End date"
- Multiple lines: Total open pathways (dark blue), 0-28 open pathways (pink), 29-62 open pathways (olive), 63+ open pathways (teal)
- Y axis: Count (0 to 2800), X axis: dates by week/month

#### Charts row 2 (side by side)
**Left chart: # Open Pathways By Tag**
- Toggle: Pathway Age | Cancer Site
- Stacked bar chart with tags on X axis: "Actions updated in the last 48h", "Unreported Histology On >12 Day Old Pathway", "Open actions > 5 days", "Recent radiology report available", "High Risk"
- Same color scheme: 0-28, 29-62, 63+, No Value

**Right chart: # Open Pathways By Pathway Type**
- Toggle: Pathway Age | Cancer Site
- Stacked bar chart with pathway types: 62 Day, Upgrade, Screening, Breast Symptomatic

#### Charts row 3 (side by side)
**Left chart: # of Open Actions by Type**
- Donut/pie chart showing action type distribution
- Segments labeled: "Chase Imaging Report: 14%", "Chase Endoscopy Report: 7.4%", "Chase Histology...", "Enquiry of Sample...", "Clinical Review Required: 8%", "Reschedule GA Diagnostic: 8.3%", "Review Diagnos...", "Cancel OP Diagnostic...", "Update Tracking...", "Urgent Review Required: 8.7%", "Book Surgery..."
- Legend with all action types listed
- "Total open actions: 3738"

**Right chart: # of Open Actions by Team**
- Horizontal stacked bar chart
- Teams on Y axis: Admissions Managers, Hospital Labs/Pathology, Cancer Services - Senior..., Clinical Leads, Endoscopy Managers, Admissions, Histology Team, Endoscopy Bookings Team, Radiology Booking, CNS, Outpatient Booking Team..., Radiology Managers, Cancer Services - MDT Coordinators
- Segments colored by action age: Open (green), 3-5 Days (yellow), 5-10 Days Old (orange), 10+ Days Old (red)
- Numbers shown within segments
- Total at end of each bar
- "Total open actions: 3738"

#### Charts row 4 (side by side)
**Left chart: Trending Pathway Close Day**
- KPI cards: "Current open pathways mean age: Day 21", "Mean close day for last month: Day 35" (red background)
- Line chart: Y axis "Average of Days Since Adjusted Pathway Start" (20-46), X axis dates (2022-2025)
- Dashed red reference line at 28 days

**Right chart: Trending Action Volume**
- Line chart: Y axis "Count" (-5000 to 55000), X axis dates (2021-2025)
- Two lines: Actions Created (teal), Actions Closed (purple)

### Monthly performance sidebar (when expanded)
Shows four columns of performance cards, each card with a colored header and metric rows:

**Column 1: First OPA** (blue header)
- Order Day: Day 3
- Scheduled Day: Day 4
- Attended Day: Day 10
- Turn Around Time: 7 Days

**Column 2: IP Diagnostics** (green header)
- Order Day: Day 4
- Scheduled Day: Day 5
- Attended Day: Day 5
- Turn Around Time: 1 Days

**Column 3: Histology** (coral/orange header)
- Order Day: —
- Scheduled Day: —
- Attended Day: Day 8
- Report Day: Day 16
- Report Turn Around Time: 8 Days
- Turn Around Time: —

**Column 3 also shows: Radiology** (teal header)
- CT x, MRI x, US x, X-ray x filter chips
- Order Day: Day 2
- Scheduled Day: Day 3
- Attended Day: Day 8
- Report Day: Day 16
- Report Turn Around Time: 8 Days
- Turn Around Time: 14 Days

**Column 3 also: OP Diagnostics** (purple header), **Endoscopy** (yellow header), **Follow-up OPA** (green header)

**Column 4 shows:**
- Attended Day: Day 9, Turn Around Time: 5 Days (top card)
- **IPT** (purple header): Received/Sent tabs, # of received IPTs: 239, # received before day 38: 230, # received after day 38: 9, %: 96%
- **Treatment** (purple header): Order Day: Day 10, Scheduled Day: Day 10, Attended Day: Day 39, Turn Around Time: 29 Days

Each metric has an info (i) icon for tooltips.

### Service Overview drill-down screens
When any of the monthly performance cards is clicked, it expands into a full-width detail view with:

**Header with the metric category name** (e.g. "First OPA", "Radiology", "Histology", etc.)

**Rolling Monthly Averages KPI row:**
- Cards showing Order Day, Scheduled Day, Attended Day, Report Day (for path/rad), Report Turn Around Time, Turn Around Time
- With info icons and tooltips (e.g. "Mean scheduled day for diagnostics completed in the last month")

**Metric Category filter:** pill/chip selector (e.g. "First OPA x", "IP Diagnostic x", "Histology x", "Endoscopy x", "OP Diagnostic x")

**Trending section:**
- Toggle: "Key events" | "Turn around time"
- Multi-line chart: Y axis "Mean Pathway Day" or "Pathway Day", X axis monthly dates (June 2024 through May 2025)
- Lines for Order Day (pink), Scheduled Day (olive/yellow), Attended Day (teal/green), Report Day (purple, for path/rad only)
- Legend with color key

**Below the chart — status tabs with counts:**
- "Unscheduled [count]", "Scheduled [count]", "Attended [count]", "Report Available [count]" (green, for path/rad), "Cancelled/DNA [count]"
- "Create Action" button (green, right side)

**Data table below the chart:**
Each drill-down has a specific table. Examples:

**First OPA table columns:** Pathway Day, Full Name, NHS Number, MRN, Diagnostic Title Value, Clean Diagnostic Status, Ordered Date, Scheduled Date (sortable with checkmark), Attended Date, Reported Date, # Open Actions, Latest Action, 28 Day Breach Date

**Radiology table columns:** Same as above plus modality-specific details, CT/MRI/US/X-ray filter chips in the metric category

**IP Diagnostics table columns:** Similar with procedure-specific details

**Histology table columns:** Pathway Day, Full Name, NHS Number, MRN, Diagnostic Title Value, Clean Diagnostic Status, Attended Date, Reported Date, # Open Actions, Latest Action, 28 Day Breach Date, 31 Day Breach Date, 62 Day Breach Date

**Endoscopy table columns:** Same pattern with endoscopy-specific data

**Treatment table columns:** Diagnostic Title Value shows procedure descriptions like "Medical termination of pregnancy | Medic", "Left hemicolectomy and ileostomy HFQ", etc.

**IPT section (within Service Overview):**
- Rolling Monthly Averages split into two columns: Received IPTs and Sent IPTs
- KPI cards: # of received IPTs (239), # received before day 38 (230), # received after day 38 (9), % received before day 38 (96%) — mirrored for Sent
- Trending chart: bar chart by "Tertiary Received Date" (2022-2025), segments colored "Received On or Before Day 38" (blue) and "Received After Day 38" (pink)
- Below: "IPTs for open Pathways" with toggle "Received IPTs" | "Sent IPTs", Reason(s) for IPT search filter, Create Action button
- Table columns: Pathway Day, Full Name, NHS Number, MRN, Tertiary Date, Tertiary Reason, Sending Org Name, Receiving Org Name, Tertiary Sending Comment, Tertiary Return Comment, Tertiary Sent Date, Tertiary Received Date

---

## Screen 5: Team Performance

### Team Performance sub-header
- "Team Performance" title with people icon, "Saved module states" dropdown
- Filters: Pathway Tags (search dropdown), Cancer Site (search dropdown), Hospital Site (search dropdown)

### Top KPI summary cards (row of 5)
- **Most Open 10 Day Old Actions** (red flag icon, red header): "Team with the most open actions over 10 days old". Top team highlighted in red badge: "Admissions (196 actions)". Then numbered list: "2. Cancer Services - Senior Management (190 actions)", "3. Admissions Managers (181 actions)"
- **Most Completed Actions** (star icon, green header): "Team who completed the most actions this week". Top: "Histology Team (1067 actions)", "2. Hospital Labs/Pathology (1056 actions)", "3. Outpatient Booking Team (COBT) (1043 actions)"
- **Most Sent Actions** (arrow icon, blue header): "Person who sent the most actions this week". Top: "Elia Benhamou (7395 actions)", "2. Will Carroll (548 actions)", "3. Ollie Ursell (526 actions)"
- **Number of Open Actions**: large "3738 Actions" on white with red text
- **Mean Age of Open Actions**: large "11.4 Days" on red background

### Team Metrics table
Table with columns:
- Title (with colored square icon): team names — Admissions, Admissions Managers, CNS, Cancer Services - MDT Coordinators, Cancer Services - Senior Management, Clinical Leads, Endoscopy Bookings Team, Endoscopy Managers, Histology Team, Hospital Labs/Pathology, Outpatient Booking Team (COBT), Radiology Booking, Radiology Managers, Cancer Services - MDT Coordinators
- Open Actions (sortable)
- Escalated Actions
- 0-2 Days
- 3-10 Days
- 10+ Days
- Completed This Week

When a team row is clicked, a **Team Performance Breakdown** drawer opens showing:
- "Actions for: Cancer Services - MDT Coordinators" title
- KPI row: Open (277), Escalated (19), 0-2 Days Old (49), 3-10 Days Old (97), 10+ Days Old (124), Closed This Week (432)
- Tabs: "all actions 277" | "watchlist only 2"
- Same action toolbar buttons
- Full actions table for that team

### Charts section (below Team Metrics table)
**Left chart: # of Open Actions by Type** — same donut/pie chart as Service Overview

**Right chart: # of Open Actions by Team** — same horizontal stacked bar chart as Service Overview (with same Open / 3-5 Days / 5-10 Days Old / 10+ Days Old color coding)

**Below: # of Open Actions by Cancer Site**
- Horizontal stacked bar chart
- Cancer sites on Y axis: Urology, Gynaecology, Skin, Upper GI, Brain, Colorectal, Head and Neck, Haematology, Sarcoma, Breast, Lung, ADOC, CUP, Paediatric
- Same color segments with numbers
- Collapse/expand control (<<)

**Trending Action Volume chart** — same as Service Overview (Actions Created vs Actions Closed line chart over 2021-2025)

---

## Implementation notes for Codex

1. **Routing**: Use React Router. The nav bar tabs route to `/ptl`, `/actions`, `/service-overview`, `/team-overview`. The landing page is at `/`.

2. **State management**: Use React context or zustand for global state (selected filters, active pathway, etc.).

3. **Pathway drawer**: This is a slide-in panel component that appears on the right side and overlays the page content. It should be reusable because it appears in Cancer PTL, Cancer Actions, and Team Overview contexts with the same content.

4. **Action drawer**: Similar pattern to pathway drawer but for single action detail view.

5. **Horizontally scrollable tables**: Use a div with `overflow-x: auto` for the wide data tables. The column headers should be sticky/frozen for the first few columns (checkbox, pathway day, full name).

6. **Charts**: Use Recharts for all charts. The stacked bar charts, line charts, donut/pie charts, and horizontal bar charts are all Recharts components.

7. **Data**: Connect to the existing API at `http://localhost:8000/api/v1/`. Where endpoints don't exist for specific views (like monthly performance metrics), create new API endpoints or compute the data client-side from existing endpoints.

8. **Color scheme**: 
   - Nav bar: #3b4a7c
   - Green buttons: #4caf50
   - Red/escalated: #d32f2f
   - Amber/warning: #ef6c00
   - Blue info: #1a73e8
   - Gray backgrounds: #f5f5f5
   - White card surfaces: #ffffff
   - Pathway age colors: 0-28 pink (#e91e63), 29-62 olive (#8bc34a), 63+ teal (#00bcd4)
   - Action age: Open green, 3-5 Days yellow, 5-10 Days orange, 10+ Days red

9. **All data is synthetic**. Add a disclaimer banner or footnote: "All data shown is synthetic and does not relate to real people."

10. **Responsive considerations**: The app is designed for wide desktop screens (1920px+). Horizontal scrolling is expected for the data tables. The pathway drawer should be approximately 60-70% of screen width.

11. **The pathway drawer is the same component everywhere**. Whether opened from the PTL, from Cancer Actions, from Service Overview, or from Team Overview — it shows the same pathway detail with the same sections. Build it once as a reusable component.

12. **Infer click-through behavior from the screenshot sequence**: 
    - Landing page cards → navigate to that module
    - PTL row → open pathway drawer
    - Action row → open action detail, which embeds pathway drawer
    - Team Metrics row → open team breakdown drawer with filtered actions
    - Monthly performance card → expand to full drill-down view
    - Histology/Radiology row in pathway drawer → open report sub-panel
    - Action row in pathway drawer → open action history sub-panel
    - IPT row → shows IPT detail inline

13. **Build all screens even if the API doesn't have the endpoint yet**. Use mock data where needed and add a TODO comment for the API endpoint. The most important thing is that every screen, table, chart, and interaction from the screenshots is present and functional with synthetic data.
