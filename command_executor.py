import os
import sys
import subprocess
import shlex
import platform
import queue
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tkinter.font as tkFont
import re

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')

class CommandExecutor:
    def __init__(self, parent):
        self.parent = parent
        self.create_widgets()
        self.command_history = []
        self.history_index = None
        self.current_process = None
        self.expecting_input = False
        self.output_queue = queue.Queue()
        self.command_lock = threading.Lock()
        self.parent.root.after(20, self.process_command_output_queue)

    def create_widgets(self):
        """Initializes the Command Executor tab widgets."""
        self.command_tab = ttk.Frame(self.parent.notebook)
        self.parent.notebook.add(self.command_tab, text="Command Executor")

        # Configure grid weights
        self.command_tab.grid_rowconfigure(2, weight=1)
        self.command_tab.grid_columnconfigure(0, weight=1)

        # Frame for command input and controls
        command_input_frame = ttk.Frame(self.command_tab)
        command_input_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        command_input_frame.grid_columnconfigure(1, weight=1)

        # Command/Input entry
        ttk.Label(command_input_frame, text="Command/Input:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_input_frame, textvariable=self.command_var, width=70)
        self.command_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Bind Up and Down arrow keys for history navigation
        self.command_entry.bind("<Up>", self.navigate_history_up)
        self.command_entry.bind("<Down>", self.navigate_history_down)
        # Bind Enter key to execute command or send input
        self.command_entry.bind("<Return>", self.handle_enter_key)

        # Execute button
        self.execute_button = ttk.Button(command_input_frame, text="Execute", command=self.execute_command)
        self.execute_button.grid(row=0, column=2, padx=5, pady=5)

        # Cancel button (disabled initially)
        self.cancel_button = ttk.Button(command_input_frame, text="Cancel", command=self.cancel_command, state='disabled')
        self.cancel_button.grid(row=0, column=3, padx=5, pady=5)

        # Browse working directory button
        browse_button = ttk.Button(command_input_frame, text="Browse", command=self.browse_directory)
        browse_button.grid(row=1, column=2, padx=5, pady=5)

        # Save Output button
        save_button = ttk.Button(command_input_frame, text="Save Output", command=self.save_output)
        save_button.grid(row=1, column=3, padx=5, pady=5)

        # Working directory entry
        ttk.Label(command_input_frame, text="Working Dir:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.working_dir_var = tk.StringVar(value=os.getcwd())
        self.working_dir_entry = ttk.Entry(command_input_frame, textvariable=self.working_dir_var, width=70)
        self.working_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        # Progress indicator
        self.progress = ttk.Progressbar(command_input_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky='ew')
        self.progress.grid_remove()  # Hide initially

        # Frame for output display
        output_frame = ttk.Frame(self.command_tab)
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # Define font
        self.output_font = tkFont.Font(family="Courier", size=12)

        # ScrolledText widget to display command output
        self.command_output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap='word',
            state='disabled',
            bg='black',
            fg='green',
            insertbackground='white',
            font=self.output_font
        )
        self.command_output_text.grid(row=0, column=0, sticky='nsew')

        # Scrollbar for the ScrolledText
        command_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.command_output_text.yview)
        self.command_output_text.configure(yscrollcommand=command_scrollbar.set)
        command_scrollbar.grid(row=0, column=1, sticky='ns')

        # Configure text tags for stdout and stderr
        self.command_output_text.tag_configure('stdout', foreground='green', font=self.output_font)
        self.command_output_text.tag_configure('stderr', foreground='red', font=self.output_font)
        self.command_output_text.tag_configure('timestamp', foreground='yellow', font=self.output_font)
        self.command_output_text.tag_configure('input', foreground='cyan', font=self.output_font)

    def browse_directory(self):
        """Opens a dialog to browse and select a working directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.working_dir_var.set(directory)

    def handle_enter_key(self, event):
        """Handles the Enter key press in the command_entry."""
        if self.current_process and self.expecting_input:
            self.send_input()
        else:
            self.execute_command()

    def execute_command(self):
        """Executes the entered command in a separate thread."""
        command = self.command_var.get().strip()
        if command:
            # Add to command history
            self.command_history.append(command)
            self.history_index = None
            # Disable the Execute button and enable Cancel button
            self.disable_execute_button()
            self.enable_cancel_button()
            # Clear previous output
            self.clear_output()
            # Start progress indicator
            self.show_progress()
            # Start executing the command in a new thread
            threading.Thread(target=self.execute_command_thread, args=(command,), daemon=True).start()
            # Clear the command entry
            self.command_var.set('')
        else:
            messagebox.showwarning("Input Error", "Please enter a command to execute.")

    def execute_command_thread(self, command):
        """Thread target function to execute the command."""
        try:
            # Determine shell usage based on OS
            use_shell = platform.system() == "Windows"

            # Automatically append '-u' for Python scripts to enforce unbuffered output
            args = command
            if not use_shell:
                args = shlex.split(command)
                if args and args[0] in ["python", "python3"]:
                    args.insert(1, "-u")

            # Start the subprocess
            self.current_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                shell=use_shell,
                cwd=self.working_dir_var.get(),
                bufsize=1
            )

            # Reset the expecting_input flag
            self.expecting_input = False

            # Read stdout and stderr in separate threads
            stdout_thread = threading.Thread(target=self.read_stream, args=(self.current_process.stdout, 'stdout'), daemon=True)
            stderr_thread = threading.Thread(target=self.read_stream, args=(self.current_process.stderr, 'stderr'), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            # Wait for the subprocess to complete
            self.current_process.wait()

            # Wait for the threads to finish reading output
            stdout_thread.join()
            stderr_thread.join()

            # After subprocess ends
            if self.current_process.returncode != 0:
                self.output_queue.put((f"\n[ERROR] Command exited with return code {self.current_process.returncode}\n", 'stderr'))

        except Exception as e:
            self.output_queue.put((f"\n[EXCEPTION] {str(e)}\n", 'stderr'))
        finally:
            # Reset process reference
            self.current_process = None
            # Stop progress indicator
            self.hide_progress()
            # Enable Execute button and disable Cancel button
            self.enable_execute_button()
            self.disable_cancel_button()
            # Ensure the flag is reset
            self.expecting_input = False

    def read_stream(self, stream, tag):
        """Reads output from the subprocess's stream."""
        try:
            for line in iter(stream.readline, ''):
                if line == '':
                    break
                self.process_line(line, tag)
        except Exception as e:
            self.output_queue.put((f"[ERROR] Failed to read {tag}: {str(e)}\n", 'stderr'))
        finally:
            stream.close()

    def process_line(self, line, tag):
        """Processes each line from the subprocess output."""
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.output_queue.put((timestamp + line, tag))

        # Check for prompts indicating that input is expected
        if self.detect_prompt(line):
            self.expecting_input = True

    def detect_prompt(self, line):
        """Detects if the subprocess is expecting input."""
        prompt_patterns = [
            r'^(?:\[Y\/N\]|Enter choice:|Password:|Enter input:)',
            r'Press any key to continue',
            r'Do you want to proceed\?',
            r'Confirm\?',
            r'Provide input:',
            r'Enter your name:'
        ]
        for pattern in prompt_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def process_command_output_queue(self):
        """Processes the output queue and updates the command_output_text widget."""
        while not self.output_queue.empty():
            line, tag = self.output_queue.get()
            with self.command_lock:
                self.command_output_text.configure(state='normal')
                self.command_output_text.insert(tk.END, line, tag)
                self.command_output_text.see(tk.END)
                self.command_output_text.configure(state='disabled')
        self.parent.root.after(20, self.process_command_output_queue)

    def navigate_history_up(self, event):
        """Navigates up in the command history."""
        if self.command_history:
            if self.history_index is None:
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            self.command_var.set(self.command_history[self.history_index])
            self.command_entry.icursor(tk.END)

    def navigate_history_down(self, event):
        """Navigates down in the command history."""
        if self.command_history and self.history_index is not None:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_var.set(self.command_history[self.history_index])
            else:
                self.history_index = None
                self.command_var.set('')
            self.command_entry.icursor(tk.END)

    def cancel_command(self):
        """Cancels the currently running command."""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.output_queue.put(("[INFO] Terminating the command...\n", 'stdout'))
                self.disable_cancel_button()
            except Exception as e:
                self.output_queue.put((f"[ERROR] Failed to terminate process: {str(e)}\n", 'stderr'))

    def send_input(self):
        """Sends user input to the subprocess's stdin."""
        if self.current_process and self.current_process.stdin and self.expecting_input:
            user_input = self.command_var.get()
            try:
                self.current_process.stdin.write(user_input + '\n')
                self.current_process.stdin.flush()
                # Display the sent input
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                formatted_input = f"{timestamp}{user_input}\n"
                self.output_queue.put((formatted_input, 'input'))
                self.command_var.set('')
                self.expecting_input = False
            except Exception as e:
                messagebox.showerror("Input Error", f"Failed to send input:\n{str(e)}")

    def show_progress(self):
        """Shows and starts the progress bar."""
        self.progress.grid()
        self.progress.start()

    def hide_progress(self):
        """Stops and hides the progress bar."""
        self.progress.stop()
        self.progress.grid_remove()

    def enable_cancel_button(self):
        """Enables the Cancel button."""
        self.cancel_button.config(state='normal')

    def disable_cancel_button(self):
        """Disables the Cancel button."""
        self.cancel_button.config(state='disabled')

    def enable_execute_button(self):
        """Enables the Execute button."""
        self.execute_button.config(state='normal')

    def disable_execute_button(self):
        """Disables the Execute button."""
        self.execute_button.config(state='disabled')

    def clear_output(self):
        """Clears the command output textbox."""
        self.command_output_text.configure(state='normal')
        self.command_output_text.delete('1.0', tk.END)
        self.command_output_text.configure(state='disabled')

    def save_output(self):
        """Saves the command output to a text file."""
        content = self.command_output_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo("Info", "No data to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                messagebox.showinfo("Success", f"Data saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data:\n{str(e)}")

# Example usage within a Tkinter application
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Command Executor")
        self.root.geometry("1000x700")

        # Create Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Initialize CommandExecutor
        self.command_executor = CommandExecutor(self)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()

