from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_yaml(relative_path: str) -> dict[str, Any]:
    raw_data: object = yaml.safe_load(read_text(relative_path))
    assert isinstance(raw_data, dict), relative_path
    return cast(dict[str, Any], raw_data)


def section_body(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    start = markdown.index(marker)
    following_heading = markdown.find("\n## ", start + len(marker))
    if following_heading == -1:
        return markdown[start:]
    return markdown[start:following_heading]


def test_system_design_skill_exists_is_conditional_and_compact() -> None:
    skill_path = ROOT / ".agents" / "skills" / "system-design" / "SKILL.md"
    assert skill_path.is_file()

    skill = skill_path.read_text(encoding="utf-8")
    assert len(skill.splitlines()) <= 80

    for required_text in (
        "name: system-design",
        "## Purpose",
        "## Use when",
        "## Do not use when",
        "## Required design packet",
        "## Stop conditions",
        "## Constraints",
        "## Output",
        "design_verdict",
        "architecture_significance",
        "skill_refs_used",
    ):
        assert required_text in skill

    index = read_text(".agents/skills/SKILL_INDEX.md")
    conditional_skills = section_body(index, "Conditional skills")
    assert "- `system-design`" in conditional_skills


def test_system_design_does_not_expand_active_docs() -> None:
    forbidden_docs = (
        "docs/04-system-design-contract.md",
        "docs/system-design.md",
        "docs/architecture-principles.md",
        "docs/adr-guidelines.md",
    )

    for relative_path in forbidden_docs:
        assert not (ROOT / relative_path).exists(), relative_path

    for relative_path in ("docs/adr", "docs/design"):
        assert not (ROOT / relative_path).exists(), relative_path

    agents = read_text("AGENTS.md")
    assert "`docs/04-system-design-contract.md`" not in agents
    assert "`docs/system-design.md`" not in agents


def test_work_contract_has_simplified_design_gate() -> None:
    work_contract = read_yaml("templates/work-contract.yaml")
    design_gate = work_contract.get("design_gate")

    assert isinstance(design_gate, dict)
    assert set(design_gate) == {
        "architecture_significance",
        "system_design_skill_required",
        "reason",
    }
    assert design_gate.get("architecture_significance") in {"none", "local", "significant"}
    assert isinstance(design_gate.get("system_design_skill_required"), bool)
    assert isinstance(design_gate.get("reason"), str)
    assert design_gate.get("reason", "").strip()


def test_design_record_template_and_plan_design_roots_are_deferred() -> None:
    assert not (ROOT / "templates" / "design-record.yaml").exists()

    plan_design_roots = sorted((ROOT / "Plan").glob("*/design"))
    assert plan_design_roots == []
