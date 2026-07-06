# Blockchain Privacy Platform — Complete Roadmap

> **Goal**: Implement audit trail, overhaul reporting, add visualizations, enhance admin analytics, notifications, and data integrity across the entire platform.

---

## Phase 1 — Audit Foundation 🔐

**Goal**: Build a complete audit trail system — model, middleware, signals, and admin viewer.

### 1.1 Audit Model
- [x] Create `audit` Django app
- [x] `AuditLog` model with fields: `user` (FK User, nullable), `action_type` (choices: CREATE, UPDATE, DELETE, RUN, APPROVE, REJECT, LOGIN, LOGOUT, EXPORT, DOWNLOAD), `content_type` (CharField — model name), `object_id` (IntegerField), `object_repr` (CharField), `changes` (JSONField — before/after diff), `ip_address` (GenericIPAddressField), `request_method` (CharField), `url` (CharField), `timestamp` (DateTimeField auto_now_add)
- [x] Add indexes on `(content_type, object_id)`, `(user, timestamp)`, `action_type`
- [x] Register in admin

### 1.2 Audit Middleware
- [x] `audit/middleware.py` — `AuditMiddleware` capturing all requests/responses
- [x] Auto-log all mutating actions (POST/PUT/DELETE) — record IP, URL, method, user agent
- [x] Register middleware in `settings.py`

### 1.3 Audit Mixin & Signals
- [x] `audit/mixins.py` — `AuditableMixin` for models needing granular change tracking
- [x] Override `save()` and `delete()` to log changes automatically
- [x] Connect `post_save`/`post_delete` signals to: Experiment, Dataset, Report, User, PrivacyTechnique, ExperimentComparison
- [x] Auto-log experiment status transitions (pending→running→completed/failed)
- [x] Auto-log dataset approvals/rejections
- [x] Auto-log user logins/logouts (via signals on `user_logged_in`/`user_logged_out`)
- [x] Auto-log report generation and downloads

### 1.4 Audit Views & URLs
- [x] `audit/views.py`:
  - [x] `audit_log_list` — paginated, filterable by action_type, content_type, date range, user
  - [x] `audit_log_detail` — single entry with full before/after diff display
  - [x] `audit_object_history` — all changes for a specific object (`?content_type=Experiment&object_id=5`)
- [x] `audit/urls.py` — routes: `/audit/`, `/audit/<pk>/`, `/audit/object-history/`
- [x] Integrate into root `urls.py` under `/audit/`

### 1.5 Audit Templates
- [x] `audit/templates/audit/audit_list.html` — table with action badges (color-coded), date range picker, type filter dropdown, search box
- [x] `audit/templates/audit/audit_detail.html` — JSON diff view with before/after side-by-side
- [x] `audit/templates/audit/partials/_audit_filters.html` — reusable filter bar component

### 1.6 Audit Management Commands
- [x] `python manage.py purge_audit_logs --days 90` — delete logs older than N days
- [x] `python manage.py export_audit_logs --start --end --out export.json` — export to JSON

### 1.7 Logging Configuration
- [x] Add `LOGGING` dict in `settings.py`:
  - [x] `audit` logger → `logs/audit.log`
  - [x] `experiments` logger → `logs/experiments.log` (run start/end/fail)
  - [x] `reports` logger → `logs/reports.log` (generate/download)
  - [x] `error` logger → `logs/error.log` (exceptions)
  - [x] Console handler for development
  - [x] Rotating file handlers: 10 MB per file, 5 backups each

---

## Phase 2 — Experiment Results & Visualization 📊

**Goal**: Transform bare metric tables into rich, interactive visualizations and dashboards.

### 2.1 Results Dashboard
- [x] New view + URL at `/experiments/results/`
- [x] Aggregate statistics cards: total experiments, avg privacy score, avg accuracy, total compute time
- [x] Privacy score trend line chart (by date of completion)
- [x] Technique comparison radar/spider chart (6 axes)
- [x] Success/failure pie chart by status
- [x] Filter bar: date range, technique type, dataset

