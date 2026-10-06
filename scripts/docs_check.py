"""Read-only check of the Markdown docs in this repo. Standard library only.

Checks:
1. Every relative link in a .md file points to a file (and to a heading, if it has `#anchor`).
2. Every `just <name>` in README.md and docs/ names a recipe in `just --summary`.
3. Every path in backticks (with a file extension, or a trailing `/`) exists in the repo.
4. README.md has no template placeholder (`<name>`), unless allowed.

Run: `just docs-check`. Exit code 1 when a check finds a problem.
Allow-list: `docs/.docs-check-ignore`. One glob per line, `#` starts a comment.
The line `placeholders: allowed` turns off check 4 (for template repos).
The line `skip: <glob>` skips whole files (a doc written ahead of code: remove the line later).
Paths that start with `standards/`, `coordination/` or `_reports/` live in a separate docs repository that is not part of this template: not checked.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORE_FILE = ROOT / "docs" / ".docs-check-ignore"
SKIP_DIRS = {"node_modules", ".venv", ".git", ".pytest_cache", "dist", "build"}
FENCE = re.compile(r"^\s*```")
LINK = re.compile(r"\]\(([^)\s]{1,500})\)")  # the cap keeps a line of "](" linear
SPAN = re.compile(r"`([^`\n]+)`")
JUST_CMD = re.compile(r"(?<![\w-])just\s+([a-z][\w-]*)")
PATHLIKE = re.compile(r"^[\w./-]+(\.(py|tsx?|ya?ml|toml|json|md|ps1|db|csv)|/)$")
BRANCH_PREFIXES = ("feat/", "fix/", "chore/")
OUTSIDE = ("standards/", "coordination/", "_reports/", "writing-style.md")
PLACEHOLDERS = ("<name>", "<One sentence")
MAX_LINE = 20_000  # a longer line is reported, not scanned (the regexes stay fast)
MAX_BYTES = 2_000_000


def tracked_markdown() -> list[Path]:
    """List the .md files that git tracks or would track. Fall back to a directory walk."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [ROOT / line for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [
            p for p in ROOT.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(ROOT).parts)
        ]


def all_repo_paths() -> set[str]:
    """Every path in the repo and each of its tails (`a/b/c.py`, `b/c.py`, `c.py`).

    A folder ends with `/`. A set lookup replaces a scan of all paths for each backtick span.
    """
    found: set[str] = set()
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if SKIP_DIRS.intersection(rel.parts):
            continue
        parts = list(rel.parts)
        tail = "/" if p.is_dir() else ""
        for i in range(len(parts)):
            found.add("/".join(parts[i:]) + tail)
    return found


def read_lines(path: Path) -> list[str] | None:
    """Read a text file. Return None when it is unreadable, not UTF-8, or too big.

    A tracked symlink that points outside the repo is still read. Only line numbers and
    link text reach the output, never the file text.
    """
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return False
    return True


def read_ignore() -> tuple[list[str], bool, list[str]]:
    patterns: list[str] = []
    placeholders_ok = False
    skips: list[str] = []
    if IGNORE_FILE.exists():
        raw_lines = read_lines(IGNORE_FILE)
        if raw_lines is None:
            raise SystemExit("docs-check: cannot read docs/.docs-check-ignore")
        for raw in raw_lines:
            line = raw.split("#", 1)[0].strip()
            if line.startswith("skip:"):
                skips.append(line.removeprefix("skip:").strip())
            elif line == "placeholders: allowed":
                placeholders_ok = True
            elif line:
                patterns.append(line)
    return patterns, placeholders_ok, skips


def recipes() -> set[str] | None:
    try:
        out = subprocess.run(
            ["just", "--summary"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return set(out.split())


def slug(heading: str) -> str:
    text = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s", "-", text)


def headings(path: Path) -> set[str]:
    found: set[str] = set()
    in_fence = False
    for line in read_lines(path) or []:
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.startswith("#"):
            found.add(slug(line.lstrip("#")))
    return found


def check_link(md: Path, target: str) -> str | None:
    if target.startswith(("http:", "https:", "mailto:", "#", "<")) or "standards/" in target:
        return None
    name, _, anchor = target.partition("#")
    name = name.split("?", 1)[0]
    dest = ROOT / name.lstrip("/") if name.startswith("/") else md.parent / name
    if not inside_root(dest):
        return f"link outside the repo: {target}"
    if not dest.exists():
        return f"broken link: {target}"
    if anchor and dest.suffix == ".md" and slug(anchor) not in headings(dest):
        return f"broken anchor: {target}"
    return None


def path_exists(md: Path, token: str, known: set[str]) -> bool:
    token = token.removeprefix("./")
    if token in BRANCH_PREFIXES or token.startswith(("/", *OUTSIDE)):
        return True  # a branch prefix, a URL path or a path in a separate docs repository
    for dest in (ROOT / token, md.parent / token):
        if inside_root(dest) and dest.exists():
            return True
    return token in known


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # a non-ASCII name must not crash a narrow console
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(errors="backslashreplace")
    patterns, placeholders_ok, skips = read_ignore()
    names = recipes()
    known = all_repo_paths()
    problems: list[str] = []
    if names is None:
        print(
            "note: `just` not found, so the `just <name>` check is skipped",
            file=sys.stderr,
        )

    def ignored(token: str) -> bool:
        return any(fnmatch.fnmatch(token, pat) for pat in patterns)

    for md in tracked_markdown():
        rel = md.relative_to(ROOT).as_posix()
        if any(fnmatch.fnmatch(rel, pat) for pat in skips):
            continue
        in_fence = False
        check_just = rel in ("README.md",) or rel.startswith("docs/")
        lines = read_lines(md)
        if lines is None:
            problems.append(f"{rel}: unreadable (not UTF-8 text, too big, or not a file)")
            continue
        for number, line in enumerate(lines, 1):
            if FENCE.match(line):
                in_fence = not in_fence
                continue

            def report(msg: str, n: int = number, where: str = rel) -> None:
                problems.append(f"{where}:{n}: {msg}")

            if len(line) > MAX_LINE:
                report("line too long to check")
                continue

            if in_fence:
                spans = [line] if line.lstrip().startswith("just ") else []
            else:
                spans = SPAN.findall(line)
                for target in LINK.findall(line):
                    if not ignored(target) and (msg := check_link(md, target)):
                        report(msg)
            for span in spans:
                if check_just and names is not None:
                    for cmd in JUST_CMD.findall(span):
                        if cmd not in names and not ignored("just " + cmd):
                            report(f"`just {cmd}` is not a recipe in the justfile")
                if (
                    not in_fence
                    and PATHLIKE.match(span)
                    and not ignored(span)
                    and not path_exists(md, span, known)
                ):
                    report(f"path not found: {span}")
            if (
                rel in ("README.md",)
                and not placeholders_ok
                and any(p in line for p in PLACEHOLDERS)
            ):
                report("template placeholder is still in the file")

    for problem in problems:
        print(problem)
    print(f"docs-check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
