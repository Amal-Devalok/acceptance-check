#!/usr/bin/env python3
"""
acceptance_check.py — how much AI-proposed code survives unedited in HEAD.

Method:
  1. Find commits in the lookback window co-authored by Claude (the
     "Co-authored-by: Claude" trailer this harness adds automatically).
  2. For each, count the lines it added (unified diff, + lines only).
  3. git blame HEAD on every file those commits touched, and tally how many
     of those originally-added lines are STILL blamed to an AI commit —
     i.e. no human-only commit has touched them since.
  4. acceptance rate = still-AI-attributed lines / lines AI ever added.

This is a proxy for "accepted without material review," not a measurement of
whether a human actually read the line. A line nobody ever revisits looks
identical, in this metric, to a line that was reviewed and judged correct.
Treat the number as a prompt to look closer, not a verdict on its own.
"""
import argparse
import subprocess
import sys
import tempfile
import shutil
import os


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def is_git_repo(cwd=None):
    r = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd)
    return r.returncode == 0 and r.stdout.strip() == "true"


def ai_commit_hashes(since, cwd=None):
    r = run(["git", "log", f"--since={since}", "--format=%H"], cwd=cwd)
    hashes = [h for h in r.stdout.strip().split("\n") if h]
    ai = []
    for h in hashes:
        msg = run(["git", "log", "-1", "--format=%B", h], cwd=cwd).stdout
        if "co-authored-by: claude" in msg.lower():
            ai.append(h)
    return hashes, ai


def touched_files(commit, cwd=None):
    r = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit], cwd=cwd)
    return [f for f in r.stdout.strip().split("\n") if f]


def added_lines(commit, path, cwd=None):
    r = run(["git", "show", commit, "--", path], cwd=cwd)
    lines = []
    for line in r.stdout.split("\n"):
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            lines.append(line[1:])
    return lines


def blame_owners(path, cwd=None):
    """Return list of commit hashes, one per current line in `path` at HEAD."""
    r = run(["git", "blame", "-w", "--line-porcelain", "HEAD", "--", path], cwd=cwd)
    if r.returncode != 0:
        return None  # file gone / unreadable at HEAD
    owners = []
    for line in r.stdout.split("\n"):
        if line and " " in line and len(line.split(" ")[0]) == 40:
            owners.append(line.split(" ")[0])
    return owners


def compute(since, cwd=None):
    all_hashes, ai_hashes = ai_commit_hashes(since, cwd=cwd)
    if not ai_hashes:
        return {"ai_commits": 0, "human_commits": len(all_hashes), "total_added": 0,
                "survived": 0, "rate": None}

    ai_set = set(ai_hashes)
    files = set()
    total_added = 0
    for h in ai_hashes:
        for f in touched_files(h, cwd=cwd):
            files.add(f)
            total_added += len(added_lines(h, f, cwd=cwd))

    survived = 0
    for f in files:
        owners = blame_owners(f, cwd=cwd)
        if owners is None:
            continue  # file deleted since — none of its lines survived, already reflected by omission
        survived += sum(1 for o in owners if o in ai_set)

    rate = (survived / total_added * 100) if total_added else None
    return {
        "ai_commits": len(ai_hashes),
        "human_commits": len(all_hashes) - len(ai_hashes),
        "total_added": total_added,
        "survived": survived,
        "rate": rate,
    }


def report(result, threshold, since):
    if result["ai_commits"] == 0:
        print(f"No Claude-coauthored commits found in the last {since}. Nothing to measure.")
        return
    r = result["rate"]
    print(f"Window: since {since}")
    print(f"AI-coauthored commits: {result['ai_commits']}   Human-only commits: {result['human_commits']}")
    if r is None:
        print("AI commits touched no line-countable diffs — nothing to measure.")
        return
    print(f"Lines AI added: {result['total_added']}   Still AI-attributed at HEAD: {result['survived']}")
    print(f"Acceptance rate: {r:.1f}%")
    if r >= threshold:
        print(
            f"\n⚠ Above the {threshold:.0f}% caution line. This is the pattern flagged in AI-coding "
            "research (GitHub Copilot productivity studies; 2025 vibe-coding data from GitClear/METR/"
            "CodeRabbit) right before skill atrophy and rubber-stamping show up — not proof it's "
            "happening here, just a prompt to check whether review is still real."
        )
    else:
        print(f"\nBelow the {threshold:.0f}% caution line.")


def self_test():
    """Synthetic repo: one AI commit, one human commit that overwrites half its lines.
    Expected acceptance rate: 50%."""
    tmp = tempfile.mkdtemp()
    try:
        run(["git", "init", "-q"], cwd=tmp)
        run(["git", "config", "user.email", "t@t.com"], cwd=tmp)
        run(["git", "config", "user.name", "Test"], cwd=tmp)

        path = os.path.join(tmp, "f.txt")
        with open(path, "w") as fh:
            fh.write("line1\nline2\n")
        run(["git", "add", "f.txt"], cwd=tmp)
        run(["git", "commit", "-q", "-m", "add lines\n\nCo-authored-by: Claude Sonnet 5 <noreply@anthropic.com>"], cwd=tmp)

        with open(path, "w") as fh:
            fh.write("line1\nCHANGED\n")
        run(["git", "add", "f.txt"], cwd=tmp)
        run(["git", "commit", "-q", "-m", "human edit"], cwd=tmp)

        result = compute("5 years ago", cwd=tmp)
        assert result["ai_commits"] == 1, result
        assert result["total_added"] == 2, result
        assert result["survived"] == 1, result
        assert abs(result["rate"] - 50.0) < 0.01, result
        print("self-test passed: 50.0% acceptance rate on synthetic 1-of-2-lines-overwritten repo")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--since", default="30 days ago", help='git-style window, e.g. "14 days ago"')
    p.add_argument("--threshold", type=float, default=90.0, help="caution threshold, percent")
    p.add_argument("--self-test", action="store_true", help="run the synthetic-repo self-check and exit")
    args = p.parse_args()

    if args.self_test:
        self_test()
        return

    if not is_git_repo():
        print("Not inside a git repository.", file=sys.stderr)
        sys.exit(1)

    result = compute(args.since)
    report(result, args.threshold, args.since)


if __name__ == "__main__":
    main()
