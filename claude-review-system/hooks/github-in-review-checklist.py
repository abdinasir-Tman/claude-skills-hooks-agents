"""PreToolUse hook (Bash): an issue moves to In Review on the Keyd Work board only when its checklist is up to date.

Blocks `gh project item-edit … --value "In Review"` (and a raw API call setting the In Review option) while the issue body
has unticked `- [ ]` boxes, unless the command says how many are left open on purpose: `# open-boxes: N` for one issue,
or `# open-boxes: 190=2 185=0` for several. N must equal the real count, so a box ticked or added later is noticed.
"""

import json
import re
import subprocess
import sys

IN_REVIEW_OPTION = "91926c4c"
ISSUE_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)")
UNTICKED = re.compile(r"^\s*[-*] \[ \] (.*)$", re.M)


def block(message: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }))
    sys.exit(0)


ITEM_EDIT = re.compile(r"\bgh\s+project\s+item-edit\b")
TO_IN_REVIEW = re.compile(r"--value[=\s]+[\"']?In[ -]Review\b")


def in_review_moves(cmd: str) -> list[str]:
    """The logical command lines that run `gh project item-edit … --value "In Review"` (or the raw API with its option).

    A mention inside quotes or backticks (docs, a heredoc being written) is not a call."""
    lines = cmd.replace("\\\n", " ").split("\n")
    moves = []
    for line in lines:
        m = ITEM_EDIT.search(line)
        if m:
            before = line[: m.start()]
            quoted = "`" in before or before.count('"') % 2 == 1 or before.count("'") % 2 == 1
            if not quoted and TO_IN_REVIEW.search(line[m.start():]):
                moves.append(line)
        elif "updateProjectV2ItemFieldValue" in line and IN_REVIEW_OPTION in line:
            moves.append(line)
    return moves


def declared(cmd: str) -> tuple[int | None, dict[str, int]]:
    m = re.search(r"#\s*open-boxes\s*:?\s*([^\n]*)", cmd)
    if not m:
        return None, {}
    text = m.group(1)
    pairs = {n: int(c) for n, c in re.findall(r"#?(\d+)\s*=\s*(\d+)", text)}
    single = re.fullmatch(r"\s*(\d+)\s*", text)
    return (int(single.group(1)) if single else None), pairs


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    cmd = (event.get("tool_input") or {}).get("command") or ""
    moves = in_review_moves(cmd)
    if not moves:
        return
    issues = sorted(set(ISSUE_URL.findall("\n".join(moves))))
    if not issues:
        block(
            "In Review check: put the issue's URL literally in the command (--url https://github.com/<org>/<repo>/issues/<n>) "
            "so its checklist can be checked before it moves to In Review."
        )
    single, pairs = declared(cmd)
    problems = []
    for owner, repo, number in issues:
        r = subprocess.run(
            ["gh", "issue", "view", number, "-R", f"{owner}/{repo}", "--json", "body", "-q", ".body"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            block(f"In Review check: could not read {owner}/{repo}#{number} ({r.stderr.strip()[:200]}). Try again.")
        open_boxes = UNTICKED.findall(r.stdout)
        allowed = pairs.get(number, single if len(issues) == 1 else None)
        if len(open_boxes) == 0 or allowed == len(open_boxes):
            continue
        shown = "\n".join(f"  - [ ] {b.strip()[:110]}" for b in open_boxes[:15])
        more = f"\n  … and {len(open_boxes) - 15} more" if len(open_boxes) > 15 else ""
        said = "none declared" if allowed is None else f"declared {allowed}"
        problems.append(f"{owner}/{repo}#{number}: {len(open_boxes)} unticked box(es), {said}:\n{shown}{more}")
    if problems:
        block(
            "In Review check failed. Tick every box the verification gate proved "
            "(gh issue edit <n> --body-file <file>). Boxes left open on purpose must be named under \"Please check\" "
            "in the report, then state their count in the command: `# open-boxes: N` (or `# open-boxes: 190=2 185=0`).\n\n"
            + "\n\n".join(problems)
        )


if __name__ == "__main__":
    main()
