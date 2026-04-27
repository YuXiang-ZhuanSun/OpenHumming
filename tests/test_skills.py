from openhumming.skills.manager import SkillManager
from openhumming.skills.validator import validate_skill_markdown


def test_skill_manager_lists_and_creates_skills(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    existing = manager.list_skills()

    assert any(skill.slug == "example_skill" for skill in existing)

    created = manager.create_skill(
        name="Debug FastAPI Server",
        description="Debug a local FastAPI application.",
        when_to_use="Use this when the user reports an HTTP or startup issue.",
        inputs=["error logs", "entrypoint", "reproduction steps"],
        procedure=["Inspect the failing entrypoint.", "Reproduce the error.", "Fix and retest."],
        output="A diagnosis and validated fix.",
    )
    valid, errors = validate_skill_markdown(created.content)

    assert created.path.exists()
    assert valid is True
    assert errors == []


def test_skill_manager_retrieves_relevant_skill_by_content(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    results = manager.find_relevant_skills(
        "I need a mature project plan for a Python agent runtime",
        limit=2,
    )

    assert results
    assert results[0].slug == "example_skill"