### 2.2 Visualization Engine
- [x] Create `experiments/visualization.py`:
  - [x] `generate_comparison_chart(experiments, chart_type)` — grouped bar chart
  - [x] `generate_radar_chart(experiments)` — multi-axis radar
  - [x] `generate_trend_chart(experiments_qs)` — time-series line chart
  - [x] `generate_privacy_breakdown(experiment)` — per-metric breakdown
  - [x] All return base64-encoded PNG/SVG for embedding
- [x] Requirements: add `matplotlib` (and optionally `plotly` for interactive)

### 2.3 Enhanced Experiment Detail View
- [x] Add performance scatter plot: execution_time vs throughput
- [x] Add privacy breakdown bar chart (sub-metrics from `metrics` JSONField)
- [x] Add "Historical Runs" section: table of previous runs with same technique
- [x] Add "Configuration Impact" — show current config params and their effect on scores
- [x] Add "Export This Experiment" button — download as CSV/JSON
- [x] Add "Generate Report" quick button — pre-selects this experiment in report form

### 2.4 Fix & Enhance Comparison Detail
- [x] **BUG FIX**: Replace broken `{% forloop.first %}` logic — actually compute:
  - [x] Best privacy score (max)
  - [x] Fastest execution time (min)
  - [x] Best accuracy (max)
  - [x] Best throughput (max)
- [x] Add radar chart comparing all techniques across 6 axes
- [x] Add grouped bar charts per metric
- [x] Add ranking table with color-coded cells (green=best, red=worst)
- [x] Add per-technique score breakdown (expandable accordion with sub-metrics)
- [x] Add "Download Comparison" button (PDF/CSV)

### 2.5 Templates for Phase 2
- [x] `experiments/templates/experiments/results_dashboard.html`
- [x] `experiments/templates/experiments/partials/_metric_charts.html`
- [x] `experiments/templates/experiments/partials/_comparison_charts.html`
- [x] Update `experiment_detail.html` with chart sections
- [x] Update `comparison_detail.html` with proper best/worst logic and charts

---

## Phase 3 — Reporting Overhaul 📄

**Goal**: From primitive JSON dumps to professional multi-format reports with scheduling, templates, and sharing.

### 3.1 PDF Report Generation
- [x] Add `reportlab` to `requirements.txt`
- [x] Implement `generate_pdf_report(report)`:
  - [x] Cover page: title, user, organization, date, report type
  - [x] Table of contents
  - [x] Executive summary section (natural language)
  - [x] Methodology section: technique descriptions, config params
  - [x] Results section: per-experiment detail pages with metrics tables
  - [x] Comparison section: side-by-side with charts
  - [x] Recommendations section: data-driven (best for privacy, best for performance)
  - [x] Raw data appendix
  - [x] Footer: page numbers, generation timestamp, platform branding
- [x] Integrate into `report_generate` flow — actually generate PDF when `file_format='pdf'`

### 3.2 Enhanced Report Content
- [x] Restructure `Report.content` from flat JSON dump to structured sections:
  - [x] `executive_summary` (generated from summary logic)
  - [x] `methodology` (technique descriptions with links)
  - [x] `results` (per-experiment with all metrics)
  - [x] `comparison` (side-by-side with rankings)
  - [x] `recommendations` (data-driven)
  - [x] `raw_data` (embedded CSV)
- [x] Update `generate_report_content()` to produce structured dict

### 3.3 Report Scheduling
- [x] `ReportSchedule` model:
- [x] `user` (FK User), `name`, `report_type`, `file_format`
- [x] `schedule_frequency` (choices: daily, weekly, monthly)
- [x] `schedule_day` (IntegerField — day of week/month)
- [x] `experiments` (ManyToManyField or filter criteria JSONField)
- [x] `last_run` (DateTimeField), `next_run` (DateTimeField), `is_active` (BooleanField)
- [x] `auto_generate` (BooleanField — run immediately when condition met)
- [x] `python manage.py process_scheduled_reports` — checks `next_run`, generates report, updates schedule
- [x] Views: list schedules, create/edit schedule, toggle active, view history
- [x] Templates: schedule list, form, detail with past runs

