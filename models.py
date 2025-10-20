from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Robot:
    id: Optional[int] = None
    model: str = ""
    robot_sn: str = ""
    controller_sn: str = ""
    status: str = ""
    fault_description: str = ""
    fault_reason: str = ""
    tasks_done: str = ""
    tasks_required: str = ""
    required_parts: str = ""
    notes: str = ""


    def to_dict(self):
        return {
            "id": self.id,
            "model": self.model,
            "robot_sn": self.robot_sn,
            "controller_sn": self.controller_sn,
            "status": self.status,
            "fault_description": self.fault_description,
            "fault_reason": self.fault_reason,
            "tasks_done": self.tasks_done,
            "tasks_required": self.tasks_required,
            "required_parts": self.required_parts,
            "notes": self.notes,
            }


    @classmethod
    def from_row(cls, row: dict):
    # row - dict from RealDictCursor or similar
        return cls(
            id=row.get("id"),
            model=row.get("model", ""),
            robot_sn=row.get("robot_sn", ""),
            controller_sn=row.get("controller_sn", ""),
            status=row.get("status", ""),
            fault_description=row.get("fault_description", ""),
            fault_reason=row.get("fault_reason", ""),
            tasks_done=row.get("tasks_done", ""),
            tasks_required=row.get("tasks_required", ""),
            required_parts=row.get("required_parts", ""),
            notes=row.get("notes", ""),
            )
