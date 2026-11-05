"""PreToolUse hook (Bash): an issue moves to In Dev on the Keyd Work board only when its spec is written.

Blocks `gh project item-edit … --value "In Dev"` (and a raw API call setting the In Dev option) while the issue body
still has `_To be filled after analysis_`, or a `### Query plan` / `### Data loading plan` section with nothing in it.
Analysis ends with a complete body; data access is planned before any code (github-issues §3, data-access skill).
"""

import json
import re
import subprocess
import sys

IN_DEV_OPTION = "47fc9ee4"
ISSUE_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)")
PLACEHOLDER = "_To be filled after analysis_"
ITEM_EDIT = re.compile(r"\bgh\s+project\s+item-edit\b")
TO_IN_DEV = re.compile(r"--value[=\s]+[\"']?In[ -]Dev\b")
PLAN_SECTION = re.compile(r"^###\s+(Query plan|Data loading plan)\b[^\n]*\n(.*?)(?=^#{2,3}\s|\Z)", re.M | re.S)
HEADING = re.compile(r"^#{2,3}\s+(.+)$", re.M)


def block(message: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }))
    sys.exit(0)


def in_dev_moves(cmd: str) -> list[str]:
    """The logical command lines that run `gh project item-edit … --value "In Dev"` (or the raw API with its option).

    A mention inside quotes or backticks (docs, a heredoc being written) is not a call."""
    moves = []
    for line in cmd.replace("\\\n", " ").split("\n"):
        m = ITEM_EDIT.search(line)
        if m:
            before = line[: m.start()]
            quoted = "`" in before or before.count('"') % 2 == 1 or before.count("'") % 2 == 1
            if not quoted and TO_IN_DEV.search(line[m.start():]):
                moves.append(line)
        elif "updateProjectV2ItemFieldValue" in line and IN_DEV_OPTION in line:
            moves.append(line)
    return moves


def problems_in(body: str) -> list[str]:
    found = []
    if PLACEHOLDER in body:
        sections = []
        for m in re.finditer(re.escape(PLACEHOLDER), body):
            heads = HEADING.findall(body[: m.start()])
            sections.append(heads[-1].strip()[:60] if heads else "top of the body")
        found.append(f"still says {PLACEHOLDER} under: " + ", ".join(dict.fromkeys(sections)))
    for name, content in PLAN_SECTION.findall(body):
        if not content.strip():
            found.append(f"'### {name}' is empty (write the table, or 'Not applicable — no data access')")
    return found


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    cmd = (event.get("tool_input") or {}).get("command") or ""
    moves = in_dev_moves(cmd)
    if not moves:
        return
    issues = sorted(set(ISSUE_URL.findall("\n".join(moves))))
    if not issues:
        block(
            "In Dev check: put the issue's URL literally in the command (--url https://github.com/<org>/<repo>/issues/<n>) "
            "so its spec can be checked before it moves to In Dev."
        )
    problems = []
    for owner, repo, number in issues:
        r = subprocess.run(
            ["gh", "issue", "view", number, "-R", f"{owner}/{repo}", "--json", "body", "-q", ".body"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            block(f"In Dev check: could not read {owner}/{repo}#{number} ({r.stderr.strip()[:200]}). Try again.")
        for p in problems_in(r.stdout):
            problems.append(f"{owner}/{repo}#{number}: {p}")
    if problems:
        block(
            "In Dev check failed: finish the Analysis first — complete the body (work plan, acceptance criteria, design, "
            "and for data access the Query plan / Data loading plan tables per the data-access skill), then move it.\n\n"
            + "\n".join(problems)
        )


if __name__ == "__main__":
    main()
