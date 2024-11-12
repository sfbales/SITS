import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import time
import requests
import os
import threading
import sys

class ApiManager:
    def __init__(self, parent):
        self.parent = parent
        self.api_tab = ttk.Frame(parent)
        parent.add(self.api_tab, text="API Manager")

        # Token file path
        self.token_file = "ngrok_token.txt"
        self.ngrok_token = self.load_ngrok_token()

        # Process handles
        self.uvicorn_process = None
        self.ngrok_process = None

        # UI components
        self.status_label = tk.Label(self.api_tab, text="API Manager - Status: Not Running")
        self.status_label.pack(pady=10)

        self.start_button = tk.Button(self.api_tab, text="Start API", command=self.start_api)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.api_tab, text="Stop API", command=self.stop_api, state="disabled")
        self.stop_button.pack(pady=5)

        self.url_text = tk.Text(self.api_tab, height=1, width=50, state="disabled")
        self.url_text.pack(pady=5)

        # Ngrok Token Setup
        self.token_label = tk.Label(self.api_tab, text="Set Ngrok Token:")
        self.token_label.pack(pady=5)

        self.token_entry = tk.Entry(self.api_tab, width=40)
        self.token_entry.pack(pady=5)
        self.token_entry.insert(0, self.ngrok_token or "")

        self.token_button = tk.Button(self.api_tab, text="Save Token", command=self.save_ngrok_token)
        self.token_button.pack(pady=5)

        # Guide Label
        self.guide_label = tk.Label(
            self.api_tab,
            text=(
                "Note: For internet access, use ngrok if you haven't set up your own connection. "
                "See the guide in the code comments for more details."
            ),
            wraplength=400,
            justify="left",
        )
        self.guide_label.pack(pady=10)

        # Handle closing of the application
        self.api_tab.bind("<Destroy>", self.on_close)

    def load_ngrok_token(self):
        """Loads the ngrok token from a file if it exists."""
        if os.path.exists(self.token_file):
            with open(self.token_file, "r") as file:
                return file.read().strip()
        return None

    def save_ngrok_token(self):
        """Saves the entered ngrok token to a file."""
        self.ngrok_token = self.token_entry.get().strip()
        with open(self.token_file, "w") as file:
            file.write(self.ngrok_token)
        messagebox.showinfo("Info", "Ngrok token saved successfully.")

    def start_uvicorn(self):
        """Starts the Uvicorn server for the API."""
        print("Starting Uvicorn server for the API...")
        self.uvicorn_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
        )

    def start_ngrok(self):
        """Starts ngrok with the personal token and retrieves the public URL."""
        print("Starting ngrok...")
        if self.ngrok_token:
            # Authenticate with the user's token
            subprocess.run(["ngrok", "config", "add-authtoken", self.ngrok_token], check=True)
        self.ngrok_process = subprocess.Popen(
            ["ngrok", "http", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait for ngrok to initialize
        public_url = None
        max_attempts = 10
        for _ in range(max_attempts):
            try:
                time.sleep(1)
                response = requests.get("http://127.0.0.1:4040/api/tunnels")
                response.raise_for_status()
                tunnels = response.json().get('tunnels', [])
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"ngrok public URL: {public_url}")
                    break
            except requests.RequestException:
                continue
        else:
            print("Failed to retrieve ngrok URL.")
        return public_url

    def start_api(self):
        """Starts the API server and ngrok, then displays the public URL."""
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        threading.Thread(target=self.run_servers).start()

    def run_servers(self):
        """Runs the uvicorn and ngrok servers."""
        self.start_uvicorn()
        public_url = self.start_ngrok()
        if public_url:
            self.status_label.config(text="API Manager - Status: Running")
            self.url_text.config(state="normal")
            self.url_text.delete("1.0", tk.END)
            self.url_text.insert("1.0", public_url)
            self.url_text.config(state="disabled")
            print("API is now accessible at:", public_url)
        else:
            self.status_label.config(text="API Manager - Status: Failed to Start ngrok")
            self.stop_api()

    def stop_api(self):
        """Stops the API server and ngrok."""
        if self.uvicorn_process:
            print("Stopping Uvicorn server...")
            self.uvicorn_process.terminate()
            self.uvicorn_process.wait()
            self.uvicorn_process = None

        if self.ngrok_process:
            print("Stopping ngrok...")
            self.ngrok_process.terminate()
            self.ngrok_process.wait()
            self.ngrok_process = None

        self.status_label.config(text="API Manager - Status: Not Running")
        self.url_text.config(state="normal")
        self.url_text.delete("1.0", tk.END)
        self.url_text.config(state="disabled")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def on_close(self, event):
        """Ensures that processes are terminated when the GUI is closed."""
        self.stop_api()

# Guide:
# Guide for Exposing Your API Over the Internet
# ---------------------------------------------
#
# This application allows you to manage a local API server using Uvicorn and expose it over the internet using ngrok.
# If you haven't set up your own server or port forwarding, ngrok is a simple way to make your local API accessible
# over the internet.
#
# **Steps to Use ngrok:**
#
# 1. **Install ngrok:**
#    - Download ngrok from [ngrok.com/download](https://ngrok.com/download).
#    - Unzip the downloaded file and place `ngrok` in a directory included in your system's PATH, or specify the full path in the code.
#
# 2. **Sign Up for an ngrok Account:**
#    - Visit [ngrok.com/signup](https://ngrok.com/signup) to create a free account.
#    - After signing up, find your authtoken on your dashboard at [ngrok.com/dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
#
# 3. **Set Your ngrok Authtoken:**
#    - In the application GUI, enter your ngrok authtoken in the "Set Ngrok Token" field.
#    - Click the "Save Token" button to save it.
#
# 4. **Start the API Server:**
#    - Click the "Start API" button in the GUI.
#    - The application will launch the Uvicorn server locally and start ngrok to tunnel it.
#
# 5. **Access Your API Over the Internet:**
#    - Once started, the public URL provided by ngrok will be displayed in the application.
#    - Use this URL to access your API from anywhere over the internet.
#
# **Important Notes:**
#
# - **Security:** Exposing your local server over the internet can pose security risks. Ensure your API has proper authentication and security measures.
# - **Ngrok Limitations:** Free ngrok accounts have limitations on session durations and concurrent tunnels. Consider upgrading if necessary.
# - **Custom Domains:** For custom domains or subdomains, additional configuration and possibly a paid ngrok plan are required.
#
# **Why Use ngrok?**
#
# - **Quick Setup:** No need to configure routers or firewalls.
# - **Secure Tunnels:** Ngrok provides HTTPS tunnels to your local server.
# - **Ease of Use:** Suitable for development, testing, or sharing your work temporarily.
#
# **Alternative to ngrok:**
#
# If you have your own server or have configured port forwarding, you can directly expose your API without using ngrok. In that case, adjust the code to bind the server to the appropriate interface and port accessible over the internet.
#
# **Adjusting the Code for Direct Exposure:**
#
# - Modify the `start_uvicorn` method to bind to `0.0.0.0`:
#
# ```python
# def start_uvicorn(self):
#     self.uvicorn_process = subprocess.Popen(
#         [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#     )
# ```
#
# - Ensure your firewall allows incoming connections on the specified port.

