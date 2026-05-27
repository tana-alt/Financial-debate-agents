from __future__ import annotations

from pathlib import Path

from scripts.validate_agent_assets import AGENT_ASSETS, validate_assets
from src.prompt_loader import AGENT_PROMPT_FILES, build_system_prompt


def test_asset_validator_accepts_repo_assets():
    assert validate_assets() == []


def test_asset_validator_fails_on_missing_assets(tmp_path: Path):
    repo = tmp_path
    (repo / ".agents" / "skills").mkdir(parents=True)
    (repo / "src" / "prompts" / "shared").mkdir(parents=True)
    for shared in (
        "global_policy.md",
        "evidence_policy.md",
        "output_policy.md",
    ):
        (repo / "src" / "prompts" / "shared" / shared).write_text("policy", encoding="utf-8")

    errors = validate_assets(repo)

    assert errors
    assert any("missing skill asset" in error for error in errors)
    assert any("missing prompt asset" in error for error in errors)


def test_runtime_prompt_mapping_has_exactly_seven_non_index_prompts():
    assert set(AGENT_PROMPT_FILES) == set(AGENT_ASSETS)
    assert len(AGENT_PROMPT_FILES) == 7
    assert all("index" not in Path(path).parts for path in AGENT_PROMPT_FILES.values())


def test_system_prompt_includes_shared_policy_and_one_agent_prompt():
    system = build_system_prompt("EarningsQualityAnalyst", "fallback scope")

    assert "<!-- ROLE: EarningsQualityAnalyst -->" in system
    assert "# Global Agent Policy" in system
    assert "# Evidence Policy" in system
    assert "# Output Policy" in system
    assert "# EarningsQualityAnalyst" in system
    assert "# CashFlowRiskAnalyst" not in system
    assert "src/prompts/index" not in system
