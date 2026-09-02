# acceptance-check

A Claude Code skill that measures how much of Claude's output survives
without material human revision — for code, and separately for Figma,
Framer, and general design ideation, because those surfaces don't offer the
same signal git does.

Two scripts:

- **`acceptance_check.py`** — code, inside a git repo. Uses `git blame` to
  see how much AI-added code is still there, untouched, at HEAD.
- **`design_check.py`** — Figma, Framer, or any design/ideation work with no
  git history to lean on. Reads the shared build-log/Decision Log this
  workflow already keeps, and measures what fraction of logged decisions
  show no considered alternative.

## The problem

GitHub Copilot and similar tools show you a suggestion-acceptance rate
directly, because their unit of work is a single inline completion. Claude
Code (and agentic coding generally) doesn't have that unit — there's no
ghost-text to accept or reject, just diffs and commits. That makes it easy to
lose the signal Copilot research has already flagged as a warning sign:
accepting AI output at a very high rate correlates with *not actually
reviewing it*.

Neither script covers pure ideation with nothing ever written down — a
direction decided in conversation and never logged is invisible to both, the
same way an uncommitted code change is invisible to the git-based one. The
log has to exist for the design side to work at all.

## What `acceptance_check.py` does (code)

Every commit this harness makes carries a `Co-authored-by: Claude` trailer.
`acceptance_check.py` walks commits in a lookback window, finds the
AI-coauthored ones, counts the lines they added, and then `git blame`s HEAD
to see how many of those lines are **still attributed to an AI commit** —
versus having been touched by a human-only commit since.

```
acceptance rate = lines still AI-attributed at HEAD / lines AI ever added
```

That's a proxy for "accepted without material review," not a measurement of
whether anyone actually read the line — a line nobody has revisited since
looks identical, in this metric, to a line that was reviewed and judged
correct. Treat a high number as a prompt to look closer, not a verdict on its
own.

## What `design_check.py` does (Figma / Framer / ideation)

Figma and Framer have no authorship metadata and no push-based change feed
available here — there's no equivalent of `git blame` to lean on. What's
available instead is the build-log / Decision Log convention this workflow
already keeps (see the Site Build Protocol SOP, and the `figma-watch` skill
that can auto-populate it from a Figma session). `design_check.py` reads
that log and classifies each entry:

- **DIVERGENT** — shows an alternative that was tried and rejected
  (`"Hero A instead of Hero B — because ..."`, or the `figma-watch` format
  `"TRIED X — ..., replaced by Y"` / `"..., don't retry"`)
- **FLAT** — states an outcome with no alternative in evidence

```
first-idea rate = FLAT entries / total entries
```

Same underlying question as the code metric — is review actually happening,
or did the first thing that got made just ship — answered through a
different mechanism because the surface doesn't offer the same signal git
does.

## Install

