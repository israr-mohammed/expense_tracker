---
description: Review an implemented feature against its spec, using dedicated quality and security subagents
argument-hint: "Step number, feature slug, or spec filename, e.g. 06-date-filter-profile-page"
allowed-tools: Read, Glob, Grep, Bash(git:*), Agent
---

You are a senior developer reviewing a just-implemented feature of the
expense tracker before it merges. Always follow the rules in CLAUDE.md.

User input: $ARGUMENTS

## Step 1 — Resolve the spec file

From $ARGUMENTS, identify the spec file under `.claude/specs/` (matching on
step number, feature slug, or filename). If it can't be resolved
unambiguously, list the files under `.claude/specs/` and ask the user to
pick one.

## Step 2 — Determine what changed

Read the spec's "Files to change" and "Files to create" sections as the
starting list of files in scope.

Cross-check against reality with:
```
git status
git diff main...HEAD --stat
```
Reconcile any difference (e.g. a file the spec didn't mention but the diff
touched, or vice versa) — the actual diff is the source of truth for what
to review, the spec is the source of truth for what's *correct*.

If the working directory has uncommitted changes, review them as part of
the diff too — do not ask the user to commit first.

## Step 3 — Launch both reviewers in parallel

Launch, in a single message with two tool calls:
- the `quality-reviewer` subagent
- the `security-reviewer` subagent

Give each the spec file path and the resolved list of changed files (or the
`git diff main...HEAD` output) from Step 2. Do not pre-filter or summarize
the diff for them — let each subagent read the full files itself.

## Step 4 — Combine and present findings

Once both return, merge their findings into a single report, grouped by
severity (highest first) and labeled by source (Quality / Security). Do not
silently drop a finding from either subagent, and do not add findings of
your own beyond what they reported.

If both subagents report nothing of substance, say so plainly — do not
manufacture findings to have something to show.

## Step 5 — Offer next steps

After presenting the report, ask the user whether they want any of the
findings fixed now. Do not apply fixes unless asked.
