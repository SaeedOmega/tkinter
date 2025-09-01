import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from utils import fix_text
from utils import set_global_font
import os

from models import Task, ToDoList
from utils import (
    DATA_FILE,
    today_str,
    now_time_str,
    export_report_for_date,
    find_due_today,
    find_overdue,
)

# Optional plyer import
try:
    from plyer import notification
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class AddTaskWindow(ctk.CTkToplevel):
    def __init__(self, master, on_add):
        super().__init__(master)
        self.title("افزودن تسک جدید")
        self.geometry("420x260")
        self.on_add = on_add
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=fix_text("عنوان:")).grid(row=0, column=1, padx=10, pady=10, sticky="e")
        self.title_entry = ctk.CTkEntry(self, placeholder_text=fix_text("مثلاً: خرید شیر"))
        self.title_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=fix_text("اولویت:")).grid(row=1, column=1, padx=10, pady=10, sticky="e")
        self.priority_combo = ctk.CTkComboBox(self, values=["Low", "Medium", "High"])
        self.priority_combo.set("Medium")
        self.priority_combo.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=fix_text("تاریخ موعد (YYYY-MM-DD):")).grid(row=2, column=1, padx=10, pady=10, sticky="e")
        self.due_entry = ctk.CTkEntry(self, placeholder_text=today_str())
        self.due_entry.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        btn = ctk.CTkButton(self, text=fix_text("افزودن"), command=self._do_add)
        btn.grid(row=3, column=0, columnspan=2, padx=10, pady=18, sticky="ew")

        self.title_entry.focus_set()

    def _do_add(self):
        title = self.title_entry.get().strip()
        priority = self.priority_combo.get()
        due = self.due_entry.get().strip()
        if not title:
            messagebox.showwarning(fix_text("خطا"), fix_text("عنوان نباید خالی باشد."))
            return
        try:
            print(due)
            task = Task(title=fix_text(title), priority=priority, due_date=due)
        except Exception:
            messagebox.showerror(fix_text("تاریخ نامعتبر", "لطفاً تاریخ را به صورت YYYY-MM-DD وارد کنید."))
            return
        self.on_add(task)
        self.destroy()

class FilterWindow(ctk.CTkToplevel):
    def __init__(self, master, on_filter):
        super().__init__(master)
        self.title("جستجو/فیلتر")
        self.geometry("420x240")
        self.on_filter = on_filter
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=fix_text("اولویت:")).grid(row=0, column=1, padx=10, pady=10, sticky="e")
        self.priority_combo = ctk.CTkComboBox(self, values=["", "Low", "Medium", "High"])
        self.priority_combo.set("")
        self.priority_combo.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=fix_text("از تاریخ (YYYY-MM-DD):")).grid(row=1, column=1, padx=10, pady=10, sticky="e")
        self.from_entry = ctk.CTkEntry(self, placeholder_text=fix_text(""))
        self.from_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=(fix_text("تا تاریخ (YYYY-MM-DD):"))).grid(row=2, column=1, padx=10, pady=10, sticky="e")
        self.to_entry = ctk.CTkEntry(self, placeholder_text=fix_text(""))
        self.to_entry.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        btn = ctk.CTkButton(self, text=fix_text("اعمال فیلتر"), command=self._do_filter)
        btn.grid(row=3, column=0, columnspan=2, padx=10, pady=18, sticky="ew")

    def _do_filter(self):
        priority = self.priority_combo.get().strip() or None
        due_from = self.from_entry.get().strip() or None
        due_to = self.to_entry.get().strip() or None
        self.on_filter(priority, due_from, due_to)
        self.destroy()

