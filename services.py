from typing import List, Dict, Any, Optional
from db import RobotRepository, HistoryRepository, Database

class RobotService:
    def __init__(self, robot_repo: RobotRepository, history_repo: HistoryRepository):
        self.robot_repo = robot_repo
        self.history_repo = history_repo

    # Работа с таблицами
    def init_db(self):
        self.robot_repo.init_db()

    # CRUD
    def get_all_robots(self) -> List[Dict[str, Any]]:
        return self.robot_repo.get_all()

    def add_robot(self, data: Dict[str, Any]) -> int:
        robot_id = self.robot_repo.add(data)
        self.history_repo.log_action(robot_id, "Добавлен робот")
        return robot_id

    def update_robot(self, robot_id: int, field: str, new_value: Any, old_value: Any = None):
        self.robot_repo.update(robot_id, field, new_value)
        self.history_repo.log_action(robot_id, "Изменение", field, old_value, new_value)

    def delete_robot(self, robot_id: int):
        self.robot_repo.delete(robot_id)
        self.history_repo.log_action(robot_id, "Удалён робот")

    # История
    def log_action(
        self,
        robot_id: int,
        action: str,
        field: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ):
        self.history_repo.log_action(robot_id, action, field, old_value, new_value)

    def get_history(self, robot_id: Optional[int] = None):
        return self.history_repo.get_history(robot_id)

    def clear_history(self):
        self.history_repo.clear_db_history()


