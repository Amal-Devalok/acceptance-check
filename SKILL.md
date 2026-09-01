---
name: acceptance-check
description: Measures how much AI-proposed code survives unedited in the current git repo — a concrete stand-in for "suggestion acceptance rate" when working with Claude Code instead of inline-completion tools like Copilot. Walks commits co-authored by Claude in a lookback window, diffs what they added, then git-blames HEAD to see how much of that is still AI-attributed versus overwritten by a human-only commit since. Flags a rate above ~90% as the caution pattern documented in AI-coding research. Trigger on "check acceptance rate", "am i rubber-stamping this", "acceptance-check", "how much of this did i actually review".
argument-hint: [--since "30 days ago"] [--threshold 90]
---

## What this measures, and what it doesn't

Copilot-style tools report acceptance rate directly (per-suggestion telemetry).
Claude Code has no such signal — there's no ghost-text to accept or reject. The
closest real proxy available from what the harness actually produces: every
commit Claude makes here carries a `Co-authored-by: Claude` trailer. So this
script finds those commits, counts the lines they added, and checks — via
`git blame` at HEAD — how many of those lines are **still attributed to an AI
commit**, versus having been touched by a human-only commit since.

That's a proxy for "accepted without material review," not a measurement of
whether anyone actually read the line. A line nobody has revisited since
looks identical to a line that was reviewed and judged correct. Treat a high
number as a prompt to look closer, not a verdict on its own — same spirit as
every other guardrail in this workflow: it exists to interrupt autopilot, not
to replace judgment.

## Running it

```
python3 acceptance_check.py [--since "30 days ago"] [--threshold 90]
```

Run from inside the git repo you want to check. Needs Python 3 stdlib only —
no install step.

## Steps when this skill is invoked

1. Confirm the current directory is a git repo. If not, say so and stop —
   don't guess at a path.
2. Run `acceptance_check.py` (this skill's own directory) with whatever
   `--since`/`--threshold` the user gave, defaulting to 30 days / 90%.
3. Report the output plainly — commit counts, lines added, rate, and the
   verdict line the script already produces. Don't re-explain what it means
   beyond what the script itself prints.
4. If the rate is at or above threshold, don't moralize — the script's own
   caution line already says what this is a signal of. Just surface it and,
   if useful, point back to the specific commits/files with the highest
   survival rate (`git log --since=<window> --grep="Co-authored-by: Claude"
   -i`) so there's somewhere concrete to look.

## Self-check

`python3 acceptance_check.py --self-test` runs a synthetic two-commit repo
(one AI commit adds two lines, one human commit overwrites one of them) and
asserts the computed rate is exactly 50%. Run this after ever touching the
script — the git-plumbing logic here is exactly the kind of thing that's
silently wrong in an edge case (root commits, deleted files, merge commits)
without a repo to check it against.

## Known limitations

- Only sees commits, not what happened in an editor before a commit existed.
  Squashed/rebased history will undercount or misattribute.
- Doesn't distinguish "reviewed and left alone because it was correct" from
  "never looked at again." No git-based signal can make that distinction.
- Merge commits and binary files are not handled specially — heavy use of
  either will skew the numbers. This is a lightweight heuristic, not an audit
  tool.
