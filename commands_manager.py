import os
import sys
import json
import subprocess
import shlex
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class CommandsManager:
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    COMMAND_FILE = os.path.join(CONFIG_DIR, "commands.json")
    DIRECTORY_FILE = os.path.join(CONFIG_DIR, "recent_directories.json")
    MAX_RECENT_DIRECTORIES = 10  # Maximum number of recent directories to keep

    def __init__(self, parent):
        """Initializes the Commands Manager with enhanced features."""
        self.parent = parent
        self.commands = []
        self.recent_directories = []
        self.current_directory = os.getcwd()
        self.create_widgets()
        self.load_commands()
        self.load_recent_directories()

    def create_widgets(self):
        """Creates and configures the GUI widgets for the Commands Manager."""
        # Create a new tab within the notebook
        self.tab = ttk.Frame(self.parent.notebook)
        self.parent.notebook.add(self.tab, text="Commands Manager")

        # Configure grid layout
        self.tab.grid_rowconfigure(2, weight=1)
        self.tab.grid_columnconfigure(0, weight=1)

        # Frame to organize the layout
        main_frame = ttk.Frame(self.tab)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Entry field to add a new command
        self.command_entry = ttk.Entry(main_frame)
        self.command_entry.grid(row=0, column=0, padx=(0, 5), pady=5, sticky='ew')
        self.command_entry.bind('<Return>', lambda event: self.add_command())

        # Buttons to add, edit, and delete commands
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=1, pady=5, sticky='nsew')

        self.add_button = ttk.Button(button_frame, text="Add", command=self.add_command)
        self.add_button.pack(fill='x', pady=2)

        self.edit_button = ttk.Button(button_frame, text="Edit", command=self.edit_command)
        self.edit_button.pack(fill='x', pady=2)

        self.delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_command)
        self.delete_button.pack(fill='x', pady=2)

        # Listbox to display the commands
        self.command_listbox = tk.Listbox(main_frame)
        self.command_listbox.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.command_listbox.bind('<Double-Button-1>', self.start_commands_with_command)

        # Scrollbar for the command listbox
        command_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.command_listbox.yview)
        self.command_listbox.configure(yscrollcommand=command_scrollbar.set)
        command_scrollbar.grid(row=1, column=2, sticky='ns')

        # Frame for directory selection
        directory_frame = ttk.Frame(self.tab)
        directory_frame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        directory_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(directory_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.directory_var = tk.StringVar(value=self.current_directory)
        self.directory_entry = ttk.Entry(directory_frame, textvariable=self.directory_var)
        self.directory_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        browse_button = ttk.Button(directory_frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Recent directories dropdown
        ttk.Label(directory_frame, text="Recent:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.recent_dirs_var = tk.StringVar()
        self.recent_dirs_combo = ttk.Combobox(directory_frame, textvariable=self.recent_dirs_var, state='readonly')
        self.recent_dirs_combo['values'] = self.recent_directories
        self.recent_dirs_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.recent_dirs_combo.bind('<<ComboboxSelected>>', self.select_recent_directory)

        # Start command button
        self.start_commands_button = ttk.Button(self.tab, text="Start Command", command=self.start_commands_with_command)
        self.start_commands_button.grid(row=2, column=0, pady=10)

    def add_command(self):
        """Adds a new command to the list and saves it."""
        command = self.command_entry.get().strip()
        if command:
            self.commands.append(command)
            self.command_listbox.insert(tk.END, command)
            self.command_entry.delete(0, tk.END)
            self.save_commands()
        else:
            messagebox.showwarning("Input Error", "Please enter a command to add.")

    def edit_command(self):
        """Edits the selected command."""
        selected = self.command_listbox.curselection()
        if selected:
            index = selected[0]
            current_command = self.commands[index]
            new_command = tk.simpledialog.askstring("Edit Command", "Modify the command:", initialvalue=current_command)
            if new_command:
                self.commands[index] = new_command.strip()
                self.command_listbox.delete(index)
                self.command_listbox.insert(index, self.commands[index])
                self.save_commands()
        else:
            messagebox.showwarning("Selection Error", "Please select a command to edit.")

    def delete_command(self):
        """Deletes the selected command after confirmation."""
        selected = self.command_listbox.curselection()
        if selected:
            index = selected[0]
            command_to_delete = self.commands[index]
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete:\n\n{command_to_delete}")
            if confirm:
                self.commands.pop(index)
                self.command_listbox.delete(index)
                self.save_commands()
        else:
            messagebox.showwarning("Selection Error", "Please select a command to delete.")

    def browse_directory(self):
        """Opens a dialog to browse and select a directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.set_current_directory(directory)

    def select_recent_directory(self, event):
        """Sets the current directory from the recent directories."""
        selected_directory = self.recent_dirs_var.get()
        if selected_directory and os.path.isdir(selected_directory):
            self.set_current_directory(selected_directory)
        else:
            messagebox.showwarning("Directory Error", "The selected directory does not exist.")

    def set_current_directory(self, directory):
        """Sets the current directory and updates recent directories."""
        self.current_directory = directory
        self.directory_var.set(directory)
        self.update_recent_directories(directory)

    def update_recent_directories(self, directory):
        """Updates the list of recent directories."""
        if directory in self.recent_directories:
            self.recent_directories.remove(directory)
        self.recent_directories.insert(0, directory)
        self.recent_directories = self.recent_directories[:self.MAX_RECENT_DIRECTORIES]
        self.recent_dirs_combo['values'] = self.recent_directories
        self.save_recent_directories()

    def start_commands_with_command(self, event=None):
        """Executes the selected command in a new terminal window."""
        selected = self.command_listbox.curselection()
        if selected:
            command = self.commands[selected[0]]
        else:
            messagebox.showwarning("Selection Error", "Please select a command to execute.")
            return

        directory = self.directory_var.get()
        if not os.path.isdir(directory):
            messagebox.showwarning("Directory Error", "The specified directory does not exist.")
            return

        # Determine the platform and choose the appropriate terminal emulator
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            terminal = shutil.which("gnome-terminal") or shutil.which("x-terminal-emulator") or shutil.which("xterm")
            if terminal:
                try:
                    # Prepare the command to change directory and execute the command
                    full_command = f"cd {shlex.quote(directory)} && {command}; exec bash"
                    subprocess.Popen([terminal, "--", "bash", "-c", full_command])
                except Exception as e:
                    messagebox.showerror("Execution Error", f"Failed to execute command:\n{str(e)}")
            else:
                messagebox.showwarning(
                    "Terminal Not Found",
                    "No suitable terminal emulator found. Please install one or run the command manually."
                )
        elif sys.platform.startswith('win'):
            try:
                # Use start to open a new command prompt window
                full_command = f'cd /d "{directory}" && {command}'
                subprocess.Popen(['cmd', '/k', full_command], shell=True)
            except Exception as e:
                messagebox.showerror("Execution Error", f"Failed to execute command:\n{str(e)}")
        else:
            messagebox.showwarning(
                "Unsupported Platform",
                "This function is not supported on your operating system."
            )

    def load_commands(self):
        """Loads commands from the JSON file."""
        if os.path.exists(self.COMMAND_FILE):
            try:
                with open(self.COMMAND_FILE, "r") as file:
                    self.commands = json.load(file)
                    for command in self.commands:
                        self.command_listbox.insert(tk.END, command)
            except json.JSONDecodeError:
                messagebox.showerror("Load Error", "Failed to decode commands.json. Starting with an empty list.")
                self.commands = []
        else:
            # If no file exists, start with an empty list
            self.commands = []

    def save_commands(self):
        """Saves the current list of commands to the JSON file."""
        try:
            with open(self.COMMAND_FILE, "w") as file:
                json.dump(self.commands, file)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save commands:\n{str(e)}")

    def load_recent_directories(self):
        """Loads recent directories from the JSON file."""
        if os.path.exists(self.DIRECTORY_FILE):
            try:
                with open(self.DIRECTORY_FILE, "r") as file:
                    self.recent_directories = json.load(file)
                    self.recent_dirs_combo['values'] = self.recent_directories
            except json.JSONDecodeError:
                messagebox.showerror("Load Error", "Failed to decode recent_directories.json.")
                self.recent_directories = []
        else:
            self.recent_directories = []

    def save_recent_directories(self):
        """Saves the recent directories to the JSON file."""
        try:
            with open(self.DIRECTORY_FILE, "w") as file:
                json.dump(self.recent_directories, file)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save recent directories:\n{str(e)}")

