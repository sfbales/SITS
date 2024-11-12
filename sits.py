import os
import importlib
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import traceback
import subprocess
import sys
import psutil
from multiprocessing import Process

# Configure logging to capture initialization and process management errors
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


class UnifiedApp:
    def __init__(self, root):
        logging.info("Initializing SITSv1.0")
        self.root = root
        self.root.title("SITSv1.0")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Initialize core modules
        self.init_package_manager()
        self.init_command_executor()
        self.init_commands_manager()
        self.init_script_executor()
        self.init_schedule_manager()
        self.init_api_manager()
        self.init_about()



    def init_package_manager(self):
        """Initialize the Package Manager with lazy import and error handling."""
        try:
            logging.info("Initializing Package Manager...")
            from package_manager import PackageManager
            self.package_manager = PackageManager(self)
            self.notebook.add(self.package_manager.package_tab, text="Package Manager")
            logging.info("Package Manager initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Package Manager: {e}")
            traceback.print_exc()

    def init_command_executor(self):
        """Initialize the Command Executor with lazy import and error handling."""
        try:
            logging.info("Initializing Command Executor...")
            from command_executor import CommandExecutor
            self.command_executor = CommandExecutor(self)
            self.notebook.add(self.command_executor.command_tab, text="Command Executor")
            logging.info("Command Executor initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Command Executor: {e}")
            traceback.print_exc()

    def init_commands_manager(self):
        """Initialize the Commands Manager with lazy import and error handling."""
        try:
            logging.info("Initializing Commands Manager...")
            from commands_manager import CommandsManager
            self.commands_manager = CommandsManager(self)
            self.notebook.add(self.commands_manager.tab, text="Commands Manager")
            logging.info("Commands Manager initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Commands Manager: {e}")
            traceback.print_exc()

    def init_script_executor(self):
        """Initialize the Script Executor with lazy import and error handling."""
        try:
            logging.info("Initializing Script Executor...")
            from script_executor import ScriptExecutor
            self.script_executor = ScriptExecutor(self)
            self.notebook.add(self.script_executor.script_tab, text="Script Executor")
            logging.info("Script Executor initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Script Executor: {e}")
            traceback.print_exc()

    def init_schedule_manager(self):
        """Initialize the Schedule Manager with lazy import and error handling."""
        try:
            logging.info("Initializing Schedule Manager...")
            from schedule_manager import ScheduleManager
            self.schedule_manager = ScheduleManager(self.notebook)
            logging.info("Schedule Manager initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Schedule Manager: {e}")

    def init_api_manager(self):
        """Initialize the API Manager with lazy import and error handling."""
        try:
            logging.info("Initializing API Manager...")
            from api_manager import ApiManager
            self.api_manager = ApiManager(self.notebook)
            logging.info("API Manager initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize API Manager: {e}")
            traceback.print_exc()
            

    def init_about(self):
        """Initialize the About tab."""
        try:
            logging.info("Initializing About...")
            import about  # Import about locally to avoid global dependency
            self.about = about.about(self.notebook)
            if self.about:
                self.notebook.add(self.about, text="About")
                logging.info("About initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize About: {e}")
            traceback.print_exc()



if __name__ == "__main__":
    root = tk.Tk()
    app = UnifiedApp(root)
    root.mainloop()

