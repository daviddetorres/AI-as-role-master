#!/usr/bin/env python3
"""
Build rules-prompts.md from Jinja2 templates under prompts/.
Reads prompts/rules/_index.yaml, assembles each rule from common + per-rule fragments,
renders prompts/templates/page.j2, writes rules-prompts.md (or path given as first arg).
"""
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
RULES_DIR = PROMPTS_DIR / "rules"
COMMON_DIR = PROMPTS_DIR / "common"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
OUTPUT_FILE = REPO_ROOT / "rules-prompts.md"

# Rules that include shared GM fidelity / declaration / combat-stance guidance
GM_FIDELITY_RULE_IDS = frozenset({
    "dnd",
    "dice-pool",
    "disco-elysium",
    "pokemon",
    "fallout",
    "deduction-detective",
    "system-call-world-dungeon",
})


def load_index():
    path = RULES_DIR / "_index.yaml"
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if yaml is not None:
        data = yaml.safe_load(raw)
        return data if isinstance(data, list) else []
    # Minimal parser for "- id: x\n  title: y\n  intro: z" format
    entries = []
    for m in re.finditer(
        r"-\s+id:\s*(\S+)\s*\n\s+title:\s*(.+?)\s*\n\s+intro:\s*(.+?)(?=\n\n|\n-|\Z)",
        raw,
        re.DOTALL,
    ):
        entries.append({
            "id": m.group(1).strip(),
            "title": m.group(2).strip(),
            "intro": m.group(3).strip(),
        })
    return entries


def render_fragment(env: Environment, rel_path: str, **context) -> str:
    tmpl = env.get_template(rel_path)
    return tmpl.render(**context).rstrip()


def build_prompt_body(env: Environment, rule_id: str) -> str:
    parts = []

    # opening
    opening_rel = f"rules/{rule_id}/opening.j2"
    if (RULES_DIR / rule_id / "opening.j2").exists():
        parts.append(render_fragment(env, opening_rel))

    # common phase1-base (pass rule_id for statless handling)
    parts.append(render_fragment(env, "common/phase1-base.j2", rule_id=rule_id))

    # mechanics
    mechanics_rel = f"rules/{rule_id}/mechanics.j2"
    if (RULES_DIR / rule_id / "mechanics.j2").exists():
        parts.append(render_fragment(env, mechanics_rel))

    # common phase2 (pass rule_id for changing-the-past exception)
    if (COMMON_DIR / "phase2.j2").exists():
        parts.append(render_fragment(env, "common/phase2.j2", rule_id=rule_id))
    if rule_id in GM_FIDELITY_RULE_IDS and (COMMON_DIR / "gm-fidelity-combat.j2").exists():
        parts.append(render_fragment(env, "common/gm-fidelity-combat.j2", rule_id=rule_id))
    # formatting
    if (COMMON_DIR / "formatting.j2").exists():
        parts.append(render_fragment(env, "common/formatting.j2"))
    # system-actions-core (pass rule_id for statless note)
    if (COMMON_DIR / "system-actions-core.j2").exists():
        parts.append(render_fragment(env, "common/system-actions-core.j2", rule_id=rule_id))

    # optional extra-actions
    extra_rel = f"rules/{rule_id}/extra-actions.j2"
    if (RULES_DIR / rule_id / "extra-actions.j2").exists():
        parts.append(render_fragment(env, extra_rel))

    return "\n\n".join(p for p in parts if p.strip())


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_FILE
    os.chdir(REPO_ROOT)

    index = load_index()
    if not index:
        print("No rules in _index.yaml", file=sys.stderr)
        sys.exit(1)

    # Jinja2 env: single search path = prompts/ (so common/, rules/<id>/, templates/ resolve)
    env = Environment(
        loader=FileSystemLoader([str(PROMPTS_DIR)]),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    rules = []
    for entry in index:
        rule_id = entry["id"]
        title = entry["title"]
        intro = entry.get("intro", "")
        prompt_body = build_prompt_body(env, rule_id)
        rules.append({
            "title": title,
            "intro": intro,
            "prompt_body": prompt_body,
        })

    page_tmpl = env.get_template("templates/page.j2")
    output = page_tmpl.render(rules=rules)

    out_path.write_text(output, encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
