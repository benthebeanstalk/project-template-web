"""Tests for scripts/docs_check.py. They build small fake repos in a temp folder. No network."""

import importlib.util
import io
import os
import sys
import time
from pathlib import Path

import pytest

SCRIPT = next(
    p / "scripts" / "docs_check.py"
    for p in Path(__file__).resolve().parents
    if (p / "scripts" / "docs_check.py").exists()
)


@pytest.fixture
def check(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("docs_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "IGNORE_FILE", tmp_path / "docs" / ".docs-check-ignore")
    monkeypatch.setattr(module, "recipes", lambda: {"setup", "test"})
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n\n## Run it\n", encoding="utf-8")
    return module


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(check, capsys):
    code = check.main()
    return code, capsys.readouterr().out


def test_clean_repo_passes(check, tmp_path, capsys):
    write(
        tmp_path,
        "README.md",
        "# App\n\nRun `just setup`. See [guide](docs/guide.md#run-it).\n",
    )
    code, out = run(check, capsys)
    assert code == 0
    assert "0 problem" in out


def test_broken_link_is_reported(check, tmp_path, capsys):
    write(tmp_path, "README.md", "See [gone](docs/gone.md).\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "README.md:1: broken link: docs/gone.md" in out


def test_broken_anchor_is_reported(check, tmp_path, capsys):
    write(tmp_path, "README.md", "See [x](docs/guide.md#nope).\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "broken anchor" in out


def test_unknown_just_recipe_is_reported(check, tmp_path, capsys):
    write(tmp_path, "README.md", "Run `just dev` to start.\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "`just dev` is not a recipe" in out


def test_just_in_prose_and_known_recipe_are_fine(check, tmp_path, capsys):
    write(tmp_path, "README.md", "We just add tests. Run `just test` and `just --list`.\n")
    code, _ = run(check, capsys)
    assert code == 0


def test_missing_path_is_reported_and_fence_is_skipped(check, tmp_path, capsys):
    write(tmp_path, "docs/a.md", "Edit `app/gone.py`.\n\n```\n`app/other.py`\n```\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "app/gone.py" in out
    assert "other.py" not in out


def test_existing_path_matches_by_suffix(check, tmp_path, capsys):
    write(tmp_path, "backend/app/config.py", "")
    write(tmp_path, "docs/a.md", "See `app/config.py` and `backend/`.\n")
    code, _ = run(check, capsys)
    assert code == 0


def test_dev_docs_paths_and_branch_prefixes_are_not_checked(check, tmp_path, capsys):
    write(
        tmp_path,
        "docs/a.md",
        "See `standards/web.md`, `coordination/plan.md`, `fix/`.\n",
    )
    code, _ = run(check, capsys)
    assert code == 0


def test_placeholder_is_reported_unless_allowed(check, tmp_path, capsys):
    write(tmp_path, "README.md", "# <name>\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "placeholder" in out
    write(tmp_path, "docs/.docs-check-ignore", "placeholders: allowed\n")
    code, _ = run(check, capsys)
    assert code == 0


def test_ignore_patterns_and_skip_lines(check, tmp_path, capsys):
    write(tmp_path, "docs/a.md", "Data is in `data/app.db`. Run `just soon`.\n")
    write(tmp_path, "docs/b.md", "See `app/missing.py`.\n")
    write(
        tmp_path,
        "docs/.docs-check-ignore",
        "data/*  # runtime\njust soon\nskip: docs/b.md\n",
    )
    code, _ = run(check, capsys)
    assert code == 0


def test_link_outside_the_repo_is_reported(check, tmp_path, capsys):
    (tmp_path.parent / "secret.md").write_text("# Secret\n", encoding="utf-8")
    write(tmp_path, "README.md", "See [x](../secret.md#secret).\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "link outside the repo" in out


@pytest.mark.skipif(os.name != "nt", reason="only a drive-letter path is absolute on Windows")
def test_drive_letter_link_is_outside_the_repo(check, tmp_path):
    outside = tmp_path.parent / "abs.md"
    outside.write_text("# Abs\n", encoding="utf-8")
    msg = check.check_link(tmp_path / "README.md", outside.as_posix())
    assert msg is not None
    assert "outside the repo" in msg


def test_leading_slash_link_is_relative_to_the_repo_root(check, tmp_path):
    # GitHub reads "/docs/x.md" as repo-root-relative, so it is safe, on every platform.
    assert check.check_link(tmp_path / "docs" / "a.md", "/docs/guide.md#run-it") is None
    msg = check.check_link(tmp_path / "docs" / "a.md", "/docs/gone.md")
    assert msg == "broken link: /docs/gone.md"


def test_path_outside_the_repo_is_not_a_match(check, tmp_path, capsys):
    (tmp_path.parent / "secret.md").write_text("# Secret\n", encoding="utf-8")
    write(tmp_path, "docs/a.md", "See `../../secret.md`.\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "path not found" in out


def test_bad_encoding_and_folder_named_md_are_reported(check, tmp_path, capsys):
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe\x00bad")
    (tmp_path / "dir.md").mkdir()
    code, out = run(check, capsys)
    assert code == 1
    assert "bad.md: unreadable" in out
    assert "dir.md: unreadable" in out
    assert str(tmp_path) not in out


def test_file_over_the_size_cap_is_reported(check, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(check, "MAX_BYTES", 10)
    write(tmp_path, "README.md", "x" * 100 + "\n")
    code, out = run(check, capsys)
    assert code == 1
    assert "README.md: unreadable" in out


def test_unreadable_ignore_file_stops_the_check(check, tmp_path):
    (tmp_path / "docs" / ".docs-check-ignore").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SystemExit):
        check.main()


@pytest.mark.parametrize("repeat", [9_000, 50_000])
def test_pathological_line_is_fast(check, tmp_path, capsys, repeat):
    write(tmp_path, "README.md", "](" * repeat + "\n")
    start = time.perf_counter()
    code, out = run(check, capsys)
    assert time.perf_counter() - start < 5
    assert code in (0, 1)
    if repeat > 10_000:
        assert "line too long" in out


def test_non_ascii_link_does_not_crash_a_narrow_stdout(check, tmp_path, monkeypatch):
    write(tmp_path, "README.md", "See [x](数据.md).\n")
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)
    code = check.main()
    stream.flush()
    assert code == 1
    assert b"\\u6570" in raw.getvalue()
    assert b"1 problem" in raw.getvalue()


def test_link_target_over_the_cap_is_not_scanned(check, tmp_path, capsys):
    write(tmp_path, "README.md", "[x](" + "a" * 501 + ").\n")
    code, _ = run(check, capsys)
    assert code == 0
    write(tmp_path, "README.md", "[x](" + "a" * 100 + ").\n")
    code, _ = run(check, capsys)
    assert code == 1
