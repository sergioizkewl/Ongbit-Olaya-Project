from asyncio import all_tasks
import tkinter as tk
from tkinter import ttk, messagebox
import calendar
import sqlite3 
import os
from datetime import datetime, timedelta
from turtle import title

#Custom Modules
from modules.database import init_db, get_user_profile, save_user_profile, get_tasks, save_task, update_task_status, delete_task, get_notes, save_note, delete_note

DB_FOLDER = r"C:\Users\Acer\CS - Project\data"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

Trackit_DB = os.path.join(DB_FOLDER, "Trackit.db")

#--------------------------- DATE PICKER ------------------
class DatePicker(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.callback = callback
        self.now = datetime.now()
        self.view_year = self.now.year
        self.view_month = self.now.month
        self.selected_date = None
        self.build_ui()

    def build_ui(self):
        for widget in self.winfo_children(): 
            widget.destroy()

        nav = tk.Frame(self, bg="white")
        nav.pack(fill="x", pady=5)
        
        tk.Button(nav, text="<", command=lambda: self.change_month(-1), relief="flat").pack(side="left", padx=5)
        tk.Label(nav, text=f"{calendar.month_name[self.view_month]} {self.view_year}", 
                 bg="white", font=("Arial", 10, "bold")).pack(side="left", expand=True)
        tk.Button(nav, text=">", command=lambda: self.change_month(1), relief="flat").pack(side="right", padx=5)

        grid = tk.Frame(self, bg="white")
        grid.pack(padx=5, pady=5)
        
        days = ["Mo","Tu","We","Th","Fr","Sa","Su"]
        for i, d in enumerate(days):
            tk.Label(grid, text=d, bg="white", font=("Arial", 8, "bold"), width=3).grid(row=0, column=i)

        cal = calendar.monthcalendar(self.view_year, self.view_month)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(grid, text=str(day), width=3, relief="flat", bg="#f8f9fa",
                                    command=lambda d=day: self.set_date(d))
                    btn.grid(row=r+1, column=c, padx=1, pady=1)

    def change_month(self, delta):
        self.view_month += delta
        if self.view_month > 12: 
            self.view_month = 1; self.view_year += 1
        elif self.view_month < 1: 
            self.view_month = 12; self.view_year -= 1
        self.build_ui()

    def set_date(self, day):
        date_str = f"{self.view_year}-{self.view_month:02d}-{day:02d}"
        self.callback(date_str) 

#--------------------------- TRACKIT APP ------------------
class TrackItApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TrackIt - Dashboard")
        self.root.geometry("1000x850")
        self.root.configure(bg="#f0f2f5")

        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        
        init_db()
        
        any_user = get_user_profile() 
        
        if not any_user:
            self.show_signup_screen()
        else:
            self.user_profile = None  
            self.show_login_screen()

#--------------------------- GUI PROCESSES ------------------
    def clear_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()

    def show_signup_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg="white", padx=40, pady=40, highlightthickness=1, highlightbackground="#ddd")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="Create Profile", font=("Arial", 18, "bold"), bg="white").pack(pady=(0, 20))
        fields = ["Name", "Password"]
        self.entries = {}
        for field in fields:
            tk.Label(frame, text=field, bg="white").pack(anchor="w")
            ent = tk.Entry(frame, font=("Arial", 12), width=30, show="*" if field == "Password" else None); ent.pack(pady=(0,10))
            self.entries[field] = ent
        tk.Button(frame, text="Sign Up", bg="black", fg="white", font=("Arial", 10, "bold"), 
                  command=self.process_signup, width=34, pady=10).pack(pady=20)
        tk.Button(frame, text="Log In", bg="black", fg="white", font=("Arial", 10, "bold"), 
                  command=self.show_login_screen, width=34, pady=10).pack(pady=5)

    def process_signup(self):
        profile = {f: self.entries[f].get() for f in self.entries}
        if all(profile.values()):
            save_user_profile(profile)
            self.user_profile = get_user_profile()
            self.build_main_interface()
        else:
            messagebox.showwarning("Error", "Fill all fields.")

    def show_login_screen(self):
        self.clear_screen()
        login_frame = tk.Frame(self.root, bg="white", padx=40, pady=40, highlightthickness=1, highlightbackground="#ddd")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(login_frame, text="Log in to Profile", font=("Arial", 18, "bold"), bg="white").pack(pady=(0, 20))
        fields = ["Name", "Password"]
        self.entries = {}
        for field in fields:
            tk.Label(login_frame, text=field, bg="white").pack(anchor="w")
            ent = tk.Entry(login_frame, font=("Arial", 12), width=30, show="*" if field == "Password" else None); ent.pack(pady=(0,10))
            self.entries[field] = ent
        tk.Button(login_frame, text="Log In", bg="black", fg="white", font=("Arial", 10, "bold"), 
                  command=self.process_login, width=34, pady=10).pack(pady=20)
        tk.Button(login_frame, text="Sign Up", bg="black", fg="white", font=("Arial", 10, "bold"), 
                  command=self.show_signup_screen, width=34, pady=10).pack(pady=5)

    def process_login(self):
        name_input = self.entries["Name"].get()
        pass_input = self.entries["Password"].get()
    
        user_data = get_user_profile(name=name_input)
    
        if user_data and user_data['password'] == pass_input:
            self.user_profile = user_data 
            self.build_main_interface()
        else:
            messagebox.showerror("Error", "Invalid Name/Password.")

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_calendar_tasks(self, date_str):
        for w in self.cal_list_frame.winfo_children(): w.destroy()
        day_tasks = [t for t in get_tasks() if t['due'] == date_str]
        tk.Label(self.cal_list_frame, text=f"Tasks for {date_str}", font=("Arial", 12, "bold"), bg="white").pack()
        for t in day_tasks: tk.Label(self.cal_list_frame, text=f"• {t['name']} ({t['status']})", bg="white").pack()

    def change_month(self, delta):
        self.current_month += delta
        if self.current_month > 12: self.current_month = 1; self.current_year += 1
        elif self.current_month < 1: self.current_month = 12; self.current_year -= 1
        self.show_calendar()
    
    def build_main_interface(self):
        self.clear_screen()
        self.sidebar = tk.Frame(self.root, bg="#ffffff", width=220); self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        self.main_area = tk.Frame(self.root, bg="#f0f2f5"); self.main_area.pack(side="right", expand=True, fill="both")
        tk.Label(self.sidebar, text="TrackIt", font=("Arial", 20, "bold"), bg="white", pady=30).pack()
        nav = [("Dashboard", self.show_dashboard), ("Tasks", self.show_tasks), ("Calendar", self.show_calendar), ("Notes", self.show_notes), ("Profile", self.show_profile)]
        for text, cmd in nav:
            tk.Button(self.sidebar, text=f"  {text}", font=("Arial", 11), bg="white", relief="flat", anchor="w", command=cmd, padx=20, pady=12).pack(fill="x")
        self.show_dashboard()

    # ---------------- DASHBOARD ----------------
    def show_dashboard(self):
        self.clear_main()
        self.create_header(f"Hey, {self.user_profile['name']}!")
        cont = tk.Frame(self.main_area, bg="#f0f2f5", padx=30); cont.pack(fill="both", expand=True)
        today_str = datetime.now().strftime("%Y-%m-%d")

        all_tasks = get_tasks(self.user_profile['id'])
        tasks_today = [t for t in all_tasks if t['due'] == today_str and t['status'] != 'Completed']
        late_tasks = [t for t in all_tasks if t['status'] == 'Late']

        #Dashboard Cards
        c1 = tk.Frame(cont, bg="white", padx=25, pady=25, highlightthickness=1, highlightbackground="#eee")
        c1.place(relx=0, rely=0, relwidth=0.45, relheight=0.45)
        tk.Label(c1, text="Today's Overview", font=("Arial", 12, "bold"), bg="white", fg="#555").pack(anchor="w")
        tk.Label(c1, text=str(len(tasks_today)), font=("Arial", 45, "bold"), bg="white", fg="black").pack(anchor="w", pady=(10,0))
        tk.Label(c1, text="Tasks for Today", font=("Arial", 10), bg="white", fg="gray").pack(anchor="w")
        if late_tasks: tk.Label(c1, text=f"⚠ {len(late_tasks)} Late Tasks", font=("Arial", 10, "bold"), bg="white", fg="red").pack(anchor="w", pady=(10,0))

        scroll_container = tk.Frame(c1, bg="white")
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))

        canvas.pack(side="left", fill="both", expand=True)
        if len(tasks_today) > 3:
            scrollbar.pack(side="right", fill="y")

        if tasks_today:
            for t in tasks_today: 
                tk.Label(scrollable_frame, text=f"• {t['name']}", font=("Arial", 10), bg="white", fg="#333").pack(anchor="w", pady=2)
        else: 
            tk.Label(scrollable_frame, text="Nothing due today!", font=("Arial", 10, "italic"), bg="white", fg="#4CAF50").pack(anchor="w")

        c2 = tk.Frame(cont, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#eee")
        c2.place(relx=0.5, rely=0, relwidth=0.45, relheight=0.45)
        tk.Label(c2, text="Weekly Progress", font=("Arial", 12, "bold"), bg="white", fg="#555").pack(anchor="w")

        c3 = tk.Frame(cont, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#eee")
        c3.place(relx=0, rely=0.5, relwidth=0.45, relheight=0.45)
        tk.Label(c3, text="Calendar", font=("Arial", 12, "bold"), bg="white", fg="#555").pack(anchor="w")

    # ----------------   GUI   -------------------
    def clear_main(self):
        for widget in self.main_area.winfo_children(): widget.destroy()

    def create_header(self, title):
        h = tk.Frame(self.main_area, bg="#f0f2f5", pady=20, padx=30); h.pack(fill="x")
        tk.Label(h, text=title, font=("Arial", 18, "bold"), bg="#f0f2f5").pack(side="left")
        tk.Button(h, text="+ Add Task", bg="black", fg="white", font=("Arial", 9, "bold"), command=self.show_add_task, padx=15, pady=8).pack(side="right")

    def show_add_task(self):
        self.clear_main()
        self.create_header("Add New Task")

        container = tk.Frame(self.main_area, bg="white", padx=30, pady=30, highlightthickness=1, highlightbackground="#eee")
        container.pack(pady=20)

        tk.Label(container, text="What needs to be done?", font=("Arial", 10), bg="white").pack(anchor="w")
        name_ent = tk.Entry(container, font=("Arial", 12), width=30, relief="solid", bd=1)
        name_ent.pack(pady=(5, 15))

        self.date_display = tk.Label(container, text="No date selected", font=("Arial", 10, "italic"), fg="gray", bg="white")
        self.date_display.pack(anchor="w")

        self.calendar_ui = DatePicker(container, self.update_date_label)
        self.calendar_ui.pack(pady=10)

        btn_frame = tk.Frame(container, bg="white")
        btn_frame.pack(fill="x", pady=20)

        tk.Button(btn_frame, text="Cancel", command=self.show_tasks, relief="flat", bg="#ccc").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Save Task", bg="black", fg="white", command=lambda: (save_task({"task_name": name_ent.get(), "due_date": self.selected_task_date, "user_id": self.user_profile['id']}), self.show_tasks())).pack(side="right")
    
    def update_date_label(self, date_str):
        self.selected_task_date = date_str
        if date_str == datetime.now().strftime("%Y-%m-%d"):
            self.date_display.config(text="Scheduled for: Today", fg="#4CAF50", font=("Arial", 10, "bold"))
        elif date_str < datetime.now().strftime("%Y-%m-%d"):
            self.date_display.config(text=f"Scheduled for: {date_str}", fg="red", font=("Arial", 10, "bold"))
        else:
            self.date_display.config(text=f"Scheduled for: {date_str}", fg="green", font=("Arial", 10, "bold"))

    def show_tasks(self):
        self.clear_main()
        self.create_header("Tasks")
        container = tk.Frame(self.main_area, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#ddd"); container.pack(padx=30, fill="both", expand=True)
        for t in get_tasks(self.user_profile['id']):
            row = tk.Frame(container, bg="white", pady=8)
            row.pack(fill="x")
            tk.Label(row, text=t['name'], fg="red" if t['status']=='Late' else "black", bg="white", width=25, anchor="w").pack(side="left")
            tk.Label(row, text=t['due'], bg="white", width=15, fg="#555").pack(side="left")
            var = tk.StringVar(value=t['status'])
            cb = ttk.Combobox(row, textvariable=var, values=("Pending", "Completed", "Late"), state="readonly", width=10)
            cb.pack(side="left", padx=10); cb.bind("<<ComboboxSelected>>", lambda e, task_id=t['id'], v=var: update_task_status(task_id, v.get()))
            tk.Button(row, text="✕", fg="red", bg="white", relief="flat", command=lambda task_id=t['id']: [delete_task(task_id), self.show_tasks()]).pack(side="right")

    def show_calendar(self):
        self.clear_main()
        self.create_header("Schedule")
        container = tk.Frame(self.main_area, bg="#f0f2f5"); container.pack(pady=5)
        tk.Button(container, text="<", command=lambda: self.change_month(-1)).pack(side="left", padx=5)
        tk.Label(container, text=f"{calendar.month_name[self.current_month]} {self.current_year}", font=("Arial", 14, "bold"), width=18).pack(side="left")
        tk.Button(container, text=">", command=lambda: self.change_month(1)).pack(side="left", padx=5)
        grid_frame = tk.Frame(self.main_area, bg="white", padx=10, pady=10, highlightthickness=1, highlightbackground="#ddd"); grid_frame.pack(padx=30)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days): tk.Label(grid_frame, text=d, font=("Arial", 9, "bold"), bg="white", width=10).grid(row=0, column=i)
        month_days = calendar.monthcalendar(self.current_year, self.current_month)
        today_str = datetime.now().strftime("%Y-%m-%d")
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    dt_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    active_tasks = [t for t in get_tasks(self.user_profile['id']) if t['due'] == dt_str and t['status'] != 'Completed']
                    bg = "#e8f5e9" if dt_str == today_str else ("#ffebee" if active_tasks and any(t['status'] == 'Late' for t in active_tasks) else ("#fffde7" if active_tasks else "#f8f9fa"))
                    btn_text = f"{day}" + (f"\n({len(active_tasks)})" if active_tasks else "")
                    tk.Button(grid_frame, text=btn_text, width=8, height=3, bg=bg, relief="flat", command=lambda s=dt_str: self.refresh_calendar_tasks(s)).grid(row=r+1, column=c, padx=2, pady=2)
        self.cal_list_frame = tk.Frame(self.main_area, bg="white"); self.cal_list_frame.pack(fill="both", expand=True, padx=30, pady=20)

    def show_notes(self):
        self.clear_main()
        self.create_header("Notes")
        
        cont = tk.Frame(self.main_area, bg="#f0f2f5", padx=30)
        cont.pack(fill="both", expand=True)

        l_list = tk.Frame(cont, bg="white", width=250)
        l_list.pack(side="left", fill="y", pady=(0, 20))
        l_list.pack_propagate(False)

        self.r_content = tk.Frame(cont, bg="white", padx=20, pady=20)
        self.r_content.pack(side="right", fill="both", expand=True, padx=(20, 0), pady=(0, 20))

        def display_content(note):
            for widget in self.r_content.winfo_children(): widget.destroy()
            
            tk.Label(self.r_content, text=note['title'], font=("Arial", 16, "bold"), bg="white", anchor="w").pack(fill="x")
            
            content_box = tk.Text(self.r_content, font=("Arial", 11), bg="white", relief="flat", wrap="word")
            content_box.insert("1.0", note['content'])
            content_box.config(state="disabled")
            content_box.pack(fill="both", expand=True, pady=10)

            btn_frame = tk.Frame(self.r_content, bg="white")
            btn_frame.pack(fill="x")
            tk.Button(btn_frame, text="Edit Note", bg="black", fg="white", command=lambda: self.show_note_editor(note), padx=20).pack(side="right")

        tk.Button(l_list, text="+ New Note", bg="white", relief="flat", command=lambda: self.show_note_editor()).pack(fill="x", pady=5)
        
        notes = get_notes()
        for n in notes:
            item = tk.Frame(l_list, bg="white")
            item.pack(fill="x", pady=1)
            tk.Button(item, text=f" {n['title']}", bg="white", relief="flat", anchor="w", command=lambda note=n: display_content(note)).pack(side="left", fill="x", expand=True)
            tk.Button(item, text="✕", fg="red", bg="white", relief="flat", command=lambda nid=n['id']: [delete_note(nid), self.show_notes()]).pack(side="right", padx=5)
        tk.Label(self.r_content, text="Select a note to view", font=("Arial", 12, "italic"), bg="white", fg="gray").pack(expand=True)

    def show_note_editor(self, note=None):
        for widget in self.r_content.winfo_children(): 
            widget.destroy()

        tk.Label(self.r_content, text="Title", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        t_ent = tk.Entry(self.r_content, font=("Arial", 12), relief="solid", bd=1)
        t_ent.pack(fill="x", pady=(5, 15))

        tk.Label(self.r_content, text="Content", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
  
        btn_frame = tk.Frame(self.r_content, bg="white")
        btn_frame.pack(side="bottom", fill="x", pady=10)

        def save():
            title = t_ent.get()
            content = txt.get("1.0", tk.END).strip()
            if not title: return messagebox.showwarning("Warning", "Title required.")
            note_data = {'title': title, 'content': content}
            if note: note_data['id'] = note['id']
            save_note(note_data)
            self.show_notes()

        tk.Button(btn_frame, text="Cancel", command=self.show_notes, bg="#ccc", padx=15).pack(side="left")
        tk.Button(btn_frame, text="Save Note", bg="black", fg="white", font=("Arial", 10, "bold"), command=save, padx=25).pack(side="right")

        txt = tk.Text(self.r_content, font=("Arial", 11), relief="solid", bd=1, wrap="word")
        txt.pack(fill="both", expand=True, pady=5)

        if note:
            t_ent.insert(0, note['title'])
            txt.insert("1.0", note['content'])

    def show_profile(self):
        self.clear_main()
        self.create_header("Profile")

        
if __name__ == "__main__":
    root = tk.Tk(); app = TrackItApp(root); root.mainloop()




