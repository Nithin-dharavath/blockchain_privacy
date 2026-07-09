---

description: Execute the current roadmap task on the current feature branch by reading test-todo.md, implementing the matched task, and stopping only when the task is complete or blocked.
allowed-tools: Read, Edit, Bash
-------------------------------

# /build-task

Execute **exactly one roadmap task** for the current branch.

## Rules

* Roadmap source: `test-todo.md`
* One branch = one top-level roadmap task
* Branch format: `feature/<task-title-slug>`
* **Implement the matched task in this run**
* Do **not** only return a plan
* Do **not** start the next roadmap task
* Stay scoped to the matched task only

## Steps

1. Get current branch:

   ```bash
   git branch --show-current
   ```

2. Validate branch starts with `feature/`. Extract the slug after `feature/` as `CURRENT_SLUG`.

3. Read `test-todo.md` and parse top-level roadmap tasks in order.
   For each task, extract:

   * `TASK_ID`
   * `TASK_TITLE`
   * `TASK_SLUG`
   * nested checklist items directly under it

4. Match `CURRENT_SLUG` to a task slug.
   If no exact match, stop.

5. Find:

   * current task
   * next task

6. Rename the session to:

   ```text
   <TASK_ID> <TASK_TITLE>
   ```

7. Inspect the current repo state relevant to the matched task:

   * `git status --short`
   * relevant files for that task
   * existing implementation related to that task only

8. Build a **short internal implementation plan** for the matched task, then **execute it immediately**.

   * Create/update the necessary files
   * Wire the required code
   * Complete the matched roadmap task in this run
   * Do **not** stop after planning unless blocked

9. Keep working until one of these is true:

   * the matched roadmap task is implemented
   * a real blocker prevents completion

10. When implementation is finished, give a short completion summary and tell the user to run `/ship-feature`.

## Execution behavior

Treat this as an **implementation command**, not a planning command.

Default behavior:

* make the code changes
* update the relevant files
* finish the matched task
* keep scope limited to the current roadmap task only

Do **not** ask for confirmation before making normal implementation changes.

## Output

Return only these sections:

### Current task

* task id + title
* current branch

### Implemented

Short bullet list of what was changed for this task.

### Files changed

List created/updated files.

### Verification

Short checks the user should run or what was verified.

### Next

* say whether the task looks ready for `/ship-feature`
* show next task id + title
* show next branch name

## Stop only if

* current branch is not `feature/<slug>`
* `test-todo.md` cannot be parsed
* branch slug does not match any roadmap task
* the task depends on missing project context/files and cannot be safely implemented
* the repo is in a broken state that prevents implementation
