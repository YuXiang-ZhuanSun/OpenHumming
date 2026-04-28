from openhumming.skills.manager import SkillManager
from openhumming.skills.extractor import SkillDraft
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
    assert created.status == "published"
    assert valid is True
    assert errors == []


def test_skill_manager_keeps_drafts_separate_from_published_skills(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    created = manager.create_skill_draft(
        name="Draft Workspace Reader",
        description="Draft a reusable workspace reading workflow.",
        when_to_use="Use this when a file-reading workflow should be reviewed before promotion.",
        inputs=["target path"],
        procedure=["Read the file.", "Summarize the result."],
        output="A reusable draft workflow.",
        metadata={"source": "workflow_capture", "confidence": 0.75},
    )

    published = manager.list_skills()
    drafts = manager.list_skill_drafts()

    assert created.path.parent == workspace_paths.skill_drafts_dir
    assert created.status == "draft"
    assert created.metadata["source"] == "workflow_capture"
    assert all(skill.slug != "draft_workspace_reader" for skill in published)
    assert any(skill.slug == "draft_workspace_reader" for skill in drafts)


def test_skill_manager_promotes_draft_to_published_skill(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    created = manager.create_skill_draft(
        name="Promotable Draft",
        description="A draft that should be promoted during review.",
        when_to_use="Use this when the workflow is ready to become a published skill.",
        inputs=["target path"],
        procedure=["Read the file.", "Summarize the result."],
        output="A published workflow.",
        metadata={"source": "workflow_capture", "confidence": 0.91},
    )

    promoted = manager.promote_skill_draft(
        created.slug,
        metadata={"promoted_by": "test-suite", "promotion_reason": "ready"},
    )

    assert promoted is not None
    assert promoted.status == "published"
    assert promoted.path.parent == workspace_paths.skills_dir
    assert promoted.metadata["promoted_by"] == "test-suite"
    assert not created.path.exists()
    assert (workspace_paths.skills_dir / "promotable_draft.md").exists()


def test_skill_manager_refreshes_draft_reuse_metadata(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    created = manager.create_skill_draft(
        name="Reusable Draft",
        description="Initial workflow draft.",
        when_to_use="Use this when the workflow first appears.",
        inputs=["target path"],
        procedure=["Read the file.", "Summarize the result."],
        output="A reusable draft workflow.",
        metadata={
            "source": "workflow_capture",
            "confidence": 0.72,
            "created_from_sessions": ["session-one"],
            "times_reused": 0,
            "capture_reason": "The workflow succeeded, has stable inputs, and looks reusable.",
        },
    )

    refreshed = manager.refresh_skill_draft(
        created.slug,
        draft=SkillDraft(
            name="Reusable Draft",
            description="Updated workflow draft.",
            when_to_use="Use this when the workflow repeats successfully.",
            inputs=["target path", "workspace context"],
            procedure=["Read the file.", "List nearby files.", "Summarize the result."],
            output="A refined reusable workflow.",
            metadata={
                "source": "workflow_capture",
                "confidence": 0.81,
                "created_from_sessions": ["session-two"],
                "times_reused": 0,
                "capture_reason": "The workflow succeeded, has stable inputs, and looks reusable.",
            },
        ),
    )

    assert refreshed is not None
    assert refreshed.metadata["times_reused"] == 1
    assert refreshed.metadata["confidence"] == 0.81
    assert refreshed.metadata["created_from_sessions"] == ["session-one", "session-two"]


def test_skill_manager_retrieves_relevant_skill_by_content(workspace_paths) -> None:
    manager = SkillManager(workspace_paths.skills_dir)
    results = manager.find_relevant_skills(
        "I need a mature project plan for a Python agent runtime",
        limit=2,
    )

    assert results
    assert results[0].slug == "example_skill"


def test_skill_manager_loads_nested_skill_extensions(workspace_paths) -> None:
    nested_skill = workspace_paths.skills_dir / "extensions" / "workspace" / "nested_reader.md"
    nested_skill.parent.mkdir(parents=True, exist_ok=True)
    nested_skill.write_text(
        """# Skill: Nested Reader

## Description

Read a nested skill extension.

## When to Use

Use this when validating skill packs.

## Inputs

- target path

## Procedure

1. Read the nested skill.

## Output

A loaded nested skill document.
""",
        encoding="utf-8",
    )

    manager = SkillManager(workspace_paths.skills_dir)
    skills = manager.list_skills()

    assert any(skill.slug == "nested_reader" for skill in skills)
