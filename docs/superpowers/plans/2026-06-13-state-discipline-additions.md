# State Discipline Additions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the `<state_discipline>` section of `context.md` with three explicit, hard behavioural rules around committing, externalising context, and proactive note-taking.

**Architecture:** Single file edit to `/opt/payload/context.md` (source of truth: `context.md` in the `claude-payload` repo). The existing `<state_discipline>` block is replaced with an expanded version that folds in the three new rules as non-negotiable obligations.

**Tech Stack:** Plaintext / XML-like context format. No code. Git for commit + push.

---

### Task 1: Expand `<state_discipline>` in `context.md`

**Files:**
- Modify: `context.md` (root of claude-payload repo)

- [ ] **Step 1: Replace the existing `<state_discipline>` block**

Find this block in `context.md`:

```
<state_discipline>
Update state before beginning any task so work can be recovered if interrupted.
Always commit and push changes to both the state repo and any active project immediately.
Reconsider whether state needs updating before ending every response.

Key files to keep current:
- /opt/state/state.json
- /opt/state/active.md
- /opt/state/projects/<project-name>.md
- /home/claude/<project-name>/CLAUDE.md
- /home/claude/<project-name>/.claude/todo.md
- /home/claude/<project-name>/.claude/notes/<note-name>.md
</state_discipline>
```

Replace it with:

```
<state_discipline>
Update state before beginning any task so work can be recovered if interrupted.

## Commit discipline
After EVERY response in which any file was changed — no exceptions — commit and push
both the state repo and any active project repo before the response ends. Do not batch
commits across responses. Do not defer until "the work is done". Each response that
touches files must end with a push.

## Externalise context
Never hold plans, decisions, or important context only in chat. If losing it would
require re-explaining next session, write it to a file now. This includes:
- task plans → .claude/todo.md
- architectural decisions → CLAUDE.md or .claude/notes/<topic>.md
- user preferences or constraints discovered mid-task → .claude/notes/<topic>.md

When in doubt, write it down. A note that wasn't needed costs nothing; missing context
costs the next session.

## Proactive note-taking
When encountering anything worth recalling — a constraint, a gotcha, a user
preference, a non-obvious decision — write a note to `.claude/notes/` before moving
on. Do not wait until the end of the task. Capture it at the moment of discovery.

## Key files to keep current
- /opt/state/state.json
- /opt/state/active.md
- /opt/state/projects/<project-name>.md
- /home/claude/<project-name>/CLAUDE.md
- /home/claude/<project-name>/.claude/todo.md
- /home/claude/<project-name>/.claude/notes/<note-name>.md
</state_discipline>
```

- [ ] **Step 2: Verify the edit looks correct**

```bash
grep -A 50 '<state_discipline>' /home/claude/claude-payload/context.md
```

Expected: the expanded block with all three subsections visible and no duplicate `<state_discipline>` tags.

- [ ] **Step 3: Commit and push**

```bash
cd /home/claude/claude-payload
git add context.md
git commit -m "docs: strengthen state_discipline with commit, externalise, and note-taking rules"
git push
```

Expected: push succeeds, no errors.

---

### Task 2: Update state repo

**Files:**
- Modify: `/opt/state/active.md`
- Modify: `/opt/state/projects/` — update or create a handoff for claude-payload

- [ ] **Step 1: Update active.md to reflect completed work**

Write to `/opt/state/active.md`:

```md
## What I was doing
Strengthening state_discipline in claude-payload context.md

## What's done
- Replaced <state_discipline> block with expanded version covering commit discipline,
  context externalisation, and proactive note-taking

## What's in flight

## What's next
- User to review and iterate on wording if needed
```

- [ ] **Step 2: Commit and push state repo**

```bash
cd /opt/state
git add active.md
git commit -m "docs: update active task after state_discipline edit"
git push
```

Expected: push succeeds.
