---

description: Ship the current roadmap feature branch, update to-do.md, merge it, create the next roadmap branch, and rename the session to the next task.
allowed-tools: Read, Edit, Bash, mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__delete_branch
------------------------------------------------------------------------------------------------------------------------------

# /ship-feature

Ship the current roadmap task branch and move to the next roadmap task.

## Rules

* Roadmap source: `test-todo.md`
* One branch = one top-level roadmap task
* Branch format: `feature/<task-title-slug>`
* Never commit to default branch
* Always squash merge
* Update **only** the matched roadmap task in `test-todo.md`
* Create the next branch from roadmap order
* Rename the session to the next task after creating the next branch

## Steps

1. Detect default branch:

   ```bash
   git remote show origin | sed -n '/HEAD branch/s/.*: //p'
   ```

   Fallback:

   ```bash
   git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   ```

2. Get current branch:

   ```bash
   git branch --show-current
   ```

3. Validate current branch:

   * must not be the default branch
   * must start with `feature/`

4. Read `test-todo.md` and parse **top-level roadmap tasks only** in order.
   For each task extract:

   * `TASK_ID`
   * `TASK_TITLE`
   * `TASK_SLUG`
   * nested checklist items directly under it

5. Match the current branch slug to the roadmap task slug.
   Find:

   * `CURRENT_TASK`
   * `NEXT_TASK`

6. Inspect current branch changes:

   ```bash
   git status --short
   git diff --staged
   git diff
   git log DEFAULT_BRANCH..HEAD --oneline
   ```

7. Validate the matched task looks complete enough to ship.
   If clearly incomplete, stop.

8. Generate:

   * `COMMIT_MESSAGE` → short Conventional Commit for the matched task
   * `PR_TITLE` → same meaning without the commit prefix

9. Update `test-todo.md`:

   * mark the matched top-level roadmap task `[x]`
   * mark nested items only if clearly completed
   * do not touch unrelated tasks

10. Commit:

```bash
git add .
git commit -m "<COMMIT_MESSAGE>"
```

11. Push:

```bash
git push
```

If needed:

```bash
git push -u origin CURRENT_BRANCH
```

12. Create or reuse PR into `DEFAULT_BRANCH`.

13. Squash merge PR.

14. Delete remote branch.

15. Switch to default branch and pull:

```bash
git checkout DEFAULT_BRANCH
git pull origin DEFAULT_BRANCH
```

16. Delete local shipped branch:

```bash
git branch -D OLD_FEATURE_BRANCH
```

17. If there is a next roadmap task:

* create:

  ```bash
  git checkout -b feature/<NEXT_TASK_SLUG>
  ```
* rename the session to:

  ```text
  <NEXT_TASK_ID> <NEXT_TASK_TITLE>
  ```

## Commit message

Generate a short Conventional Commit from the shipped task, for example:

* `feat: add visualization engine`
* `feat: enhance experiment detail view`
* `fix: improve comparison detail metrics`

## PR body

Keep it short:

* what the task completed
* key files changed
* short verification notes

## Output

Return only:

### Shipped

* task id + title
* commit message
* PR link

### Next

* next task id + title
* next branch name
* session name

## Stop if

* current branch is the default branch
* current branch is not `feature/<slug>`
* `test-todo.md` cannot be parsed
* branch slug does not match a roadmap task
* no changes to commit
* task is clearly incomplete
* PR creation or merge fails
