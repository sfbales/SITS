import os
import json
import threading
import time
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
import tkinter as tk
from tkinter import filedialog
from tkcalendar import DateEntry  # Install via 'pip install tkcalendar'
import subprocess

class ScheduleManager:
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    SCHEDULE_FILE = os.path.join(CONFIG_DIR, "scheduled_tasks.json") # File to persist scheduled tasks
    
    def __init__(self, parent_notebook):
        self.parent_notebook = parent_notebook
        self.tab = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.tab, text="Schedule Manager")
        self.scheduled_tasks = []
        self.lock = threading.Lock()
        self.load_scheduled_tasks()
        self.create_widgets()
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def create_widgets(self):
        """Set up UI components for the Schedule Manager tab."""
        # Main frame setup
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title label
        ttk.Label(main_frame, text="Task Scheduler", font=("Arial", 14, "bold")).pack(pady=10)

        # Frame for adding new tasks
        frame = ttk.Frame(main_frame)
        frame.pack(fill='x', expand=True, pady=5)

        # Task Name
        ttk.Label(frame, text="Task Name:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.task_name_entry = ttk.Entry(frame)
        self.task_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Command/Script
        ttk.Label(frame, text="Command/Script:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.command_entry = ttk.Entry(frame, width=50)
        self.command_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.command_browse_button = ttk.Button(frame, text="Browse", command=self.browse_command)
        self.command_browse_button.grid(row=1, column=2, padx=5, pady=5, sticky='w')

        # Working Directory
        ttk.Label(frame, text="Working Directory:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.working_dir_entry = ttk.Entry(frame, width=50)
        self.working_dir_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.working_dir_browse_button = ttk.Button(frame, text="Browse", command=self.browse_working_directory)
        self.working_dir_browse_button.grid(row=2, column=2, padx=5, pady=5, sticky='w')

        # Schedule Type
        ttk.Label(frame, text="Schedule Type:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.schedule_type = ttk.Combobox(frame, values=["One-time", "Recurring", "Interval"], state="readonly")
        self.schedule_type.current(0)  # Default to "One-time"
        self.schedule_type.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.schedule_type.bind("<<ComboboxSelected>>", self.update_schedule_type)

        # Schedule Details Frame
        self.schedule_details_frame = ttk.Frame(frame)
        self.schedule_details_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky='w')

        # Initialize schedule type frames
        self.init_one_time_frame()
        self.init_recurring_frame()
        self.init_interval_frame()

        # Show default schedule type frame
        self.one_time_frame.pack(fill='x', expand=True)

        # Close After Option
        ttk.Label(frame, text="Close After:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.close_after_entry = ttk.Entry(frame, width=10)
        self.close_after_entry.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(frame, text="executions (leave blank for unlimited)").grid(row=5, column=2, padx=5, pady=5, sticky='w')

        # Save Output Option
        self.save_output_var = tk.BooleanVar()
        self.save_output_check = ttk.Checkbutton(frame, text="Save Output", variable=self.save_output_var, command=self.toggle_save_output)
        self.save_output_check.grid(row=6, column=1, padx=5, pady=5, sticky='w')

        # Output Saving Method
        self.output_method_frame = ttk.Frame(frame)

        self.output_method_var = tk.StringVar(value="single_file")
        self.output_method_single = ttk.Radiobutton(
            self.output_method_frame, text="Save all outputs in a single file with timestamps",
            variable=self.output_method_var, value="single_file", command=self.update_output_method
        )
        self.output_method_separate = ttk.Radiobutton(
            self.output_method_frame, text="Save each output to a separate file",
            variable=self.output_method_var, value="separate_files", command=self.update_output_method
        )

        # Output File/Directory Selection
        self.output_path_label = ttk.Label(frame, text="Output File:")
        self.output_path_entry = ttk.Entry(frame, width=50)
        self.output_path_browse_button = ttk.Button(frame, text="Browse", command=self.browse_output_path)

        # Add Task Button
        self.add_task_button = ttk.Button(frame, text="Add Task", command=self.add_task)
        self.add_task_button.grid(row=9, column=2, pady=10, sticky='e')

        # Task List
        columns = ("Task", "Type", "Next Run", "Command", "Working Directory", "Schedule Details", "Close After", "Save Output")
        self.task_list = ttk.Treeview(main_frame, columns=columns, show='headings')
        for col in columns:
            self.task_list.heading(col, text=col)
            self.task_list.column(col, minwidth=100, stretch=True)
        self.task_list.pack(fill='both', expand=True, pady=10)

        # Add scrollbar to the task list
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.task_list.yview)
        self.task_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Populate task list
        self.populate_task_list()

        # Delete Task Button
        self.delete_task_button = ttk.Button(main_frame, text="Delete Selected Task", command=self.delete_task)
        self.delete_task_button.pack(pady=5)

    def init_one_time_frame(self):
        """Initialize the one-time schedule frame."""
        self.one_time_frame = ttk.Frame(self.schedule_details_frame)

        # Date selection
        ttk.Label(self.one_time_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.one_time_date = DateEntry(self.one_time_frame)
        self.one_time_date.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Time selection
        ttk.Label(self.one_time_frame, text="Time:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.one_time_hour = ttk.Combobox(
            self.one_time_frame, values=[f"{i:02d}" for i in range(24)], width=5, state="readonly"
        )
        self.one_time_hour.current(0)
        self.one_time_hour.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.one_time_minute = ttk.Combobox(
            self.one_time_frame, values=[f"{i:02d}" for i in range(60)], width=5, state="readonly"
        )
        self.one_time_minute.current(0)
        self.one_time_minute.grid(row=1, column=2, padx=5, pady=5, sticky='w')

    def init_recurring_frame(self):
        """Initialize the recurring schedule frame."""
        self.recurring_frame = ttk.Frame(self.schedule_details_frame)

        # Frequency selection
        ttk.Label(self.recurring_frame, text="Frequency:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.recurring_frequency = ttk.Combobox(
            self.recurring_frame, values=["Daily", "Weekly", "Monthly"], state="readonly"
        )
        self.recurring_frequency.current(0)
        self.recurring_frequency.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.recurring_frequency.bind("<<ComboboxSelected>>", self.update_recurring_frequency)

        # Time selection
        ttk.Label(self.recurring_frame, text="Time:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.recurring_hour = ttk.Combobox(
            self.recurring_frame, values=[f"{i:02d}" for i in range(24)], width=5, state="readonly"
        )
        self.recurring_hour.current(0)
        self.recurring_hour.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.recurring_minute = ttk.Combobox(
            self.recurring_frame, values=[f"{i:02d}" for i in range(60)], width=5, state="readonly"
        )
        self.recurring_minute.current(0)
        self.recurring_minute.grid(row=1, column=2, padx=5, pady=5, sticky='w')

        # Weekly days selection
        self.weekly_days_frame = ttk.Frame(self.recurring_frame)
        self.weekly_days_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.weekly_days_vars = []
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days_of_week):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.weekly_days_frame, text=day, variable=var)
            chk.grid(row=i//4, column=i%4, sticky='w')
            self.weekly_days_vars.append((day, var))

        # Hide weekly days frame initially
        self.weekly_days_frame.grid_remove()

    def init_interval_frame(self):
        """Initialize the interval schedule frame."""
        self.interval_frame = ttk.Frame(self.schedule_details_frame)

        ttk.Label(self.interval_frame, text="Interval:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.interval_value = ttk.Entry(self.interval_frame, width=10)
        self.interval_value.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.interval_unit = ttk.Combobox(
            self.interval_frame, values=["Seconds", "Minutes", "Hours"], state="readonly"
        )
        self.interval_unit.current(0)
        self.interval_unit.grid(row=0, column=2, padx=5, pady=5, sticky='w')

    def toggle_save_output(self):
        """Toggle the visibility of the output file selection based on the save output checkbox."""
        if self.save_output_var.get():
            self.output_method_frame.grid(row=7, column=1, padx=5, pady=5, sticky='w')
            self.output_method_single.grid(row=0, column=0, sticky='w')
            self.output_method_separate.grid(row=1, column=0, sticky='w')

            self.output_path_label.grid(row=8, column=0, padx=5, pady=5, sticky='e')
            self.output_path_entry.grid(row=8, column=1, padx=5, pady=5, sticky='w')
            self.output_path_browse_button.grid(row=8, column=2, padx=5, pady=5, sticky='w')
        else:
            self.output_method_frame.grid_remove()
            self.output_path_label.grid_remove()
            self.output_path_entry.grid_remove()
            self.output_path_browse_button.grid_remove()

    def update_output_method(self):
        """Update UI elements based on the selected output method."""
        method = self.output_method_var.get()
        if method == "single_file":
            self.output_path_label.config(text="Output File:")
        elif method == "separate_files":
            self.output_path_label.config(text="Output Directory:")

    def browse_command(self):
        """Open a file dialog to select a command or script."""
        file_path = filedialog.askopenfilename(title="Select Command or Script")
        if file_path:
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, file_path)

    def browse_working_directory(self):
        """Open a directory dialog to select a working directory."""
        directory = filedialog.askdirectory(title="Select Working Directory")
        if directory:
            self.working_dir_entry.delete(0, tk.END)
            self.working_dir_entry.insert(0, directory)

    def browse_output_path(self):
        """Open a file or directory dialog based on the output method."""
        method = self.output_method_var.get()
        if method == "single_file":
            file_path = filedialog.asksaveasfilename(title="Select Output File")
            if file_path:
                self.output_path_entry.delete(0, tk.END)
                self.output_path_entry.insert(0, file_path)
        elif method == "separate_files":
            directory = filedialog.askdirectory(title="Select Output Directory")
            if directory:
                self.output_path_entry.delete(0, tk.END)
                self.output_path_entry.insert(0, directory)

    def update_schedule_type(self, event=None):
        """Show/hide schedule detail frames based on schedule type."""
        schedule_type = self.schedule_type.get()
        # Clear all frames
        for frame in (self.one_time_frame, self.recurring_frame, self.interval_frame):
            frame.pack_forget()
        # Show the selected frame
        if schedule_type == "One-time":
            self.one_time_frame.pack(fill='x', expand=True)
        elif schedule_type == "Recurring":
            self.recurring_frame.pack(fill='x', expand=True)
            self.update_recurring_frequency()
        elif schedule_type == "Interval":
            self.interval_frame.pack(fill='x', expand=True)

    def update_recurring_frequency(self, event=None):
        """Show/hide weekly days selection based on frequency."""
        frequency = self.recurring_frequency.get()
        if frequency == "Weekly":
            self.weekly_days_frame.grid()
        else:
            self.weekly_days_frame.grid_remove()

    def load_scheduled_tasks(self):
        """Load scheduled tasks from JSON."""
        if os.path.exists(self.SCHEDULE_FILE):
            try:
                with open(self.SCHEDULE_FILE, "r") as file:
                    self.scheduled_tasks = json.load(file)
                # Convert next_run from string to datetime object
                for task in self.scheduled_tasks:
                    task["next_run"] = datetime.fromisoformat(task["next_run"])
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to load scheduled tasks.")
                self.scheduled_tasks = []

    def save_scheduled_tasks(self):
        """Save the current list of scheduled tasks to JSON."""
        try:
            with open(self.SCHEDULE_FILE, "w") as file:
                # Convert next_run to string for JSON serialization
                tasks_to_save = [
                    {**task, "next_run": task["next_run"].isoformat()} for task in self.scheduled_tasks
                ]
                json.dump(tasks_to_save, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scheduled tasks:\n{str(e)}")

    def add_task(self):
        """Add a new task to the scheduler."""
        task_name = self.task_name_entry.get().strip()
        command = self.command_entry.get().strip()
        working_dir = self.working_dir_entry.get().strip()
        schedule_type = self.schedule_type.get()

        # Input validation
        if not task_name or not command:
            messagebox.showwarning("Input Error", "Please enter a task name and command/script.")
            return

        # Close After
        close_after = self.close_after_entry.get().strip()
        if close_after:
            if not close_after.isdigit() or int(close_after) <= 0:
                messagebox.showwarning("Input Error", "Close After must be a positive integer.")
                return
            close_after = int(close_after)
        else:
            close_after = None  # Unlimited executions

        # Save Output
        save_output_enabled = self.save_output_var.get()
        save_output = {"enabled": save_output_enabled, "method": None, "path": None}
        if save_output_enabled:
            output_method = self.output_method_var.get()
            output_path = self.output_path_entry.get().strip()
            if not output_path:
                messagebox.showwarning("Input Error", "Please specify an output file or directory.")
                return
            save_output["method"] = output_method
            save_output["path"] = output_path

        # Prepare task dictionary
        task = {
            "task_name": task_name,
            "command": command,
            "working_directory": working_dir or None,
            "schedule_type": schedule_type,
            "next_run": None,  # Will be set later
            "schedule_details": "",
            "close_after": close_after,
            "run_count": 0,
            "save_output": save_output,
        }

        # Schedule details based on schedule type
        if schedule_type == "One-time":
            date = self.one_time_date.get_date()
            hour = int(self.one_time_hour.get())
            minute = int(self.one_time_minute.get())
            run_at = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
            if run_at <= datetime.now():
                messagebox.showwarning("Input Error", "The scheduled time must be in the future.")
                return
            task["next_run"] = run_at
            task["schedule_details"] = f"At {run_at.strftime('%Y-%m-%d %H:%M:%S')}"
        elif schedule_type == "Recurring":
            frequency = self.recurring_frequency.get()
            hour = int(self.recurring_hour.get())
            minute = int(self.recurring_minute.get())
            time_of_day = timedelta(hours=hour, minutes=minute)
            task["frequency"] = frequency
            task["time_of_day"] = str(time_of_day)

            if frequency == "Weekly":
                days_selected = [
                    day for day, var in self.weekly_days_vars if var.get()
                ]
                if not days_selected:
                    messagebox.showwarning("Input Error", "Please select at least one day of the week.")
                    return
                task["days_of_week"] = days_selected
                task["schedule_details"] = f"Every {', '.join(days_selected)} at {hour:02d}:{minute:02d}"
            else:
                task["days_of_week"] = None
                if frequency == "Daily":
                    task["schedule_details"] = f"Daily at {hour:02d}:{minute:02d}"
                elif frequency == "Monthly":
                    task["schedule_details"] = f"Monthly at {hour:02d}:{minute:02d}"

            # Calculate next run time
            task["next_run"] = self.calculate_next_run(task)
        elif schedule_type == "Interval":
            interval_value = self.interval_value.get()
            if not interval_value.isdigit() or int(interval_value) <= 0:
                messagebox.showwarning("Input Error", "Interval must be a positive integer.")
                return
            interval_value = int(interval_value)
            interval_unit = self.interval_unit.get()
            interval_seconds = interval_value
            if interval_unit == "Minutes":
                interval_seconds *= 60
            elif interval_unit == "Hours":
                interval_seconds *= 3600
            task["interval_seconds"] = interval_seconds
            task["next_run"] = datetime.now() + timedelta(seconds=interval_seconds)
            task["schedule_details"] = f"Every {interval_value} {interval_unit.lower()}"
        else:
            messagebox.showwarning("Input Error", "Invalid schedule type.")
            return

        with self.lock:
            self.scheduled_tasks.append(task)
            self.save_scheduled_tasks()

        # Update task list in GUI
        self.task_list.insert('', 'end', values=(
            task_name, schedule_type, task["next_run"].strftime("%Y-%m-%d %H:%M:%S"),
            command, working_dir or "", task["schedule_details"],
            close_after if close_after is not None else "Unlimited",
            "Yes" if save_output_enabled else "No"
        ))

        # Clear input fields
        self.task_name_entry.delete(0, 'end')
        self.command_entry.delete(0, 'end')
        self.working_dir_entry.delete(0, 'end')
        self.close_after_entry.delete(0, 'end')
        self.save_output_var.set(False)
        self.toggle_save_output()

    def calculate_next_run(self, task):
        """Calculate the next run time for recurring tasks."""
        now = datetime.now()
        frequency = task["frequency"]
        time_parts = task["time_of_day"].split(":")
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        time_of_day = timedelta(hours=hours, minutes=minutes)
        next_run = datetime.combine(now.date(), datetime.min.time()) + time_of_day

        if frequency == "Daily":
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == "Weekly":
            days_of_week = task["days_of_week"]
            days_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            today = now.weekday()
            days_indices = [days_mapping[day] for day in days_of_week]
            days_ahead = [(day - today) % 7 for day in days_indices]
            days_ahead = [day if day != 0 or next_run > now else 7 for day in days_ahead]
            min_days_ahead = min(days_ahead)
            next_run += timedelta(days=min_days_ahead)
        elif frequency == "Monthly":
            day = now.day
            if next_run <= now:
                month = now.month + 1 if now.month < 12 else 1
                year = now.year + 1 if month == 1 else now.year
                next_run = datetime(year, month, day, next_run.hour, next_run.minute)
        return next_run

    def delete_task(self):
        """Delete the selected task from the scheduler."""
        selected_item = self.task_list.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a task to delete.")
            return

        task_index = self.task_list.index(selected_item)
        with self.lock:
            del self.scheduled_tasks[task_index]
            self.save_scheduled_tasks()

        self.task_list.delete(selected_item)

    def populate_task_list(self):
        """Populate the task list from the scheduled tasks."""
        for task in self.scheduled_tasks:
            self.task_list.insert('', 'end', values=(
                task["task_name"], task["schedule_type"],
                task["next_run"].strftime("%Y-%m-%d %H:%M:%S"),
                task["command"], task.get("working_directory") or "", task.get("schedule_details") or "",
                task.get("close_after", "Unlimited"),
                "Yes" if task.get("save_output", {}).get("enabled") else "No"
            ))

    def run_scheduler(self):
        """Run scheduled tasks based on their schedules."""
        while True:
            now = datetime.now()
            tasks_to_reschedule = []
            with self.lock:
                for index, task in enumerate(self.scheduled_tasks.copy()):
                    if now >= task["next_run"]:
                        # Execute the task
                        self.execute_task(task)

                        # Increment run count
                        task["run_count"] += 1

                        # Check if task should be closed after a certain number of executions
                        if task["close_after"] is not None and task["run_count"] >= task["close_after"]:
                            # Remove task
                            self.scheduled_tasks.pop(index)
                            self.delete_task_in_gui(index)
                            continue  # Skip rescheduling

                        # Determine next run time based on schedule type
                        next_run = self.get_next_run_time(task)
                        if next_run:
                            task["next_run"] = next_run
                            tasks_to_reschedule.append((index, next_run))
                        else:
                            # Remove one-time tasks after execution
                            self.scheduled_tasks.pop(index)
                            self.delete_task_in_gui(index)

                self.save_scheduled_tasks()

            # Update the GUI for rescheduled tasks
            for index, next_run in tasks_to_reschedule:
                self.update_task_in_gui(index, next_run)

            time.sleep(1)  # Sleep briefly to prevent excessive CPU usage

    def get_next_run_time(self, task):
        """Calculate the next run time based on the task's schedule."""
        now = datetime.now()
        schedule_type = task["schedule_type"]
        if schedule_type == "One-time":
            return None  # One-time tasks are not rescheduled
        elif schedule_type == "Recurring":
            return self.calculate_next_run(task)
        elif schedule_type == "Interval":
            return now + timedelta(seconds=task["interval_seconds"])
        return None

    def execute_task(self, task):
        """Execute the specified task."""
        command = task["command"]
        working_directory = task.get("working_directory")
        save_output = task.get("save_output", {})
        save_output_enabled = save_output.get("enabled", False)
        output_method = save_output.get("method")
        output_path = save_output.get("path")

        try:
            if save_output_enabled and output_method and output_path:
                if output_method == "single_file":
                    # Append output to single file with timestamp
                    with open(output_path, 'a') as output_file:
                        output_file.write(f"\n--- Output at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                        process = subprocess.Popen(
                            command, cwd=working_directory, shell=True,
                            stdout=output_file, stderr=subprocess.STDOUT
                        )
                        process.wait()
                elif output_method == "separate_files":
                    # Save output to a separate file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_name = f"{task['task_name']}_{timestamp}.txt"
                    output_file_path = os.path.join(output_path, file_name)
                    with open(output_file_path, 'w') as output_file:
                        process = subprocess.Popen(
                            command, cwd=working_directory, shell=True,
                            stdout=output_file, stderr=subprocess.STDOUT
                        )
                        process.wait()
            else:
                subprocess.Popen(command, cwd=working_directory, shell=True)
            # Update GUI (must be done on the main thread)
            self.tab.after(0, lambda: messagebox.showinfo(
                "Task Executed", f"Task '{task['task_name']}' has been executed."
            ))
        except Exception as e:
            self.tab.after(0, lambda: messagebox.showerror(
                "Execution Error", f"Failed to execute task '{task['task_name']}':\n{str(e)}"
            ))

    def update_task_in_gui(self, index, next_run):
        """Update the 'Next Run' time in the GUI for a task."""
        # Must be called from the main thread
        def update():
            try:
                item_id = self.task_list.get_children()[index]
                values = list(self.task_list.item(item_id, 'values'))
                values[2] = next_run.strftime("%Y-%m-%d %H:%M:%S")
                self.task_list.item(item_id, values=values)
            except IndexError:
                pass  # Task might have been deleted

        self.tab.after(0, update)

    def delete_task_in_gui(self, index):
        """Delete a task from the GUI task list."""
        def delete():
            try:
                item_id = self.task_list.get_children()[index]
                self.task_list.delete(item_id)
            except IndexError:
                pass  # Task might have been deleted already

        self.tab.after(0, delete)

