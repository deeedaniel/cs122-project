import os

import customtkinter as ctk
from PIL import Image


class DataAnalysisTab(ctk.CTkFrame):
    """Left sidebar menu + a content area that swaps between three pages."""

    PAGES = {
        "Price and Quantity": "Relationship between price and quantity",
        "Price over two weeks": "Fetch the data from the API here.",
        "Profitable Categories": "Show products with images and details here.",
    }

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # Column 0 = sidebar (fixed), column 1 = content (takes the rest)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------- sidebar ----------
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar, text="Menu", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # ---------- content area ----------
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # ---------- one button + one page per menu item ----------
        self.buttons = {}
        self.pages = {}
        for row, (name, description) in enumerate(self.PAGES.items(), start=1):
            # name=name freezes the current value; without it every button
            # would open the LAST page (a classic lambda-in-a-loop bug)
            button = ctk.CTkButton(
                self.sidebar,
                text=name,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda name=name: self.show_page(name),
            )
            button.grid(row=row, column=0, padx=20, pady=10)
            self.buttons[name] = button

            self.pages[name] = self._build_page(name, description)

        self.show_page("Price and Quantity")  # page shown on startup

    def _build_page(self, title, description):
        """Create one page frame. Put each page's real widgets in here."""
        page = ctk.CTkFrame(self.content)
        ctk.CTkLabel(
            page, text=title, font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(page, text=description).pack(anchor="w", padx=20)
        return page

    def show_page(self, name):
        for page_name, page in self.pages.items():
            page.grid_forget()  # hide every page
            self.buttons[page_name].configure(fg_color="transparent")

        self.pages[name].grid(row=0, column=0, sticky="nsew")  # show the chosen one
        self.buttons[name].configure(fg_color=("gray75", "gray25"))  # highlight it