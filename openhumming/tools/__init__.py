from openhumming.scheduler.manager import TaskManager
from openhumming.skills.manager import SkillManager
from openhumming.tools.file_read import FileReadTool
from openhumming.tools.file_write import FileWriteTool
from openhumming.tools.list_dir import ListDirTool
from openhumming.tools.registry import ToolRegistry
from openhumming.tools.skill_create import SkillCreateTool
from openhumming.tools.skill_read import SkillReadTool
from openhumming.tools.task_create import TaskCreateTool
from openhumming.workspace.paths import WorkspacePaths


def build_default_registry(
    paths: WorkspacePaths,
    skill_manager: SkillManager,
    task_manager: TaskManager,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FileReadTool(paths.root))
    registry.register(FileWriteTool(paths.root))
    registry.register(ListDirTool(paths.root))
    registry.register(SkillReadTool(skill_manager))
    registry.register(SkillCreateTool(skill_manager))
    registry.register(TaskCreateTool(task_manager))
    return registry