Drop this folder into `~/.claude/skills/acceptance-check/` (or your
project's `.claude/skills/`). Requires Python 3, standard library only — no
install step, no dependencies.

## Use

```
python3 acceptance_check.py --since "30 days ago" --threshold 90     # code
python3 design_check.py --log build-log.md --threshold 70            # design
```

Or, inside a Claude Code session with the skill installed: `/acceptance-check`.

Run the matching `--self-test` any time you touch either script:

```
python3 acceptance_check.py --self-test   # synthetic 2-commit repo, expects 50%
python3 design_check.py --self-test       # synthetic 4-entry log, expects 50%
```

The code one is what caught a real bug during development (`git diff-tree`
silently returns nothing for a repo's initial commit unless you pass
`--root`) — this kind of history/text parsing is exactly where an edge case
goes silently wrong without something to check it against.

## Why 90% (code), and why this matters at all

This isn't an arbitrary number. It's built directly on a handful of findings
from AI-coding research:

- **GitHub's own Copilot productivity research** found significant speed
  gains from AI-assisted coding, concentrated most heavily in junior
  developers — the same group flagged across multiple studies as most prone
  to high, unreviewed acceptance rates and the skill atrophy that follows.
  [github.blog](https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/)

- **2025 vibe-coding data** (aggregated from GitClear, METR, and CodeRabbit)
  found AI-generated code shipping with roughly 4x more duplication and 2.7x
  more security vulnerabilities than hand-written code — despite feeling
  faster to produce. A companion study, *"Professional Software Developers
  Don't Vibe, They Control"* (2025), found that experienced developers treat
  AI output as a controlled subordinate with checkpoints, not autopilot — the
  behavioral difference this tool is trying to make measurable.
  [Vibe Coding in Practice](https://arxiv.org/pdf/2512.11922) ·
  [Don't Vibe, They Control](https://arxiv.org/pdf/2512.14012)

- **Perry, Srivastava, Kumar & Boneh, Stanford / ACM CCS 2023**, *"Do Users
  Write More Insecure Code with AI Assistants?"* — developers with AI
  assistance wrote measurably less secure code and rated it *more* secure.
  Developers whose code ended up least secure trusted the AI at 4.0/5;
  developers whose code was most secure trusted it at 1.5/5. Trust and
  quality moved in opposite directions.
  [arXiv](https://arxiv.org/pdf/2211.03622) ·
  [ACM DL](https://dl.acm.org/doi/10.1145/3576915.3623157)

- **Risko & Gilbert, "Cognitive Offloading"** (*Trends in Cognitive
  Sciences*, 2016) — the underlying mechanism this whole guardrail exists to
  interrupt. Offloading a task reshapes your confidence in your own ability,
  which reshapes your actual capability over time — a feedback loop, not a
  one-time trade. The clearest empirical number for that loop comes from a
  multicenter colonoscopy RCT: adenoma detection rate was 25.3% with AI
  assistance, but fell to 22.4% — below the clinicians' own 28.4% pre-AI
  baseline — when the same clinicians went back to unaided work after a
  period of AI-assisted practice.
  [Cognitive Offloading (Semantic Scholar)](https://www.semanticscholar.org/paper/Cognitive-Offloading-Risko-Gilbert/a43c46209e447520c0753707baa8c9f12cead7c5) ·
  [deskilling scoping review](https://www.sciencedirect.com/science/article/pii/S2949820126000123)

None of this says a 90%+ acceptance rate is wrong on any given day — a
genuinely mechanical task should have a high rate. It's a flag to check
whether review is still happening, in the same spirit as every guardrail it's
built from: interrupt autopilot, don't replace judgment.

## Why 70% (design), and where that number is weaker than the code one

The design-side threshold draws on the same research already cited for
"never accept the first output" in the underlying SOP:

- **ACM Creativity & Cognition 2024**, *"Homogenization Effects of LLMs on
  Human Creative Ideation"* — AI users produced ideas that were less
  semantically distinct from each other and reported less ownership over
  them than users of a non-AI creativity tool.
- A **CHI 2024 design-fixation study** found fixation doesn't disappear with
  AI use, it relocates — from a reference image onto whatever the AI
  generated first, when reliance is heavy.

Be honest about what's different here: those studies motivate *why*
divergence matters, but neither one measured "what fraction of logged design
decisions should show an alternative" the way the Copilot and Stanford
research gave the code tool an actual number to build on. **70% is a working
default modeled after the code tool's 90%, not a figure any cited study
measured.** Treat it as a starting point to recalibrate against your own
team's real baseline, not a target.

## Known limitations

**`acceptance_check.py` (code):**
- Only sees commits, not what happened in an editor before a commit existed.
  Squashed or rebased history will undercount or misattribute.
- Can't distinguish "reviewed and left alone because it was correct" from
  "never looked at again" — no git-based signal can make that distinction.
- Merge commits and binary files aren't handled specially; heavy use of
  either will skew the numbers.

**`design_check.py` (design):**
- Entirely dependent on log discipline. Silent about anything never written
  down, and can't tell a genuinely single-path decision from an unreviewed
  one — it only sees what made it into the log.
- Doesn't distinguish Figma from Framer from pure ideation, by design — the
  log format is meant to be source-agnostic. Tag entries at the source and
  filter before running if that distinction turns out to matter to you.

Both are lightweight heuristics, not audit tools.

## License

MIT — see [LICENSE](./LICENSE).
