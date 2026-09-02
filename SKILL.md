---
name: acceptance-check
description: Measures how much of Claude's output survives without material human revision — three modes, picked by what the user actually has available. session_check.py is the zero-setup default for non-coders building through Claude Code, Figma MCP, and Framer MCP — Claude tallies its own proposal/reaction pattern live, no log, no git needed. acceptance_check.py is for real git repos (git-blame based). design_check.py is for teams already keeping a build-log/Decision Log. Trigger on "check acceptance rate", "am i rubber-stamping this", "acceptance-check", "how much of this did i actually review", "first-idea rate".
argument-hint: (usually no args — this skill picks the right mode automatically)
---

## Pick the mode by what actually exists, not by preference

1. **No git repo, no log, working through Claude Code / Figma MCP / Framer
   MCP** — the default for non-coders. Use `session_check.py`. Nothing to
   set up; see below.
2. **A real git repo with commits** — use `acceptance_check.py` (git-blame
   based, the most rigorous of the three, 90% threshold is literature-backed).
3. **A team already maintaining a build-log/Decision Log** — use
   `design_check.py` (reads that log's divergent-vs-flat entries, 70%
   working-default threshold).

Don't ask a non-coder to start keeping a log just to make mode 3 available —
that recreates the exact friction this project exists to remove. Default to
session mode unless a git repo or an existing log is already there.

## Session mode — how it actually works

There's no file the user writes and no git commit to inspect. Claude tracks
its own proposal/reaction pattern live, during normal work, and keeps the
tally in a small hidden file the user never opens: `.acceptance-tally.json`
in the project directory. This is bookkeeping, not a log — same idea as
`quick-share`'s state file, there so a running tally survives context
compaction, not something anyone is asked to maintain.

**During the session, after any substantive proposal** — a webpage draft or
edit (Edit/Write), a Figma MCP call that creates or changes something
(`2d_write_html`, `2d_update_objects`, `use_figma`, `generate_figma_design`,
etc.), or a Framer MCP call that changes site content — watch the user's
very next message and classify it:

- **accept** — a short affirmation ("yes," "good," "looks great," "next,"
  "ship it"), or the user just moves on to something materially different
  without commenting on what was just shown. Silence-as-approval counts.
- **revise** — "no," "actually," "try something else," "change X," "I don't
  like...," an undo, or a request for a materially different version of the
  *same* thing just proposed.

Then record it — don't ask the user, don't interrupt the flow, just do it as
a quiet side effect of continuing the conversation:

```
python3 session_check.py --record --surface webpage --summary "hero section draft" --reaction accept
```

`--surface` is `webpage`, `figma`, or `framer`. `--summary` is a few words,
not a transcript — this is bookkeeping, not the build-log this mode exists
to avoid.

**When to report:** on request ("check my acceptance rate," "am I rubber-
stamping this"), or naturally at a checkpoint (end of a work session, before
a handoff) — not after every single event, which would just be the log
fatigue problem in a different shape.

```
python3 session_check.py --threshold 90
```

## What this mode can't claim

The classification is Claude's own read of tone and intent in the moment,
not an independent measurement — there's a real conflict-of-interest
question in the AI grading its own acceptance rate. State that plainly if
asked, and if a count looks obviously wrong, say so and let the user correct
it rather than defending the number. A corrected tally is worth more than a
precise-looking wrong one.

## Running the other two modes

```
python3 acceptance_check.py --since "30 days ago" --threshold 90     # code, git repo
python3 design_check.py --log build-log.md --threshold 70            # existing build-log
```

## Self-checks

Run the matching one after touching any script:

```
python3 session_check.py --self-test      # synthetic 4-event tally, expects 75%
python3 acceptance_check.py --self-test   # synthetic 2-commit repo, expects 50%
python3 design_check.py --self-test       # synthetic 4-entry log, expects 50%
```

## Known limitations

**Session mode:** self-reported by the same AI whose output it's grading;
tone classification is inherently soft; only sees what happened inside this
tool, not decisions made in a separate conversation or another app entirely.

**Code mode:** only sees commits, not pre-commit edits; squashed/rebased
history undercounts; can't distinguish "reviewed and correct" from "never
revisited."

**Design-log mode:** entirely dependent on log discipline; the 70% threshold
is a working default, not literature-derived like the code tool's 90%.

All three are lightweight heuristics, not audit tools.
