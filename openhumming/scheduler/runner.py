from openhumming.scheduler.manager import TaskManager, TaskRecord


class TaskRunner:
    def __init__(self, task_manager: TaskManager) -> None:
        self.task_manager = task_manager

    def enabled_tasks(self) -> list[TaskRecord]:
        return [task for task in self.task_manager.list_tasks() if task.enabled]
