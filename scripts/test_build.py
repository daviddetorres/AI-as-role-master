"""
Tests for rules-prompts build: output structure, no stray template syntax,
required sections in prompt body, manifest vs fragment consistency.
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
RULES_DIR = PROMPTS_DIR / "rules"
OUTPUT_FILE = REPO_ROOT / "rules-prompts.md"


def run_build(output_path: Optional[Path] = None) -> str:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "build.py")]
    if output_path is not None:
        cmd.append(str(output_path))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    path = output_path if output_path is not None else OUTPUT_FILE
    return path.read_text(encoding="utf-8")


def load_index():
    raw = (RULES_DIR / "_index.yaml").read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(
        r"-\s+id:\s*(\S+)\s*\n\s+title:\s*(.+?)\s*\n\s+intro:\s*(.+?)(?=\n\n|\n-|\Z)",
        raw,
        re.DOTALL,
    ):
        entries.append({"id": m.group(1).strip(), "title": m.group(2).strip()})
    return entries


class TestBuildRuns:
    """Build runs and produces non-empty output."""

    def test_build_produces_output(self, tmp_path):
        out = tmp_path / "rules-prompts.md"
        content = run_build(out)
        assert out.exists()
        assert len(content.strip()) > 0

    def test_build_writes_to_default_path(self):
        run_build()
        assert OUTPUT_FILE.exists()
        assert OUTPUT_FILE.read_text(encoding="utf-8").strip()


class TestOutputStructure:
    """Output has expected title, sections, and details blocks."""

    @pytest.fixture
    def built(self, tmp_path):
        run_build(tmp_path / "out.md")
        return (tmp_path / "out.md").read_text(encoding="utf-8")

    def test_starts_with_title(self, built):
        assert built.strip().startswith("# Rules prompts")

    def test_each_rule_has_section_and_details(self, built):
        index = load_index()
        for entry in index:
            title = entry["title"]
            assert f"## {title}" in built, f"Missing section for {title}"
            # One details block per section (simple check: count of <details> equals rules)
        assert built.count("<details>") == len(index)
        assert built.count("</details>") == len(index)

    def test_each_details_has_one_md_code_block(self, built):
        # Each <details> should contain exactly one ```md ... ```
        blocks = re.findall(r"<details>.*?```md(.*?)```.*?</details>", built, re.DOTALL)
        index = load_index()
        assert len(blocks) == len(index)
        for block in blocks:
            assert block.strip(), "Code block should be non-empty"


class TestNoStrayTemplateSyntax:
    """Compiled output must not contain unprocessed {{ or }}."""

    def test_no_double_braces(self, tmp_path):
        run_build(tmp_path / "out.md")
        content = (tmp_path / "out.md").read_text(encoding="utf-8")
        assert "{{" not in content, "Output should not contain {{"
        assert "}}" not in content, "Output should not contain }}"


class TestRequiredSectionsInPromptBody:
    """Each prompt body includes key phrases."""

    @pytest.fixture
    def built(self, tmp_path):
        run_build(tmp_path / "out.md")
        return (tmp_path / "out.md").read_text(encoding="utf-8")

    def test_prompt_bodies_contain_phase1_and_phase2(self, built):
        blocks = re.findall(r"```md(.*?)```", built, re.DOTALL)
        for block in blocks:
            assert "Phase 1" in block or "Phase 2" in block, "Prompt should mention Phase 1 or Phase 2"
            assert "System actions" in block, "Prompt should include System actions"

    def test_prompt_bodies_contain_save_and_help(self, built):
        blocks = re.findall(r"```md(.*?)```", built, re.DOTALL)
        for block in blocks:
            assert "@save" in block
            assert "@help" in block


class TestManifestAndFragmentsConsistent:
    """Every rule in _index has opening.j2 and mechanics.j2; no extra dirs."""

    def test_every_index_entry_has_dir_with_opening_and_mechanics(self):
        index = load_index()
        for entry in index:
            rule_id = entry["id"]
            rule_dir = RULES_DIR / rule_id
            assert rule_dir.is_dir(), f"Missing directory for rule {rule_id}"
            assert (rule_dir / "opening.j2").exists(), f"Missing opening.j2 for {rule_id}"
            assert (rule_dir / "mechanics.j2").exists(), f"Missing mechanics.j2 for {rule_id}"

    def test_no_extra_rule_dirs(self):
        index_ids = {e["id"] for e in load_index()}
        for path in RULES_DIR.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                assert path.name in index_ids, f"Directory {path.name} not in _index.yaml"
