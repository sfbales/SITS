# about.py
import tkinter as tk
from tkinter import ttk 
import webbrowser
import os

class About:
    def __init__(self, parent_notebook):
        self.parent_notebook = parent_notebook
        self.tab = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.tab, text="About")
        self.create_widgets()

    def create_widgets(self):
        """Create UI elements for the About tab."""
        
        # Configure the grid to have a single column that expands
        self.tab.columnconfigure(0, weight=1)
        
        # Main information labels centered
        ttk.Label(
            self.tab, 
            text="SITS - Snake In The Shell", 
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, padx=10, pady=(20, 10))
        
        ttk.Label(self.tab, text="Version: 1.0").grid(row=1, column=0, padx=10, pady=5)
        ttk.Label(
            self.tab, 
            text="Author: Salvatore Francesco Balestrieri - Email: balestrierisf@gmail.com"
        ).grid(row=2, column=0, padx=10, pady=5)
        ttk.Label(
            self.tab, 
            text="A suite to simplify the management of Python-based software. If you like my project consider making a donation. If you want to make a donation using a different method contact me directly via email. Thank you for your support", 
            wraplength=400, 
            justify="center"
        ).grid(row=3, column=0, padx=20, pady=10)
        
        # Donate button centered
        donate_button = ttk.Button(
            self.tab, 
            text="Donate with PayPal", 
            command=self.open_donation_link
        )
        donate_button.grid(row=4, column=0, pady=20)

    def open_donation_link(self):
        """Open a web link to the donation page."""
        url = "https://www.paypal.me/truetomyname"
        webbrowser.open(url)

def about(parent_notebook):
    """Initializes the About module and returns the tab for integration into the main application."""
    try:
        module = About(parent_notebook)
        return module.tab
    except Exception as e:
        print(f"Failed to initialize About: {e}")
        return None