### 3.4 Report Templates
- [x] `ReportTemplate` model:
  - [x] `name`, `description`, `is_public` (BooleanField)
  - [x] `user` (FK User, nullable for system templates)
  - [x] `sections` (JSONField — which sections to include: summary, methodology, results, comparison, recommendations, raw)
  - [x] `layout` (JSONField — header text, footer text, colors, logo)
- [x] Users select a template when generating reports
- [x] System seed: 3 default templates ("Full Report", "Executive Summary", "Technical Deep Dive")
- [x] `python manage.py seed_report_templates` — load defaults

### 3.5 Report Sharing
- [x] `ReportShare` model:
  - [x] `report` (FK Report), `shared_by` (FK User)
  - [x] `shared_with_user` (FK User, nullable)
  - [x] `share_token` (UUIDField, unique — for anonymous links)
  - [x] `expires_at` (DateTimeField, nullable), `max_access_count` (IntegerField, nullable)
  - [x] `permissions` (choices: view_only, download)
  - [x] `last_accessed` (DateTimeField), `access_count` (IntegerField)
- [x] Share link generation: `/share/<token>/`
- [x] Views: share report (modal/form), manage shares, revoke share
- [x] Public view: token-based, no login required, shows report summary + download

### 3.6 Export Enhancements
- [x] Add XLSX export via `openpyxl` — multiple sheets (Summary, Details, Raw Data)
- [x] Add combined ZIP export — contains PDF + CSV + JSON together
- [x] Add chart export — generate and embed chart images in all formats

### 3.7 Templates for reporting overhaul
- [x] `reports/templates/reports/report_schedule_list.html`
- [x] `reports/templates/reports/report_schedule_form.html`
- [x] `reports/templates/reports/report_template_list.html`
- [x] `reports/templates/reports/report_template_form.html`
- [x] `reports/templates/reports/share_report.html`
- [x] `reports/templates/reports/shared_view.html`
- [x] Update `report_detail.html` with proper section rendering
- [x] Update `report_generate.html` with template selection
- [x] Update `report_generate.html` with scheduling option

---

## Phase 4 — Admin & System Analytics 🛠️

**Goal**: Turn the minimal admin panel into a full operations dashboard.

### 4.1 Enhanced System Reports
- [x] **Time-series analysis**:
  - [x] Experiment volume over time (daily/weekly/monthly buckets)
  - [x] Success rate over time line chart
  - [x] Average scores over time trend
- [x] **User analytics**:
  - [x] Active users / new users per month (bar chart)
  - [x] Top 10 experimenters (leaderboard table)
  - [x] User type distribution (pie chart)
  - [x] Experiments per user histogram
- [x] **Dataset analytics**:
  - [x] Approval rate (approved vs rejected pie)
  - [x] Average approval time (hours/days)
  - [x] Dataset type distribution (bar chart)
  - [x] Upload volume over time
- [x] **Technique analytics**:
  - [x] Usage frequency per technique (bar chart)
  - [x] Average performance comparison (grouped bar: privacy_score, accuracy, throughput)
  - [x] Success rate per technique
- [x] **System health**:
  - [x] Experiment failure rate over time
  - [x] Average execution time trend
  - [x] Most common error messages (word cloud or frequency table)

### 4.2 Admin Audit Viewer
- [ ] New view at `/admin-panel/audit/`:
  - [ ] Full audit log table (all users, all actions)
  - [ ] Advanced filters: date range, action type, content type, user, search
  - [ ] Bulk actions: export selected, delete old
- [ ] `/admin-panel/audit/user/<pk>/` — audit trail for specific user
- [ ] `/admin-panel/audit/object/<content_type>/<pk>/` — audit trail for specific object
- [ ] Template: `admin_panel/templates/admin_panel/audit_logs.html`

### 4.3 Admin Notifications
- [ ] `AdminNotification` model:
  - [ ] `message` (TextField), `type` (choices: info, warning, danger, success)
  - [ ] `link` (URLField, nullable), `is_read` (BooleanField), `created_at`
  - [ ] Auto-create on: new dataset pending, experiment failure rate spike, new user registration
