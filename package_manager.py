import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
import subprocess
from datetime import datetime
import sys
import queue

class PackageManager:
    def __init__(self, parent):
        self.parent = parent
        self.all_packages = []
        self.ui_queue = queue.Queue()  # Queue for handling UI updates
        self.create_widgets()
        self.list_packages()
        self.parent.root.after(100, self.process_ui_queue)  # Start processing UI queue

    def create_widgets(self):
        """Initializes the Package Manager tab widgets."""
        self.package_tab = ttk.Frame(self.parent.notebook)
        self.parent.notebook.add(self.package_tab, text="Package Manager")
        self.package_tab.grid_rowconfigure(2, weight=1)
        self.package_tab.grid_columnconfigure(0, weight=1)

        # Frame for package operations
        operation_frame = tk.Frame(self.package_tab)
        operation_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        operation_frame.grid_columnconfigure(1, weight=1)

        # Package entry field
        tk.Label(operation_frame, text="Package Name:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.package_entry = tk.Entry(operation_frame, width=30)
        self.package_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Buttons for install, uninstall, upgrade, and refresh
        ttk.Button(operation_frame, text="Install", command=self.install_package).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(operation_frame, text="Uninstall", command=self.uninstall_package).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(operation_frame, text="Upgrade", command=self.upgrade_package).grid(row=0, column=4, padx=5, pady=5)
        
        # Refresh button
        refresh_button = ttk.Button(operation_frame, text="Refresh", command=self.list_packages)
        refresh_button.grid(row=0, column=5, padx=5, pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(operation_frame, mode='indeterminate')
        self.progress.grid(row=0, column=6, padx=5, pady=5)
        self.progress.grid_remove()

        # Search functionality
        tk.Label(operation_frame, text="Search:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(operation_frame, textvariable=self.search_var)
        search_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        search_entry.bind('<KeyRelease>', self.filter_packages)

        # Separator
        ttk.Separator(self.package_tab, orient='horizontal').grid(row=1, column=0, sticky='ew', padx=10, pady=5)

        # PanedWindow for package list and details
        paned_window = ttk.PanedWindow(self.package_tab, orient='horizontal')
        paned_window.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')

        # Treeview for package listing
        self.setup_treeview(paned_window)

        # Package details and log
        self.setup_details_frame(paned_window)

    def setup_treeview(self, paned_window):
        """Sets up the Treeview widget for displaying packages."""
        tree_frame = tk.Frame(self.package_tab)
        paned_window.add(tree_frame, weight=3)

        package_columns = ("Package", "Version")
        self.package_tree = ttk.Treeview(tree_frame, columns=package_columns, show='headings')
        self.package_tree.heading("Package", text="Package", command=lambda: self.sort_packages("Package", False))
        self.package_tree.heading("Version", text="Version", command=lambda: self.sort_packages("Version", False))
        self.package_tree.column("Package", anchor='w', width=400)
        self.package_tree.column("Version", anchor='center', width=100)
        self.package_tree.pack(side='left', fill='both', expand=True)

        # Scrollbar for Treeview
        package_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.package_tree.yview)
        self.package_tree.configure(yscrollcommand=package_scrollbar.set)
        package_scrollbar.pack(side='right', fill='y')

        # Bind events for package selection and details
        self.package_tree.bind("<Double-1>", self.populate_package_name)
        self.package_tree.bind("<<TreeviewSelect>>", self.on_package_select)

    def setup_details_frame(self, paned_window):
        """Sets up the details frame for package information and logs."""
        details_frame = tk.Frame(self.package_tab, relief='sunken', borderwidth=1)
        paned_window.add(details_frame, weight=2)

        tk.Label(details_frame, text="Package Details", font=('Arial', 12, 'bold')).pack(anchor='nw', padx=5, pady=5)
        self.details_pane = scrolledtext.ScrolledText(details_frame, wrap='word', state='disabled', height=10)
        self.details_pane.pack(fill='both', expand=True, padx=5, pady=5)

        tk.Label(details_frame, text="Operations Log", font=('Arial', 12, 'bold')).pack(anchor='nw', padx=5, pady=(10, 5))
        self.operations_pane = scrolledtext.ScrolledText(details_frame, wrap='word', state='disabled', height=10)
        self.operations_pane.pack(fill='both', expand=True, padx=5, pady=5)

    def list_packages(self):
        """Lists all installed packages and populates the Treeview."""
        threading.Thread(target=self.list_packages_thread, daemon=True).start()

    def list_packages_thread(self):
        self.ui_queue.put(self.show_progress)
        
        returncode, output, error = self.run_command([sys.executable, "-m", "pip", "list", "--format=json"])
        
        self.ui_queue.put(self.hide_progress)
        
        if returncode == 0:
            try:
                packages = json.loads(output)
                self.all_packages = packages
                self.ui_queue.put(lambda: self.populate_package_tree(packages))
            except json.JSONDecodeError:
                self.log_operation("[ERROR] Failed to parse package list.")
        else:
            self.log_operation(f"[ERROR] {error.strip() if error else 'Unknown error occurred while listing packages.'}")

    def process_ui_queue(self):
        """Processes the UI queue on the main thread to update the GUI safely."""
        while not self.ui_queue.empty():
            command = self.ui_queue.get()
            command()
        self.parent.root.after(100, self.process_ui_queue)  # Keep checking the queue

    def populate_package_tree(self, packages):
        """Populates Treeview with packages."""
        self.package_tree.delete(*self.package_tree.get_children())
        for pkg in packages:
            self.package_tree.insert('', 'end', values=(pkg['name'], pkg['version']))

    def show_progress(self):
        """Shows and starts the progress bar."""
        self.progress.grid()
        self.progress.start()

    def hide_progress(self):
        """Stops and hides the progress bar."""
        self.progress.stop()
        self.progress.grid_remove()

    def log_operation(self, message):
        """Logs operation messages with timestamps."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.operations_pane.configure(state='normal')
        self.operations_pane.insert(tk.END, f"[{timestamp}] {message}\n")
        self.operations_pane.see(tk.END)
        self.operations_pane.configure(state='disabled')

    def install_package(self):
        """Installs a specified Python package."""
        package = self.package_entry.get().strip()
        if package:
            if messagebox.askyesno("Confirm Install", f"Are you sure you want to install '{package}'?"):
                self.show_progress()
                threading.Thread(target=self.manage_package_thread, args=(["install"], package, "install"), daemon=True).start()

    def uninstall_package(self):
        """Uninstalls a specified Python package."""
        package = self.package_entry.get().strip()
        if package:
            if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall '{package}'?"):
                self.show_progress()
                threading.Thread(target=self.manage_package_thread, args=(["uninstall", "-y"], package, "uninstall"), daemon=True).start()

    def upgrade_package(self):
        """Upgrades a specified Python package."""
        package = self.package_entry.get().strip()
        if package:
            if messagebox.askyesno("Confirm Upgrade", f"Are you sure you want to upgrade '{package}'?"):
                self.show_progress()
                threading.Thread(target=self.manage_package_thread, args=(["install", "--upgrade"], package, "upgrade"), daemon=True).start()

    def manage_package_thread(self, command, package, action):
        """Threaded function for managing package installation/uninstallation/upgrade."""
        self.log_operation(f"Starting {action} of '{package}'.")
        returncode, stdout, stderr = self.run_command([sys.executable, "-m", "pip"] + command + [package])
        self.hide_progress()
        if returncode == 0:
            self.log_operation(f"[SUCCESS] {stdout.strip() if stdout else f'{action.capitalize()} completed successfully.'}")
        else:
            self.log_operation(f"[ERROR] {stderr.strip() if stderr else 'Unknown error occurred.'}")
        self.list_packages()

    def run_command(self, command):
        """Runs a command in the subprocess and returns the result."""
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def filter_packages(self, event):
        """Filters the packages based on search input."""
        search_term = self.search_var.get().lower()
        filtered_packages = [pkg for pkg in self.all_packages if search_term in pkg['name'].lower()]
        self.populate_package_tree(filtered_packages)

    def populate_package_name(self, event):
        """Populates the selected package name into the entry for further actions."""
        selected_item = self.package_tree.selection()
        if selected_item:
            package_name = self.package_tree.item(selected_item)["values"][0]
            self.package_entry.delete(0, tk.END)
            self.package_entry.insert(0, package_name)

    def on_package_select(self, event):
        """Shows the details of the selected package in the details pane."""
        selected_item = self.package_tree.selection()
        if selected_item:
            package_name = self.package_tree.item(selected_item)["values"][0]
            package_details = next((pkg for pkg in self.all_packages if pkg['name'] == package_name), None)
            if package_details:
                details_text = f"Name: {package_details['name']}\nVersion: {package_details['version']}"
                self.details_pane.configure(state='normal')
                self.details_pane.delete("1.0", tk.END)
                self.details_pane.insert(tk.END, details_text)
                self.details_pane.configure(state='disabled')

