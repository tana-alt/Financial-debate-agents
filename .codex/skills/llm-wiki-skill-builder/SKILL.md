---
name: llm-wiki-skill-builder
description: Use when an agent needs to convert LLM wiki raw research records into a structured, ready-to-use Codex skill draft. Trigger this skill for transforming raw observations, source-linked notes, and research captures into canonical `.codex/skills` skill files with proper frontmatter, workflow steps, and output rules.
---

# LLM Wiki Skill Builder

Convert raw LLM wiki research records into a practical skill draft that follows the current Codex skill layout.

## When to Use

- A raw research note or source-linked observation set needs to become a skill.
- You are handed source-linked observations and must produce SKILL.md + agents/openai.yaml.
- A new skill must target the repo's current `.codex/skills/<skill-name>/` layout.

## Workflow

1. Read the raw research note to extract observations and source references.
2. Identify the skill name, trigger contexts, and core workflow from the observations.
3. Write SKILL.md with YAML frontmatter (`name`, `description`) and a concise imperative body.
4. Write agents/openai.yaml with `display_name`, `short_description`, and `default_prompt`.
5. Place the files under `.codex/skills/<skill-name>/`.
6. Validate: frontmatter has `name` + `description`, body is under 500 lines, no extraneous files.

## What to Read

- The raw note, research capture, or source-linked observations at the path provided.
- An existing skill for structural reference (e.g., `.codex/skills/agent-visibility-skill/SKILL.md`).
- The skill-creator guide at `~/.codex/skills/.system/skill-creator/SKILL.md` for anatomy rules.

## Content Rules

- Put all trigger information in the frontmatter `description`, not in the body.
- Use imperative/infinitive form throughout.
- Keep the body concise and action-oriented -- under 500 lines, under 5k words.
- Only create SKILL.md and agents/openai.yaml per skill directory. No README, CHANGELOG, or extras.
- Use ASCII only in all generated files.

## Output Rules

- Produce exactly two files in `.codex/skills/<skill-name>/`: `SKILL.md` and `agents/openai.yaml`.
- Report which files were created and confirm the skill name.
