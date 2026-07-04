---

description: Commit, push, create PR, merge, clean up, sync to-do.md, and create the next roadmap branch by reading tasks directly from to-do.md
allowed-tools: Read, Bash, mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__delete_branch
------------------------------------------------------------------------------------------------------------------------

# /ship-feature

Ships the current Blockchain Privacy Platform roadmap feature branch, updates `to-do.md`, commits, pushes, creates or reuses a PR, squash-merges it, deletes the shipped branch, and creates the **next roadmap branch automatically**.

This command **does not hardcode the roadmap**.
It reads the roadmap directly from **`to-do.md`**.

---

# Branch format

Current branch **must** be:

```text
feature/<task-title-slug>
```

Examples:

* `feature/audit-model`
* `feature/audit-middleware`
* `feature/audit-mixin-and-signals`
* `feature/results-dashboard`
* `feature/visualization-engine`
* `feature/report-sharing`
* `feature/notification-model`

The **next branch must also use slug-only format** — **no task numbers in branch names**.

---

# Roadmap source

The roadmap source of truth is:

```text
to-do.md
```

The command must parse roadmap tasks from `to-do.md` instead of using a hardcoded list.

A roadmap task is any checklist line that begins with a task ID like:

```md
- [ ] Something
- [x] Something
```

and appears under a phase section in the roadmap.

The command should use the **ordered appearance in `to-do.md`** as the roadmap order.

---

# Step 1 — Detect branches

Determine the repository default branch and store it as `DEFAULT_BRANCH`.

Run:

```bash
git remote show origin | sed -n '/HEAD branch/s/.*: //p'
```

If that returns empty, fall back to:

```bash
git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
```

Run:

```bash
git branch --show-current
```

Store it as:

* `CURRENT_BRANCH`
* `OLD_FEATURE_BRANCH`

If `CURRENT_BRANCH` is the default branch, stop and say:

```text
You're currently on the default branch.
Switch to a roadmap feature branch before running /ship-feature.
```

---

# Step 2 — Validate branch format

`CURRENT_BRANCH` must match:

```text
feature/<task-title-slug>
```

If the branch does not start with `feature/`, stop and say:

```text
Current branch does not match the roadmap branch format.
Use: feature/<task-title-slug>
Then run /ship-feature again.
```

Extract the slug after `feature/` and store it as:

* `CURRENT_SLUG`

---

# Step 3 — Parse roadmap tasks from `to-do.md`

Open `to-do.md`.

Build an ordered roadmap task list by scanning the file from top to bottom.

For every **top-level roadmap task item** in the file, extract:

* `TASK_ID`
* `TASK_TITLE`
* `TASK_SLUG`
* `TASK_LINE_NUMBER`
* `TASK_CHECK_STATE`
* `TASK_SECTION` if available

## What counts as a roadmap task

A roadmap task is a checklist line that belongs to the main roadmap sequence and corresponds to a ship-able feature branch.

Examples from this project:

* `1.1 Audit Model`
* `1.2 Audit Middleware`
* `1.3 Audit Mixin & Signals`
* `2.1 Results Dashboard`
* `3.5 Report Sharing`
* `5.3 Notification Views & URLs`
* `6.4 Shareable Result Links`

## Ignore these when parsing roadmap order

Do **not** treat the following as roadmap tasks:

* nested sub-checklist items under a task
* file inventory items
* dependency graph items
* example snippets
* checklist items inside notes/examples
* anything after the main roadmap section that is not part of the phase task list

## Task title normalization

For each task title, compute `TASK_SLUG` with these rules:

1. lowercase
2. replace `&` with `and`
3. replace `/` with `and`
4. remove punctuation except spaces and hyphens
5. replace spaces with hyphens
6. collapse repeated hyphens
7. trim leading/trailing hyphens

Examples:

* `Audit Model` → `audit-model`
* `Audit Mixin & Signals` → `audit-mixin-and-signals`
* `Fix & Enhance Comparison Detail` → `fix-and-enhance-comparison-detail`
* `Notification Views & URLs` → `notification-views-and-urls`
* `PDF Report Generation` → `pdf-report-generation`

Store the parsed roadmap as an ordered list.

If no roadmap tasks can be parsed from `to-do.md`, stop and say:

```text
Could not parse roadmap tasks from to-do.md.
Make sure the roadmap checklist exists in to-do.md before running /ship-feature.
```

---

# Step 4 — Match the current branch to a roadmap task

Match `CURRENT_SLUG` against the parsed roadmap task slugs from Step 3.

The first exact slug match sets:

* `CURRENT_TASK_ID`
* `CURRENT_TASK_TITLE`
* `CURRENT_TASK_LINE_NUMBER`
* `CURRENT_TASK_INDEX`

If no match is found, stop with:

```text
Could not match branch slug "<slug>" to any roadmap task in to-do.md.
Use a branch name in the form: feature/<task-title-slug>
```

Report internally:

* `CURRENT_TASK_ID`
* `CURRENT_TASK_TITLE`

---

