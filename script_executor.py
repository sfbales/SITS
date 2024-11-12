import os
import sys
import json
import threading
import queue
import subprocess
import ast
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import importlib.util
import stat
import platform
import shlex
import shutil


class ScriptExecutor:
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    CONFIG_FILE = os.path.join(CONFIG_DIR, "last_directory.json")  # Configuration file to store last directory

    def __init__(self, parent):
        self.parent = parent
        self.output_queue = queue.Queue()
        self.create_widgets()
        self.load_last_directory()
        self.parent.root.after(100, self.process_output_queue)

    def create_widgets(self):
        """Initializes the Script Executor tab widgets."""
        self.script_tab = ttk.Frame(self.parent.notebook)
        self.parent.notebook.add(self.script_tab, text="Script Executor")

        # Configure grid weights
        self.script_tab.grid_rowconfigure(4, weight=1)
        self.script_tab.grid_columnconfigure(0, weight=1)

        # Frame for directory selection and search
        script_operation_frame = ttk.Frame(self.script_tab)
        script_operation_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        script_operation_frame.grid_columnconfigure(1, weight=1)

        # Directory selection
        self.directory_var = tk.StringVar()
        ttk.Label(script_operation_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.directory_entry = ttk.Entry(script_operation_frame, textvariable=self.directory_var, width=50)
        self.directory_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        browse_button = ttk.Button(script_operation_frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        search_button = ttk.Button(script_operation_frame, text="Search", command=self.search_scripts)
        search_button.grid(row=0, column=3, padx=5, pady=5)

        # Frame for script list and scrollbar
        script_list_frame = ttk.Frame(self.script_tab)
        script_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        script_list_frame.grid_columnconfigure(0, weight=1)
        script_list_frame.grid_rowconfigure(0, weight=1)

        # Treeview to display scripts
        script_columns = ("Script Path",)
        self.script_tree = ttk.Treeview(script_list_frame, columns=script_columns, show='headings')
        self.script_tree.heading("Script Path", text="Script Path")
        self.script_tree.column("Script Path", anchor='w')
        self.script_tree.grid(row=0, column=0, sticky='nsew')

        # Scrollbar for the Treeview
        script_scrollbar = ttk.Scrollbar(script_list_frame, orient="vertical", command=self.script_tree.yview)
        self.script_tree.configure(yscroll=script_scrollbar.set)
        script_scrollbar.grid(row=0, column=1, sticky='ns')

        # Bind single-click event to show dependencies
        self.script_tree.bind("<ButtonRelease-1>", self.show_dependencies)

        # Execute and Make Executable Buttons Frame
        buttons_frame = ttk.Frame(self.script_tab)
        buttons_frame.grid(row=2, column=0, padx=10, pady=5, sticky='ew')

        # Execute Button
        self.execute_button = ttk.Button(buttons_frame, text="Execute", command=self.execute_selected_script)
        self.execute_button.pack(side='left', padx=5)

        # Make Executable Button
        self.make_executable_button = ttk.Button(
            buttons_frame,
            text="Make Executable",
            command=self.make_selected_script_executable
        )
        self.make_executable_button.pack(side='left', padx=5)

        # Frame for dependencies display
        dependencies_frame = ttk.Frame(self.script_tab)
        dependencies_frame.grid(row=3, column=0, padx=10, pady=5, sticky='ew')
        dependencies_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(dependencies_frame, text="Dependencies:").grid(row=0, column=0, padx=5, pady=5, sticky='nw')
        self.dependencies_text = scrolledtext.ScrolledText(
            dependencies_frame, wrap='word', state='disabled', height=5
        )
        self.dependencies_text.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Frame for output display
        output_frame = ttk.Frame(self.script_tab)
        output_frame.grid(row=4, column=0, padx=10, pady=10, sticky='nsew')
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # ScrolledText widget to display script output
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap='word', state='disabled')
        self.output_text.grid(row=0, column=0, sticky='nsew')

        # Scrollbar for the output ScrolledText
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscroll=output_scrollbar.set)
        output_scrollbar.grid(row=0, column=1, sticky='ns')

    def load_last_directory(self):
        """Loads the last used directory from a configuration file."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as file:
                    last_directory = json.load(file).get("last_directory", "")
                    if os.path.isdir(last_directory):
                        self.directory_var.set(last_directory)
                        self.search_scripts()  # Populate scripts on launch if directory exists
            except json.JSONDecodeError:
                pass  # Ignore JSON errors

    def save_last_directory(self, directory):
        """Saves the last used directory to a configuration file."""
        try:
            with open(self.CONFIG_FILE, "w") as file:
                json.dump({"last_directory": directory}, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

    def browse_directory(self):
        """Opens a dialog to browse and select a directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.directory_var.set(directory)
            self.save_last_directory(directory)
            self.search_scripts()

    def search_scripts(self):
        """Searches for .py files in the selected directory and populates the script_tree."""
        directory = self.directory_var.get()
        if not directory:
            messagebox.showwarning("Input Error", "Please select a directory to search.")
            return
        threading.Thread(target=self.search_scripts_thread, args=(directory,), daemon=True).start()

    def search_scripts_thread(self, directory):
        """Thread target for searching scripts."""
        py_files = []
        for root_dir, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root_dir, file)
                    py_files.append(full_path)
        self.parent.root.after(0, lambda: self.populate_script_tree(py_files))

    def populate_script_tree(self, scripts):
        """Populates the Treeview with the list of Python scripts."""
        self.script_tree.delete(*self.script_tree.get_children())
        if scripts:
            for script in scripts:
                self.script_tree.insert('', 'end', values=(script,))
        else:
            messagebox.showinfo("Info", "No .py files found in the selected directory.")

    def show_dependencies(self, event=None):
        """Displays the dependencies for the selected script."""
        selected_item = self.script_tree.selection()
        if selected_item:
            script_path = self.script_tree.item(selected_item)['values'][0]
            threading.Thread(
                target=self.extract_and_display_dependencies, args=(script_path,), daemon=True
            ).start()

    def extract_and_display_dependencies(self, script_path):
        """Extracts and displays dependencies in a thread."""
        dependencies = self.extract_dependencies(script_path)
        missing_deps = self.check_missing_dependencies(dependencies)
        self.parent.root.after(0, lambda: self.display_dependencies(dependencies, missing_deps))

    def extract_dependencies(self, script_path):
        """Parses the Python script to extract imported modules/packages."""
        dependencies = set()
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                node = ast.parse(file.read(), filename=script_path)
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Import):
                    for alias in stmt.names:
                        module = alias.name.split('.')[0]
                        dependencies.add(module)
                elif isinstance(stmt, ast.ImportFrom):
                    if stmt.module:
                        module = stmt.module.split('.')[0]
                        dependencies.add(module)
        except Exception as e:
            self.output_queue.put(f"Failed to extract dependencies from {script_path}:\n{str(e)}\n")
        return dependencies

    def check_missing_dependencies(self, dependencies):
        """Checks which dependencies are not installed."""
        missing = []
        for dependency in dependencies:
            if dependency in sys.builtin_module_names:
                continue  # Skip built-in modules
            if importlib.util.find_spec(dependency) is None:
                missing.append(dependency)
        return missing

    def display_dependencies(self, dependencies, missing_deps):
        """Displays dependencies and highlights missing ones."""
        self.dependencies_text.configure(state='normal')
        self.dependencies_text.delete('1.0', tk.END)

        if dependencies:
            for dep in sorted(dependencies):
                if dep in missing_deps:
                    self.dependencies_text.insert(tk.END, f"{dep} (Missing)\n")
                else:
                    self.dependencies_text.insert(tk.END, f"{dep}\n")
        else:
            self.dependencies_text.insert(tk.END, "No dependencies found.")

        self.dependencies_text.configure(state='disabled')

    def execute_selected_script(self):
        """Executes the selected Python script, possibly in a terminal."""
        selected_item = self.script_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a script to execute.")
            return

        script_path = self.script_tree.item(selected_item)['values'][0]
        if not os.path.isfile(script_path):
            messagebox.showerror("File Error", f"The selected script does not exist:\n{script_path}")
            return

        # Ask the user if they want to open the script in a terminal
        open_in_terminal = messagebox.askyesno(
            "Open in Terminal",
            "Does this script require a terminal window? Click 'Yes' to open in terminal."
        )

        # Disable the execute button
        self.execute_button.config(state='disabled')

        # Clear previous output
        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state='disabled')

        # Start execution in a separate thread
        threading.Thread(
            target=self.run_script_with_button_control,
            args=(script_path, open_in_terminal),
            daemon=True
        ).start()

    def make_selected_script_executable(self):
        """Makes the selected Python script executable by applying chmod +x."""
        selected_item = self.script_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a script to make executable.")
            return

        script_path = self.script_tree.item(selected_item)['values'][0]
        if not os.path.isfile(script_path):
            messagebox.showerror("File Error", f"The selected script does not exist:\n{script_path}")
            return

        # Check if the OS is Unix-like
        if os.name != 'posix':
            messagebox.showinfo("Not Applicable", "Make Executable is only applicable on Unix-like systems.")
            return

        try:
            # Get current permissions
            current_permissions = os.stat(script_path).st_mode
            # Add execute permissions for user, group, and others
            os.chmod(
                script_path,
                current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )
            messagebox.showinfo("Success", f"Successfully made the script executable:\n{script_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to make the script executable:\n{str(e)}")

    def run_script_with_button_control(self, script_path, open_in_terminal):
        """Runs the script and manages the execute button state."""
        try:
            # Execute the script
            self.run_script(script_path, open_in_terminal)
        finally:
            # Re-enable the execute button
            self.parent.root.after(0, self.enable_execute_button)

    def enable_execute_button(self):
        """Enables the execute button."""
        self.execute_button.config(state='normal')

    def run_script(self, script_path, open_in_terminal):
        """Runs the selected Python script and captures its output."""
        try:
            if open_in_terminal:
                # Platform-specific commands to open a terminal
                if platform.system() == 'Windows':
                    command = f'start cmd.exe /k "{sys.executable} {script_path}"'
                    subprocess.Popen(command, shell=True)
                elif platform.system() == 'Darwin':  # macOS
                    command = f'osascript -e \'tell application "Terminal" to do script "{shlex.quote(sys.executable)} {shlex.quote(script_path)}"\''
                    subprocess.Popen(command, shell=True)
                elif platform.system() == 'Linux':
                    # Attempt to use common terminal emulators
                    terminals = ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal']
                    for term in terminals:
                        if shutil.which(term):
                            command = [term, '-e', f'{sys.executable} {script_path}']
                            subprocess.Popen(command)
                            break
                    else:
                        messagebox.showerror(
                            "Error",
                            "No supported terminal emulator found. Please install xterm, gnome-terminal, or konsole."
                        )
                else:
                    messagebox.showerror("Error", "Unsupported operating system.")
            else:
                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                def read_stream(stream):
                    for line in iter(stream.readline, ''):
                        self.output_queue.put(line)
                    stream.close()

                stdout_thread = threading.Thread(target=read_stream, args=(process.stdout,))
                stderr_thread = threading.Thread(target=read_stream, args=(process.stderr,))

                stdout_thread.start()
                stderr_thread.start()

                process.wait()
                stdout_thread.join()
                stderr_thread.join()

                self.output_queue.put(f"\nScript exited with return code {process.returncode}\n")
        except Exception as e:
            self.output_queue.put(f"\nFailed to execute script:\n{str(e)}\n")

    def process_output_queue(self):
        """Processes the output queue and updates the output_text widget."""
        while not self.output_queue.empty():
            line = self.output_queue.get()
            self.output_text.configure(state='normal')
            self.output_text.insert(tk.END, line)
            self.output_text.see(tk.END)
            self.output_text.configure(state='disabled')
        self.parent.root.after(100, self.process_output_queue)

