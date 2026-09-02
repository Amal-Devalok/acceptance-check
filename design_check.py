#!/usr/bin/env python3
"""
design_check.py — the Figma/Framer/ideation analog of acceptance_check.py.

Neither Figma nor Framer exposes an authorship trail the way git does, so
there's no equivalent of "git blame" to measure line survival. What's
available instead is the build-log / Decision Log convention already in use
across this workflow (populated manually, or automatically by the
figma-watch skill) — a running list of design decisions, one line each.

This reads that log and classifies each entry:

  DIVERGENT — shows an alternative that was tried and rejected
              ("Hero A instead of Hero B — because ...", or the figma-watch
              format "TRIED X — ..., replaced by Y" / "..., don't retry")
  FLAT      — states an outcome with no alternative in evidence

    first-idea rate = FLAT entries / total entries

This can't tell you whether a flat entry SHOULD have had an alternative —
plenty of decisions are genuinely single-path, and this is blind to whatever
never made it into the log at all. It's a prompt to check whether your own
log's ratio matches how much real exploration actually happened — same
spirit as the code tool's acceptance rate, different mechanism because the
underlying surfaces don't offer the same signal.
"""
import argparse
import os
import re
import shutil
import tempfile

DIVERGENT_PATTERNS = [
    re.compile(r"\binstead of\b", re.I),
    re.compile(r"^\s*[-*]?\s*TRIED\b.*(replaced by|became|don't retry|dont retry)", re.I),
]


def classify(line):
    return any(p.search(line) for p in DIVERGENT_PATTERNS)


def parse_entries(path):
    entries = []
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- ") or line.startswith("* "):
                line = line[2:].strip()
            if len(line) < 8:
                continue
            entries.append(line)
    return entries


def compute(path):
    entries = parse_entries(path)
    if not entries:
        return {"total": 0}
    divergent = sum(1 for e in entries if classify(e))
    flat = len(entries) - divergent
    return {
        "total": len(entries),
        "divergent": divergent,
        "flat": flat,
        "flat_rate": flat / len(entries) * 100,
    }


def report(result, threshold, path):
    if result["total"] == 0:
        print(f"No entries found in {path}. Nothing to measure yet.")
        return
    print(f"Log: {path}")
    print(
        f"Entries: {result['total']}   "
        f"Divergent (alternative documented): {result['divergent']}   "
        f"Flat (no alternative shown): {result['flat']}"
    )
    print(f"First-idea rate: {result['flat_rate']:.1f}%")
    if result["flat_rate"] >= threshold:
        print(
            f"\n⚠ Above the {threshold:.0f}% working default. This is the pattern flagged in "
            "design-fixation research (CHI 2024) and idea-homogenization studies (ACM Creativity "
            "& Cognition 2024) — most logged decisions show no considered alternative. Not proof "
            "nothing was explored, just a prompt to check."
        )
    else:
        print(f"\nBelow the {threshold:.0f}% working default.")
    print(
        "\nNote: unlike the code tool's 90% figure, this threshold is a working default styled "
        "after it, not a number any specific study measured — recalibrate against your own "
        "team's baseline."
    )


def self_test():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "build-log.md")
        with open(path, "w") as f:
            f.write("# build log\n")
            f.write("- Hero A instead of Hero B — because B tested worse on mobile\n")
            f.write("- TRIED sticky nav — broke on Safari, don't retry\n")
            f.write("- Used the default footer layout\n")
            f.write("- Picked serif headline\n")
        result = compute(path)
        assert result["total"] == 4, result
        assert result["divergent"] == 2, result
        assert result["flat"] == 2, result
        assert abs(result["flat_rate"] - 50.0) < 0.01, result
        print("self-test passed: 50.0% first-idea rate on synthetic 4-entry log")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--log", default="build-log.md", help="path to the build/decision log")
    p.add_argument(
        "--threshold", type=float, default=70.0,
        help="caution threshold for first-idea rate, percent (working default, see Note)",
    )
    p.add_argument("--self-test", action="store_true", help="run the synthetic-log self-check and exit")
    args = p.parse_args()

    if args.self_test:
        self_test()
        return

    if not os.path.exists(args.log):
        print(f"No log found at {args.log}.", flush=True)
        return

    report(compute(args.log), args.threshold, args.log)


if __name__ == "__main__":
    main()
