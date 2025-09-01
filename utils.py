
from __future__ import annotations
from typing import List
from datetime import datetime, date
import json, os
import arabic_reshaper
from bidi.algorithm import get_display

from models import Task

DATA_FILE = "data.txt"

def today_str() -> str:
    return date.today().isoformat()

def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")

def save_tasks_jsonl(filename: str, tasks: List[Task]) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n")

def load_tasks_jsonl(filename: str) -> List[Task]:
    items: List[Task] = []
    if not os.path.exists(filename):
        return items
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            items.append(Task(**obj))
    return items

def export_report_for_date(filename: str, tasks: List[Task], target_date: str) -> None:
    """Export in the exact format requested by the brief."""
    target_date = Task._normalize_date(target_date)
    lines = [f"{target_date}: YYYY-MM-DD", "-"*21]
    for t in tasks:
        if t.due_date == target_date:
            status = "انجام شده" if t.is_done else "انجام نشده"
            lines.append(f"عنوان: {t.title} - | وضعیت: {status} :| اولویت: {t.priority} :")
    content = "\n".join(lines) + "\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def find_due_today(tasks: List[Task]) -> List[Task]:
    today = today_str()
    return [t for t in tasks if t.due_date == today and not t.is_done]

def find_overdue(tasks: List[Task]) -> List[Task]:
    today = today_str()
    return [t for t in tasks if t.due_date and t.due_date < today and not t.is_done]


def fix_text(text: str) -> str:
    """متن رو reshape و bidi میکنه تا برای فارسی درست نمایش داده بشه"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def set_global_font(family="Mikhak-FD", size=16):
    from customtkinter import CTkLabel, CTkButton, CTkEntry, CTkCheckBox, CTkOptionMenu, CTkComboBox, CTkSwitch, CTkFont

    app_font = CTkFont(family=family, size=size)

    def patch(cls):
        original_init = cls.__init__
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("font", app_font)
            original_init(self, *args, **kwargs)
        cls.__init__ = __init__

    widgets = [CTkLabel, CTkButton, CTkEntry, CTkCheckBox, CTkOptionMenu, CTkComboBox, CTkSwitch]
    for w in widgets:
        patch(w)

    return app_font