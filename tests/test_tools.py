from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.tools.file_read import FileReadTool
from openhumming.tools.file_write import FileWriteTool
from openhumming.tools.list_dir import ListDirTool
from openhumming.tools.skill_read import SkillReadTool
from openhumming.tools.task_create import TaskCreateTool


def test_file_tools_round_trip(workspace_paths) -> None:
    writer = FileWriteTool(workspace_paths.root)
    reader = FileReadTool(workspace_paths.root)
    lister = ListDirTool(workspace_paths.root)

    write_result = writer.run({"path": "files/note.txt", "content": "hello"})
    read_result = reader.run({"path": "files/note.txt"})
    list_result = lister.run({"path": "files"})

    assert write_result.success is True
    assert read_result.content == "hello"
    assert any(item["name"] == "note.txt" for item in list_result.content)


def test_skill_and_task_tools(workspace_paths) -> None:
    skill_tool = SkillReadTool(SkillManager(workspace_paths.skills_dir))
    task_tool = TaskCreateTool(TaskManager(workspace_paths.tasks_file))

    skill_result = skill_tool.run({"slug": "example_skill"})
    task_result = task_tool.run({"natural_language": "每天晚上 11 点总结今天的对话"})

    assert skill_result.success is True
    assert "Create Agent Project Plan" in skill_result.content
    assert task_result.success is True
    assert task_result.metadata["id"].startswith("task_")
