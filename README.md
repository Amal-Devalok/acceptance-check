# acceptance-check

A Claude Code skill that measures how much AI-proposed code survives
unedited in a git repo — a concrete stand-in for "suggestion acceptance
rate," for teams using an agentic coding tool instead of an inline-completion
tool that reports this number natively.

## The problem

GitHub Copilot and similar tools show you a suggestion-acceptance rate
directly, because their unit of work is a single inline completion. Claude
Code (and agentic coding generally) doesn't have that unit — there's no
ghost-text to accept or reject, just diffs and commits. That makes it easy to
lose the signal Copilot research has already flagged as a warning sign:
accepting AI output at a very high rate correlates with *not actually
reviewing it*.

## What it does

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

## Install

Drop this folder into `~/.claude/skills/acceptance-check/` (or your
project's `.claude/skills/`). Requires Python 3, standard library only — no
install step, no dependencies.

## Use

```
python3 acceptance_check.py --since "30 days ago" --threshold 90
```

Or, inside a Claude Code session with the skill installed: `/acceptance-check`.

Run `python3 acceptance_check.py --self-test` any time you touch the script —
it spins up a synthetic two-commit repo and asserts the computed rate is
exactly 50%, which is what caught a real bug (`git diff-tree` silently
returns nothing for a repo's initial commit unless you pass `--root`) during
development.

## Why 90%, and why this matters at all

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

## Known limitations

- Only sees commits, not what happened in an editor before a commit existed.
  Squashed or rebased history will undercount or misattribute.
- Can't distinguish "reviewed and left alone because it was correct" from
  "never looked at again" — no git-based signal can make that distinction.
- Merge commits and binary files aren't handled specially; heavy use of
  either will skew the numbers. This is a lightweight heuristic, not an audit
  tool.

## License

MIT — see [LICENSE](./LICENSE).
