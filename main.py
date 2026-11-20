# GUI to display the data organization and data analysis results

import csv, json, os, threading

# threading for reducing time taken to load data and perform analysis
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog
from components.DataOrganizationTab import DataOrganizationTab
from components.DataAnalysisTab import DataAnalysisTab
from PIL import Image
import customtkinter as ctk
import pandas as pd
import requests


if __name__ == "__main__":
    # Create the main window
    ctk.set_appearance_mode("light")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default
    app = ctk.CTk()
    app.title("Amazon Products Analysis")
    app.geometry("800x600")

    # Image above the tabs
    logo = Image.open("sample_response.png")
    logo_image = ctk.CTkImage(light_image=logo, dark_image=logo, size=(60, 60))
    logo_label = ctk.CTkLabel(app, image=logo_image, text="")
    logo_label.pack(pady=(10, 0))   # packed first, so it sits above the tabs
    
    tabs = ctk.CTkTabview(app)
    #tabs.grid(row=0, column=0, sticky="nsew")
    tabs.pack(expand=True, fill="both")
    data_organization_tab = tabs.add("Data Organization")
    data_analysis_tab = tabs.add("Products Analysis")
    
    DataOrganizationTab(data_organization_tab).pack(expand=True, fill="both")
    DataAnalysisTab(data_analysis_tab).pack(expand=True, fill="both")
    # Start the GUI event loop
    app.mainloop()