class ReportWindow(ctk.CTkToplevel):
    def __init__(self, master, on_export):
        super().__init__(master)
        self.title("گزارش روزانه")
        self.geometry("420x200")
        self.on_export = on_export
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=fix_text("تاریخ (YYYY-MM-DD):")).grid(row=0, column=1, padx=10, pady=10, sticky="e")
        self.date_entry = ctk.CTkEntry(self, placeholder_text=today_str())
        self.date_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self, text=fix_text("نام فایل خروجی:")).grid(row=1, column=1, padx=10, pady=10, sticky="e")
        self.file_entry = ctk.CTkEntry(self, placeholder_text="report.txt")
        self.file_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        btn = ctk.CTkButton(self, text=fix_text("تولید گزارش"), command=self._do_export)
        btn.grid(row=2, column=0, columnspan=2, padx=10, pady=18, sticky="ew")

    def _do_export(self):
        date_str = self.date_entry.get().strip() or today_str()
        filename = self.file_entry.get().strip() or "report.txt"
        self.on_export(date_str, filename)
        self.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("To-Do List Pro")
        set_global_font()
        self.geometry("800x540")
        self.minsize(780, 520)

        # Data
        self.todo = ToDoList()
        # Auto-load
        if os.path.exists(DATA_FILE):
            self.todo.load_from_file(DATA_FILE)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        top.grid_columnconfigure(3, weight=1)

        self.clock_label = ctk.CTkLabel(top, text="--:--:--",width=75)
        self.clock_label.grid(row=0, column=0, padx=8, pady=8)

        self.today_btn = ctk.CTkButton(top, text=fix_text("کارهای امروز"), command=self.show_today)
        self.today_btn.grid(row=0, column=1, padx=8, pady=8)

        self.filter_btn = ctk.CTkButton(top, text=fix_text("جستجو/فیلتر"), command=self.open_filter)
        self.filter_btn.grid(row=0, column=2, padx=8, pady=8)

        self.status_label = ctk.CTkLabel(top, text=fix_text(""))
        self.status_label.grid(row=0, column=3, padx=8, pady=8, sticky="e")

        # Center: list
        center = ctk.CTkFrame(self)
        center.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkLabel(center, text=fix_text("لیست کارها"))
        hdr.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="e")

        self.listbox = ctk.CTkTextbox(center, wrap="none")
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        # Bottom buttons
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(6, 12))
        for i in range(6):
            bottom.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(bottom, text=fix_text("افزودن"), command=self.open_add).grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(bottom, text=fix_text("حذف"), command=self.remove_selected).grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(bottom, text=fix_text("ذخیره"), command=self.save_data).grid(row=0, column=2, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(bottom, text=fix_text("بارگذاری"), command=self.load_data).grid(row=0, column=3, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(bottom, text=fix_text("گزارش روز"), command=self.open_report).grid(row=0, column=4, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(bottom, text=fix_text("نمایش همه"), command=self.refresh_view).grid(row=0, column=5, padx=6, pady=8, sticky="ew")

        # Events
        self.listbox.bind("<Delete>", lambda e: self.remove_selected())
        self.listbox.bind("<Double-1>", lambda e: self.toggle_selected())

        # Initial render + clock + notifications
        self.refresh_view()
        self.tick_clock()
        self.notify_due_tasks()

    # --- UI helpers ---
    def format_task(self, idx, t: Task) -> str:
        done = "✓" if t.is_done else "✗"
        return fix_text(f"{idx+1:>2}. [{done}] ({t.priority[:1]}) {t.title} | ایجاد: {t.created_date} | موعد: {t.due_date or '-'}")

    def refresh_view(self, items=None):
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        if items is None:
            items = self.todo.list_tasks()
        for i, t in enumerate(items):
            self.listbox.insert("end", self.format_task(i, t) + "\n")
        self.listbox.configure(state="disabled")
        self.status_label.configure(text=fix_text(f"تعداد تسک‌ها: {len(self.todo.list_tasks())}"))

    def selected_index(self) -> Optional[int]:
        # map cursor line to task index
        try:
            index = int(float(self.listbox.index("insert")).__floor__()) - 1
            if 0 <= index < len(self.todo.list_tasks()):
                return index
        except Exception:
            pass
        return None

    # --- Actions ---
    def open_add(self):
        AddTaskWindow(self, on_add=self.add_task)

    def add_task(self, task: Task):
        self.todo.add_task(task)
        self.refresh_view()

    def remove_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo("حذف", fix_text("ابتدا یک تسک را انتخاب کنید (روی خطش کلیک کنید)."))
            return
        title = self.todo.list_tasks()[idx].title
        if self.todo.remove_task(title):
            self.refresh_view()

    def toggle_selected(self):
        idx = self.selected_index()
        if idx is None:
            return
        self.todo.toggle_done(idx)
        self.refresh_view()

    def save_data(self):
        self.todo.save_to_file(DATA_FILE)
        messagebox.showinfo("ذخیره شد", fix_text(f"تسک‌ها در فایل {DATA_FILE} ذخیره شدند."))

    def load_data(self):
        self.todo.load_from_file(DATA_FILE)
        self.refresh_view()
        messagebox.showinfo("بارگذاری شد", fix_text(f"تسک‌ها از فایل {DATA_FILE} بارگذاری شدند."))

    def show_today(self):
        items = self.todo.list_by_date(today_str())
        self.refresh_view(items)

    def open_filter(self):
        FilterWindow(self, on_filter=self.apply_filter)

    def apply_filter(self, priority, due_from, due_to):
        items = self.todo.filter(priority=priority, due_from=due_from, due_to=due_to)
        self.refresh_view(items)

    def open_report(self):
        ReportWindow(self, on_export=self.export_report)

    def export_report(self, date_str, filename):
        export_report_for_date(filename, self.todo.list_tasks(), date_str)
        messagebox.showinfo("گزارش آماده شد", fix_text(f"گزارش در فایل {filename} ذخیره شد."))

    # --- Clock & notifications ---
    def tick_clock(self):
        self.clock_label.configure(text=fix_text(now_time_str()))
        self.after(1000, self.tick_clock)

    def notify_due_tasks(self):
        due_today = find_due_today(self.todo.list_tasks())
        overdue = find_overdue(self.todo.list_tasks())
        msgs = []
        if due_today:
            msgs.append(fix_text(f"{len(due_today)} تسک با موعد امروز"))
        if overdue:
            msgs.append(fix_text(f"{len(overdue)} تسک عقب‌افتاده"))
        if msgs:
            text = fix_text(" و ".join(msgs))
            try:
                messagebox.showwarning(fix_text("یادآوری"), text)
            except Exception:
                pass
            if HAS_PLYER:
                try:
                    notification.notify(title="To-Do List Pro", message=text, timeout=5)
                except Exception:
                    pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