- [ ] Admin dashboard header shows unread badge + dropdown with latest 5
- [ ] Full page: `/admin-panel/notifications/` — list all, mark read, mark all read

### 4.4 System Metrics
- [ ] `SystemMetric` model:
  - [ ] `metric_name` (CharField), `metric_value` (FloatField), `recorded_at` (DateTimeField)
  - [ ] Captures: active_users, experiments_per_hour, avg_response_time, error_rate
- [ ] `python manage.py record_system_metrics` — run via cron every 15 minutes
- [ ] Display metric trends in admin dashboard

### 4.5 Error Tracking
- [ ] `ExperimentErrorReport` model:
  - [ ] `experiment` (FK), `technique` (FK), `error_message`, `traceback` (TextField)
  - [ ] `resolved` (BooleanField), `resolved_by` (FK User, nullable), `resolved_at` (DateTimeField)
  - [ ] `resolution_notes` (TextField)
- [ ] Auto-create on experiment failure (in the except block of `experiment_run`)
- [ ] Admin view: list unresolved errors, mark as resolved with notes

### 4.6 Templates for Phase 4
- [ ] Update `admin_panel/templates/admin_panel/system_reports.html` — full analytics
- [ ] `admin_panel/templates/admin_panel/audit_logs.html`
- [ ] `admin_panel/templates/admin_panel/error_reports.html`
- [ ] `admin_panel/templates/admin_panel/partials/_time_series_chart.html`
- [ ] `admin_panel/templates/admin_panel/partials/_user_analytics.html`
- [ ] `admin_panel/templates/admin_panel/partials/_technique_analytics.html`
- [ ] Update `admin_panel/templates/admin_panel/dashboard.html` — notification badge, more stats

---

## Phase 5 — Notifications System 🔔

**Goal**: Universal notification system across all user actions.

### 5.1 Notification Model
- [ ] `Notification` model:
  - [ ] `recipient` (FK User), `actor` (FK User, nullable)
  - [ ] `verb` (CharField choices: experiment_completed, experiment_failed, dataset_approved, dataset_rejected, report_ready, report_shared, comparison_shared)
  - [ ] `description` (TextField)
  - [ ] `action_url` (URLField or CharField — relative path)
  - [ ] `is_read` (BooleanField default False), `read_at` (DateTimeField, nullable)
  - [ ] `created_at` (DateTimeField auto_now_add)

### 5.2 Notification Triggers
- [ ] Experiment completes → notify owner with link to detail
- [ ] Experiment fails → notify owner with link to error
- [ ] Dataset approved/rejected → notify uploader with admin notes
- [ ] Report generation completes → notify creator with download link
- [ ] Report shared → notify recipient (if user exists)
- [ ] Dataset pending approval → notify all admin users

### 5.3 Notification Views & URLs
- [ ] `/notifications/` — list all, filter by read/unread
- [ ] `/notifications/mark-read/<pk>/` — mark single as read
- [ ] `/notifications/mark-all-read/` — mark all as read
- [ ] `/notifications/unread-count/` — JSON endpoint for badge count (for AJAX polling)
- [ ] Template filter: `{% notification_badge request.user %}`

### 5.4 Notification UI
- [ ] Header dropdown in `base.html` — bell icon with count badge
- [ ] Dropdown shows latest 5 notifications with relative timestamps
- [ ] Unread indicator (bold text + blue dot)
- [ ] Full page at `/notifications/` with pagination

### 5.5 Templates for Phase 5
- [ ] `notifications/templates/notifications/list.html`
- [ ] `notifications/templates/notifications/partials/_dropdown.html`
- [ ] `notifications/templates/notifications/partials/_item.html`
- [ ] Update `base.html` — add notification dropdown to navbar

---

## Phase 6 — Data Integrity, Export & Polish ✨

**Goal**: Ensure data quality, add bulk operations, write tests.

