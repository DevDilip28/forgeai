from pathlib import Path
from typing import Any

from forgeai.config.settings import settings


def _load_prompt(name: str, default: str) -> str:
    prompt_file = settings.forgeai_dir / "prompts" / f"{name}.md"

    if not prompt_file.exists():
        return default

    try:
        return prompt_file.read_text(encoding="utf-8")
    except OSError:
        return default


def _load_rules() -> str:
    rules_dir = settings.forgeai_dir / "rules"

    if not rules_dir.exists():
        return ""

    rules = []

    for rule_file in rules_dir.glob("*.md"):
        try:
            content = rule_file.read_text(encoding="utf-8")
            rules.append(f"## Rule: {rule_file.stem}\n{content}")
        except OSError:
            continue

    if not rules:
        return ""

    return "\n\n# User Defined Rules\n\n" + "\n\n".join(rules)


def get_config_status() -> dict[str, Any]:
    status = {
        "prompts": {
            "loaded": 0,
            "files": [],
        },
        "rules": {
            "loaded": 0,
            "files": [],
        },
    }

    prompts_dir = settings.forgeai_dir / "prompts"

    if prompts_dir.exists():
        for file in prompts_dir.glob("*.md"):
            try:
                lines = len(file.read_text(encoding="utf-8").splitlines())

                status["prompts"]["loaded"] += 1
                status["prompts"]["files"].append(
                    {
                        "name": file.name,
                        "lines": lines,
                    }
                )
            except OSError:
                continue

    rules_dir = settings.forgeai_dir / "rules"

    if rules_dir.exists():
        for file in rules_dir.glob("*.md"):
            try:
                lines = len(file.read_text(encoding="utf-8").splitlines())

                status["rules"]["loaded"] += 1
                status["rules"]["files"].append(
                    {
                        "name": file.name,
                        "lines": lines,
                    }
                )
            except OSError:
                continue

    return status


_DEFAULT_SYSTEM_PROMPT = """You are ForgeAI, an autonomous AI coding agent.

Your job is to help developers understand, modify,
debug, and build software.

Core rules:
- Understand the user's request before acting.
- Inspect relevant files before modifying them.
- Use tools only when necessary.
- Respect the current operating mode.
- Respect project rules and .gitignore.
- Never perform destructive operations without approval.
- Keep responses concise and useful.

When modifying code:
- Write clean and maintainable code.
- Follow the existing project structure and conventions.
- Handle errors appropriately.
- Consider edge cases.
- Prefer simple solutions over unnecessary complexity.
"""

_DEFAULT_CODE_REVIEW_PROMPT = """Review the following code for:

1. Bugs
2. Code quality
3. Performance
4. Security
5. Maintainability

Code:
{code}
"""

_DEFAULT_CODE_GENERATION_PROMPT = """Generate code for the following requirements:

Requirements:
{requirements}

Language:
{language}

Provide clean, maintainable code with
appropriate error handling.
"""


_base_system_prompt = _load_prompt(
    "system_prompt",
    _DEFAULT_SYSTEM_PROMPT,
)

_rules = _load_rules()

SYSTEM_PROMPT = f"{_base_system_prompt}{_rules}"

CODE_REVIEW_PROMPT = _load_prompt(
    "code_review_prompt",
    _DEFAULT_CODE_REVIEW_PROMPT,
)

CODE_GENERATION_PROMPT = _load_prompt(
    "code_generation_prompt",
    _DEFAULT_CODE_GENERATION_PROMPT,
)
