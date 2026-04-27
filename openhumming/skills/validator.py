REQUIRED_HEADINGS = [
    "# Skill:",
    "## Description",
    "## When to Use",
    "## Inputs",
    "## Procedure",
    "## Output",
]


def validate_skill_markdown(content: str) -> tuple[bool, list[str]]:
    errors = [heading for heading in REQUIRED_HEADINGS if heading not in content]
    return (not errors, errors)
