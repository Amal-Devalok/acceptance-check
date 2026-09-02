#!/usr/bin/env python3
"""
session_check.py — acceptance tracking with zero user effort, for people who
don't write code and don't keep a log: they just work through Claude Code,
Figma MCP, and Framer MCP, and see what gets made.

Neither git (design_check.py's sibling, acceptance_check.py) nor a
hand-maintained build-log (design_check.py) fits this case — there's no
commit trail if the user never touches git, and asking a non-coder to jot
one-liners is the exact friction this whole project exists to avoid.

So this one has no external system at all. Claude keeps the tally itself,
live, in a small hidden file (`.acceptance-tally.json` by default) that the
user never opens or edits — the same kind of invisible bookkeeping quick-share
uses to survive context compaction, not a log anyone is asked to maintain.

The classification itself — did the user accept what Claude proposed, or ask
for something different — is a judgment call only Claude can make in the
moment (tone, "looks good" vs "actually try..."), so it can't be scripted.
This script only does the mechanical half: append an event, and report the
tally. See SKILL.md for the classification protocol Claude follows.
"""
import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone


def load(path):
    if not os.path.exists(path):
        return {"events": []}
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record(path, surface, summary, reaction):
    if reaction not in ("accept", "revise"):
        raise ValueError('reaction must be "accept" or "revise"')
    data = load(path)
    data["events"].append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "surface": surface,
        "summary": summary,
        "reaction": reaction,
    })
    save(path, data)
    return data


def compute(data):
    events = data.get("events", [])
    if not events:
        return {"total": 0}
    accept = sum(1 for e in events if e["reaction"] == "accept")
    revise = len(events) - accept
    return {"total": len(events), "accept": accept, "revise": revise,
            "rate": accept / len(events) * 100}


def report(result, threshold, path):
    if result["total"] == 0:
        print(f"No tallied events yet at {path}. Nothing to report.")
        return
    print(f"Session tally: {path}")
    print(f"Proposals: {result['total']}   Accepted as-is: {result['accept']}   Revised: {result['revise']}")
    print(f"Acceptance rate: {result['rate']:.1f}%")
    if result["rate"] >= threshold:
        print(
            f"\n⚠ Above the {threshold:.0f}% caution line — same pattern flagged in Copilot productivity "
            "research and the vibe-coding studies this workflow is built on: very high, unreviewed "
            "acceptance correlates with review stopping in practice, not just in code."
        )
    else:
        print(f"\nBelow the {threshold:.0f}% caution line.")
    print(
        "\nNote: this rate reflects Claude's own read of your reactions, not an independent "
        "measurement — treat it as a rough signal, and say so if a count looks wrong; a corrected "
        "tally is more useful than a precise-looking wrong one."
    )


def self_test():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "tally.json")
        record(path, "webpage", "hero section draft", "accept")
        record(path, "figma", "nav variant", "accept")
        record(path, "framer", "pricing table", "revise")
        record(path, "webpage", "footer", "accept")
        data = load(path)
        result = compute(data)
        assert result["total"] == 4, result
        assert result["accept"] == 3, result
        assert result["revise"] == 1, result
        assert abs(result["rate"] - 75.0) < 0.01, result
        print("self-test passed: 75.0% acceptance rate on synthetic 4-event tally")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", default=".acceptance-tally.json", help="tally file path")
    p.add_argument("--threshold", type=float, default=90.0, help="caution threshold, percent")
    p.add_argument("--record", action="store_true", help="append one event instead of reporting")
    p.add_argument("--surface", choices=["webpage", "figma", "framer"], help="required with --record")
    p.add_argument("--summary", help="short description of what was proposed, required with --record")
    p.add_argument("--reaction", choices=["accept", "revise"], help="required with --record")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        self_test()
        return

    if args.record:
        if not (args.surface and args.summary and args.reaction):
            p.error("--record needs --surface, --summary, and --reaction")
        record(args.file, args.surface, args.summary, args.reaction)
        print(f"Recorded: [{args.surface}] {args.summary} -> {args.reaction}")
        return

    report(compute(load(args.file)), args.threshold, args.file)


if __name__ == "__main__":
    main()