# Step 5 — Determine the next roadmap task

Using the parsed roadmap order from Step 3, find the task immediately after `CURRENT_TASK_INDEX`.

Store:

* `NEXT_TASK_ID`
* `NEXT_TASK_TITLE`
* `NEXT_TASK_SLUG`

If there is no next task, set:

* `HAS_NEXT_TASK=false`

Otherwise set:

* `HAS_NEXT_TASK=true`

---

# Step 6 — Inspect changes and generate commit message

Run:

```bash
git diff --staged
git diff
git log DEFAULT_BRANCH..HEAD --oneline
```

If a matching spec exists in `.claude/specs/`, use it.
If not, infer the feature from the code changes and commit history.

Generate a Conventional Commit message using one of:

* `feat:`
* `fix:`
* `chore:`
* `docs:`
* `refactor:`
* `test:`
* `perf:`

Rules:

* lowercase
* no period at the end
* under 72 characters
* describe what the user can now do, not what the code does

Examples:

* `feat: add audit model and admin registration`
* `feat: add audit middleware for request logging`
* `feat: add visualization engine for experiment charts`
* `fix: correct comparison detail ranking logic`
* `feat: add report sharing with token links`

Also generate:

* `COMMIT_MESSAGE`
* `PR_TITLE`

`PR_TITLE` must be plain English **without** the Conventional Commit prefix.

---

# Step 7 — Update `to-do.md` for the shipped task

Open `to-do.md` and locate the exact roadmap task line for `CURRENT_TASK_ID` / `CURRENT_TASK_TITLE`.

Update the **main roadmap task checkbox** for the shipped task from unchecked to checked.

Example:

From:

```md
- [ ] Audit Model
```

to:

```md
- [x] Audit Model
```

## Important rules for `to-do.md`

### 1) Update only the current roadmap task automatically

The command must always mark the **main current roadmap task** as complete.

### 2) Nested subtasks

If the current roadmap task has nested checklist items immediately below it, the command may mark them `[x]` **only if one of the following is true**:

* the user already checked them manually
* the spec/checklist clearly maps to completed implementation work
* the changed files and code strongly indicate those sub-items are done

If there is uncertainty, leave nested subtasks unchanged rather than guessing.

### 3) Do not modify unrelated tasks

Do not tick:

* sibling tasks
* future tasks
* prior unfinished tasks
* phase headers
* file inventory checklists
* dependency graph notes

### 4) Preserve formatting

Preserve indentation, spacing, headings, and all non-target lines.

After editing `to-do.md`, verify that the current roadmap task line is now `[x]`.

If the current task is still not marked complete, stop and say:

```text
Current roadmap task is not marked complete in to-do.md.
Update the checklist for the shipped task before committing.
```

Report:

```text
✓ Updated to-do.md for CURRENT_TASK_ID — CURRENT_TASK_TITLE
```

---

# Step 8 — Commit

Run:

```bash
git add .
git status --short
```

If there are no changes to commit, stop and say:

```text
No changes detected.
Nothing to commit.
```

Before committing, confirm that the current roadmap task in `to-do.md` is checked.

If not, stop and say:

```text
Current roadmap task is not marked complete in to-do.md.
Update the checklist for the shipped task before committing.
```

Otherwise run:

```bash
git commit -m "<COMMIT_MESSAGE>"
```

Report:

```text
✓ Updated to-do.md
✓ Committed — <COMMIT_MESSAGE>
```

---

# Step 9 — Push

Run:

```bash
git push
```

If push fails because no upstream exists, run:

```bash
git push -u origin CURRENT_BRANCH
```

Report:

```text
✓ Pushed — CURRENT_BRANCH
```

---

# Step 10 — Create or reuse PR

If GitHub MCP is not connected, stop and say:

```text
GitHub MCP is not connected. Run /mcp to check connection.
```

If a PR already exists for `CURRENT_BRANCH`, reuse it.
Otherwise create one from `CURRENT_BRANCH` into `DEFAULT_BRANCH`.

Use `PR_TITLE` as the title.

## PR body if a spec exists

```markdown
## What this PR does
<one paragraph from the spec overview>

## Changes
<bullet list of changed files with one-line descriptions>

## Definition of done
<spec checklist with completed items marked [x]>

## How to test
<testing steps from the spec>
```

## PR body if no spec exists

```markdown
## What this PR does
<one paragraph describing the completed roadmap task>

## Changes
<bullet list of changed files with one-line descriptions>

## How to test
1. Run the relevant Django checks/tests.
2. Open the affected page, command, or workflow.
3. Verify the new functionality manually.
4. Include any task-specific verification steps.
```

## PR body guidance by task type

### Audit tasks

Include:

* models, middleware, signals, views, templates, or commands added
* where audit events are captured
* how to verify logs appear in DB, UI, or admin

### Visualization tasks

Include:

* charts added
* views/templates updated
* any new visualization utility functions
* how to verify charts render with experiment data

### Reporting tasks

Include:

* report generation/export/share/scheduling functionality added
* models/templates/commands updated
* how to generate and validate report output files

