---
name: acceptance-check
description: Measures how much of Claude's output survives without material human revision — across two different surfaces, because they offer different signals. For code (git repos): acceptance_check.py walks commits co-authored by Claude and git-blames HEAD to see how much of what they added is still AI-attributed vs. overwritten by a human-only commit since. For Figma/Framer/general design ideation, which have no git-blame equivalent: design_check.py reads the shared build-log.md (populated manually or by the figma-watch skill) and measures what fraction of logged decisions show no considered alternative. Both flag a caution threshold rather than a hard rule. Trigger on "check acceptance rate", "am i rubber-stamping this", "acceptance-check", "how much of this did i actually review", "first-idea rate", "design-check".
argument-hint: code: [--since "30 days ago"] [--threshold 90]   design: [--log build-log.md] [--threshold 70]
---

## Two scripts, because code and design don't offer the same signal

Git gives code a real authorship trail — every commit here carries a
`Co-authored-by: Claude` trailer, so `acceptance_check.py` can measure
whether AI-added lines are still there, untouched, at HEAD. That's a genuine
rate with a genuine denominator (lines added).

Figma and Framer have neither authorship metadata nor a push-based change
feed available here — `get_metadata` is a pull with no "who changed this"
field. There's no equivalent of git blame to lean on. What exists instead is
the build-log / Decision Log convention this workflow already keeps (see the
Site Build Protocol SOP and the `figma-watch` skill) — a running list of
design decisions, one line each. `design_check.py` reads that log instead of
a version-control history, and measures a related but different thing: what
fraction of *logged* decisions show a considered alternative versus just
stating the outcome. Different mechanism, same underlying question — is
review actually happening, or is the first thing that got made just... what
shipped.

Neither script covers pure ideation with nothing written down anywhere. If a
direction was decided in conversation and never logged, it's invisible to
both tools — the same way an un-committed code change is invisible to the
code one. The log has to exist for this to work at all; see `figma-watch` and
the Decision Log guidance in the Site Build Protocol for how to keep that
close to zero-effort.

## Running them

```
python3 acceptance_check.py --since "30 days ago" --threshold 90     # code, inside a git repo
python3 design_check.py --log build-log.md --threshold 70            # Figma / Framer / ideation
```

Both are Python 3 stdlib only — no install step, no dependencies.

## Steps when this skill is invoked

1. Ask (or infer from context) which surface is in question — a git repo
   with real commits, or a design surface whose only record is a build-log.
   If both apply to the same project, running both and reporting them
   together is fine and often the more honest picture.
2. For code: confirm the current directory is a git repo before running
   `acceptance_check.py`. If not, say so and stop.
3. For design: confirm a build-log file actually exists before running
   `design_check.py`. If it doesn't, say so — this isn't something to
   fabricate a log for just to produce a number.
4. Report the script's own output plainly — don't re-explain what it means
   beyond what it already prints. If either rate is at or above its
   threshold, don't moralize; the script's own caution line already says
   what pattern it's flagging.

## Self-checks

- `python3 acceptance_check.py --self-test` — synthetic two-commit git repo,
  asserts a 50% acceptance rate.
- `python3 design_check.py --self-test` — synthetic four-entry log, asserts
  a 50% first-idea rate.

Run the relevant one after touching either script. Both self-tests were
written first specifically because this kind of text/history parsing is
exactly where an edge case (a repo's root commit, a log entry with unusual
punctuation) goes silently wrong without something to check it against.

## Known limitations

**Code (`acceptance_check.py`):**
- Only sees commits, not what happened in an editor before a commit existed.
  Squashed/rebased history undercounts or misattributes.
- Can't distinguish "reviewed and left alone because it was correct" from
  "never looked at again."
- Merge commits and binary files aren't handled specially.

**Design (`design_check.py`):**
- Entirely dependent on log discipline — silent about anything never
  written down, and can't tell a genuinely single-path decision from an
  unreviewed one.
- The 70% threshold is a working default modeled after the code tool's, not
  a number any cited study measured directly — recalibrate against your own
  team's actual baseline rather than treating it as fixed.
- Doesn't distinguish Figma from Framer from pure ideation — by design, since
  the log format is meant to be source-agnostic. If that turns out to matter,
  tag entries at the source and filter before running.