### 6.1 Management Commands
- [ ] `python manage.py audit_consistency_check` — verify all FK relationships intact, no orphaned records
- [ ] `python manage.py report_data_fix` — fix null accuracy scores, recalculate summaries
- [ ] `python manage.py generate_missing_reports` — for completed experiments with no report
- [ ] `python manage.py sync_audit_metrics` — recalculate system metrics from raw experiment data
- [ ] `python manage.py fix_orphaned_files` — clean up media files without DB records

### 6.2 Model Improvements
- [ ] `Report.generated_at` — separate from `created_at`, tracks last file generation time
- [ ] `Experiment.configuration_snapshot` — deep copy of technique params at run time
- [ ] `AuditLog.object_repr` — populate automatically via `save()` override
- [ ] Add `Meta.unique_together` or constraints where missing

### 6.3 Bulk Export
- [ ] `/export/experiments/` — export all user's experiments as CSV/JSON/XLSX
- [ ] `/export/reports/` — export report metadata as CSV/JSON
- [ ] Date range filtering, technique filtering, format selection
- [ ] Zip download for multi-file exports

### 6.4 Shareable Result Links
- [ ] Token-based sharing for individual experiment results
- [ ] `/share/experiment/<token>/` — public view of experiment (no login)
- [ ] Uses same `share_token` logic from report sharing (Phase 3.5)

### 6.5 Testing
- [ ] Write tests for `AuditLog` model and middleware
- [ ] Write tests for report generation (all formats)
- [ ] Write tests for visualization functions
- [ ] Write tests for notification triggers
- [ ] Write tests for management commands
- [ ] Aim for >70% coverage on new code

### 6.6 Templates for Phase 6
- [ ] `export/templates/export/export_page.html`
- [ ] `share/templates/share/experiment_view.html`

---

## File Inventory — All New Files by Phase

### Phase 1
```
audit/
├── __init__.py
├── models.py
├── middleware.py
├── mixins.py
├── views.py
├── urls.py
├── forms.py
├── tests.py
├── apps.py
├── templates/audit/
│   ├── audit_list.html
│   ├── audit_detail.html
│   └── partials/_audit_filters.html
└── management/commands/
    ├── purge_audit_logs.py
    └── export_audit_logs.py
```

### Phase 2
```
experiments/
├── visualization.py
└── templates/experiments/
    ├── results_dashboard.html
    └── partials/
        ├── _metric_charts.html
        └── _comparison_charts.html
```

### Phase 3
```
reports/
├── templates/reports/
│   ├── report_schedule_list.html
│   ├── report_schedule_form.html
│   ├── report_template_list.html
│   ├── report_template_form.html
│   ├── share_report.html
│   └── shared_view.html
```

### Phase 4
```
admin_panel/
├── templates/admin_panel/
│   ├── audit_logs.html
│   ├── error_reports.html
│   └── partials/
│       ├── _time_series_chart.html
│       ├── _user_analytics.html
│       └── _technique_analytics.html
```

### Phase 5
```
notifications/
├── __init__.py
├── models.py
├── views.py
├── urls.py
├── tests.py
├── apps.py
├── context_processors.py
├── templatetags/
│   └── notification_tags.py
└── templates/notifications/
    ├── list.html
    └── partials/
        ├── _dropdown.html
        └── _item.html
```

### Phase 6
```
export/
├── __init__.py
├── views.py
├── urls.py
├── apps.py
└── templates/export/
    └── export_page.html

share/
├── __init__.py
├── views.py
├── urls.py
└── templates/share/
    └── experiment_view.html
```

---

## Dependency Graph

```
Phase 1 (Audit) ─────────────────────┐
                                     ├──> Phase 4 (Admin) depends on audit models
                                     │
Phase 2 (Visualization) ─────────────┤
                                     ├──> Phase 3 (Reports) uses viz engine
                                     │
Phase 5 (Notifications) ────────────┤  depends on Phase 1 signals
                                     │
Phase 6 (Export/Polish) ─────────────┘  depends on everything above
```

**Recommended execution order**: P1 → P2 → P3 → P4 → P5 → P6