### Admin/analytics tasks

Include:

* dashboards, analytics, notifications, or metrics added
* models/views/templates/commands changed
* how to verify admin workflows and analytics output

### Notification/export/polish tasks

Include:

* trigger sources, views, export formats, public links, tests, or cleanup commands
* how to verify notifications, exports, or management commands

Report:

```text
✓ PR created — <PR URL>
```

---

# Step 11 — Merge PR

Merge the PR using **Squash Merge**.

If PR creation failed, stop.
If merge conflicts exist, stop and ask the user to resolve them first.

Report:

```text
✓ PR merged to DEFAULT_BRANCH
```

---

# Step 12 — Delete remote branch

Delete `OLD_FEATURE_BRANCH` via GitHub MCP.

If it is already deleted, ignore the error.

Report:

```text
✓ Remote branch deleted
```

---

# Step 13 — Switch to default branch and pull

Run:

```bash
git checkout DEFAULT_BRANCH
git pull origin DEFAULT_BRANCH
```

Report:

```text
✓ Switched to DEFAULT_BRANCH — up to date
```

---

# Step 14 — Delete local branch

Run:

```bash
git branch -D OLD_FEATURE_BRANCH
```

If it no longer exists locally, ignore the error.

Report:

```text
✓ Local branch deleted
```

---

# Step 15 — Create the next roadmap branch

If `HAS_NEXT_TASK=false`, do not create a branch. Report:

```text
✓ Roadmap complete — no next feature branch created
```

If `HAS_NEXT_TASK=true`, generate:

```text
feature/<NEXT_TASK_SLUG>
```

Examples:

* `Audit Middleware` → `feature/audit-middleware`
* `Visualization Engine` → `feature/visualization-engine`
* `Report Sharing` → `feature/report-sharing`
* `Notification Views & URLs` → `feature/notification-views-and-urls`
* `Shareable Result Links` → `feature/shareable-result-links`

Store it as:

* `NEXT_BRANCH`

Run:

```bash
git checkout -b NEXT_BRANCH
```

If it already exists locally, stop and say:

```text
The next roadmap branch already exists locally: NEXT_BRANCH
Switch to it manually or delete it before continuing.
```

Set:

* `CURRENT_BRANCH = NEXT_BRANCH`

Report:

```text
✓ Created new feature branch — CURRENT_BRANCH
✓ Next roadmap task — NEXT_TASK_ID: NEXT_TASK_TITLE
```

---

# Final summary

## If a next branch was created

```text
────────────────────────────────────────

/ship-feature complete

✓ Updated to-do.md
✓ Committed — <COMMIT_MESSAGE>
✓ Pushed — <OLD_FEATURE_BRANCH>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to DEFAULT_BRANCH
✓ Local branch deleted
✓ Created new feature branch — <CURRENT_BRANCH>
✓ Next roadmap task — <NEXT_TASK_ID>: <NEXT_TASK_TITLE>

Next: implement <NEXT_TASK_ID> on <CURRENT_BRANCH>

────────────────────────────────────────
```

## If there is no next task

```text
────────────────────────────────────────

/ship-feature complete

✓ Updated to-do.md
✓ Committed — <COMMIT_MESSAGE>
✓ Pushed — <OLD_FEATURE_BRANCH>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to DEFAULT_BRANCH
✓ Local branch deleted
✓ Roadmap complete — no next feature branch created

Next: blockchain privacy roadmap is complete

────────────────────────────────────────
```

---

# Rules

* Never commit directly to the default branch.
* Always use **Squash Merge**.
* Always delete both the remote and local shipped branch.
* Always create the **next roadmap branch** unless the roadmap is complete.
* The next branch must come from the **parsed roadmap order in `to-do.md`**, not from git diff or a generic name.
* The current branch must follow the roadmap branch naming format.
* Branches must **not** contain task numbers.
* Always update `to-do.md` before commit for the shipped task.
* If GitHub MCP is not connected, stop with:

```text
GitHub MCP is not connected. Run /mcp to check connection.
```

* If push fails due to no upstream, use:

```bash
git push -u origin CURRENT_BRANCH
```

* Never proceed to merge if PR creation fails.
* Never fail only because a spec file is missing.
* If a spec is incomplete, use the code changes as the source of truth.
* If a PR already exists for the current branch, reuse it.
* Stop only for critical blockers such as:

  * merge conflicts
  * no changes to commit
  * GitHub MCP unavailable
  * invalid roadmap branch format
  * unable to determine the next roadmap task
  * unable to parse roadmap tasks from `to-do.md`
  * unable to update `to-do.md` for the current task

---

# Recommended branch names for this project

Use this style going forward:

```text
feature/audit-model
feature/audit-middleware
feature/audit-mixin-and-signals
feature/audit-views-and-urls
feature/results-dashboard
feature/visualization-engine
feature/pdf-report-generation
feature/report-sharing
feature/admin-audit-viewer
feature/notification-model
feature/shareable-result-links
feature/testing
```
