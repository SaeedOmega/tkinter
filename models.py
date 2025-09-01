
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional, Iterable, Dict, Any
from datetime import date, datetime

@dataclass
class Task:
    title: str
    is_done: bool = False
    priority: str = "Medium"  # Low, Medium, High
    created_date: str = ""
    due_date: str = ""  # YYYY-MM-DD

    def __post_init__(self):
        # Normalize dates to YYYY-MM-DD
        if not self.created_date:
            self.created_date = date.today().isoformat()
        else:
            self.created_date = self._normalize_date(self.created_date)
        if self.due_date:
            self.due_date = self._normalize_date(self.due_date)
        else:
            self.due_date = self._normalize_date(date.today().isoformat())

    @staticmethod
    def _normalize_date(d: str) -> str:
        # Accepts 'YYYY-MM-DD' or other parsable formats
        try:
            return datetime.fromisoformat(d).date().isoformat()
        except ValueError:
            # Try common formats
            for fmt in ("%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y.%m.%d"):
                try:
                    return datetime.strptime(d, fmt).date().isoformat()
                except ValueError:
                    continue
            raise

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ToDoList:
    def __init__(self):
        self._tasks: List[Task] = []

    # --- Required API ---
    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove first task matching title. Returns True if removed."""
        for i, t in enumerate(self._tasks):
            if t.title == title:
                del self._tasks[i]
                return True
        return False

    def list_tasks(self) -> List[Task]:
        return list(self._tasks)

    def list_by_date(self, target_date: str) -> List[Task]:
        target_date = Task._normalize_date(target_date)
        return [t for t in self._tasks if t.due_date == target_date]

    def save_to_file(self, filename: str) -> None:
        from utils import save_tasks_jsonl
        save_tasks_jsonl(filename, self._tasks)

    def load_from_file(self, filename: str) -> None:
        from utils import load_tasks_jsonl
        self._tasks = load_tasks_jsonl(filename)

    # --- Helpers ---
    def filter(self, *, priority: Optional[str] = None, due_from: Optional[str] = None, due_to: Optional[str] = None) -> List[Task]:
        items = self._tasks
        if priority:
            items = [t for t in items if t.priority.lower() == priority.lower()]
        if due_from:
            df = Task._normalize_date(due_from)
            items = [t for t in items if t.due_date and t.due_date >= df]
        if due_to:
            dt_ = Task._normalize_date(due_to)
            items = [t for t in items if t.due_date and t.due_date <= dt_]
        return items

    def toggle_done(self, index: int) -> None:
        if 0 <= index < len(self._tasks):
            self._tasks[index].is_done = not self._tasks[index].is_done
            if not self._tasks[index].due_date:
                self._tasks[index].due_date = date.today().isoformat()
