import os
import threading
from tkinter import filedialog
import customtkinter as ctk
import pandas as pd
from api_client import (
    CATEGORIES,
    CSV_PATH,
    fetch_all_daily_categories,
    fetch_category_bestsellers,
    load_products_csv,
    save_products_csv,
)


class DataOrganizationTab(ctk.CTkFrame):
    """
    Data Organization Tab with 3 pages:
      1. Extract CSV: Load and preview stored CSV products.
      2. Fetch Data: Fetch live bestsellers from Rainforest API.
      3. Display Products: Browse products by rank, category, or search.
    """

    PAGES = {
        "Extract CSV": "Load the raw CSV file here.",
        "Fetch Data": "Fetch the data from the API here.",
        "Display Products": "Show products with images and details here.",
    }

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.current_csv_path = CSV_PATH
        self.df = pd.DataFrame()

        # Layout: sidebar on column 0, content on column 1
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar, text="Menu", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Sidebar buttons
        self.buttons = {}
        self.pages = {}
        for row, (name, description) in enumerate(self.PAGES.items(), start=1):
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

        self.reload_csv_data()
        self.show_page("Extract CSV")

    def _build_page(self, title, description):
        if title == "Extract CSV":
            return self._build_extract_csv_page(title, description)
        elif title == "Fetch Data":
            return self._build_fetch_data_page(title, description)
        elif title == "Display Products":
            return self._build_display_products_page(title, description)

        page = ctk.CTkFrame(self.content)
        ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(page, text=description).pack(anchor="w", padx=20)
        return page

    # --- Page 1: Extract CSV ---
    def _build_extract_csv_page(self, title, description):
        page = ctk.CTkFrame(self.content)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 2))
        ctk.CTkLabel(page, text=description).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # File controls
        controls = ctk.CTkFrame(page)
        controls.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls, text="CSV File:").grid(row=0, column=0, padx=(10, 5), pady=10)
        self.csv_path_entry = ctk.CTkEntry(controls)
        self.csv_path_entry.insert(0, self.current_csv_path)
        self.csv_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10)

        browse_btn = ctk.CTkButton(controls, text="Browse...", width=80, command=self._on_browse_csv)
        browse_btn.grid(row=0, column=2, padx=5, pady=10)

        reload_btn = ctk.CTkButton(controls, text="Reload CSV", width=90, command=self.reload_csv_data)
        reload_btn.grid(row=0, column=3, padx=(5, 10), pady=10)

        # Summary box
        self.csv_preview_box = ctk.CTkTextbox(page, wrap="none")
        self.csv_preview_box.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 15))

        return page

    def _on_browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select Products CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if filename:
            self.current_csv_path = filename
            self.csv_path_entry.delete(0, "end")
            self.csv_path_entry.insert(0, filename)
            self.reload_csv_data()

    def reload_csv_data(self):
        target_path = self.csv_path_entry.get().strip() if hasattr(self, "csv_path_entry") else self.current_csv_path
        self.current_csv_path = target_path
        self.df = load_products_csv(target_path)

        if hasattr(self, "csv_preview_box"):
            self.csv_preview_box.delete("1.0", "end")
            if self.df.empty:
                self.csv_preview_box.insert("end", f"No products found in {target_path}.\nFetch data using the 'Fetch Data' tab.")
            else:
                self.csv_preview_box.insert("end", f"Total Records: {len(self.df)}\n")
                self.csv_preview_box.insert("end", f"Categories: {list(self.df['category'].unique())}\n\n")
                preview_cols = ["rank", "category", "title", "price_raw", "rating", "ratings_total", "asin"]
                cols_to_show = [c for c in preview_cols if c in self.df.columns]
                self.csv_preview_box.insert("end", self.df[cols_to_show].head(30).to_string(index=False))

        if hasattr(self, "display_scroll_frame"):
            self._render_products()

    # --- Page 2: Fetch Data ---
    def _build_fetch_data_page(self, title, description):
        page = ctk.CTkFrame(self.content)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 2))
        ctk.CTkLabel(page, text=description).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        controls = ctk.CTkFrame(page)
        controls.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls, text="Category:").grid(row=0, column=0, padx=10, pady=10)

        options = [
            "All Categories (3 API Credits)",
            "Appliances",
            "Electronics",
            "Home & Kitchen",
        ]
        self.category_dropdown = ctk.CTkOptionMenu(controls, values=options)
        self.category_dropdown.set(options[0])
        self.category_dropdown.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        self.fetch_btn = ctk.CTkButton(controls, text="Fetch Bestsellers", command=self._start_fetch_thread)
        self.fetch_btn.grid(row=0, column=2, padx=10, pady=10)

        # Log box
        log_frame = ctk.CTkFrame(page)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 15))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(log_frame, wrap="word")
        self.log_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.log_textbox.insert("end", "Ready. Click 'Fetch Bestsellers' to gather data from Rainforest API.\n")

        return page

    def _log(self, text):
        if hasattr(self, "log_textbox"):
            self.log_textbox.insert("end", f"{text}\n")
            self.log_textbox.see("end")

    def _start_fetch_thread(self):
        # Run API calls in background thread so the GUI does not freeze
        self.fetch_btn.configure(state="disabled", text="Fetching...")
        threading.Thread(target=self._run_fetch, daemon=True).start()

    def _run_fetch(self):
        choice = self.category_dropdown.get()
        try:
            if "All Categories" in choice:
                self._log("Fetching all 3 categories (Appliances, Electronics, Home & Kitchen)...")
                fetch_all_daily_categories()
            else:
                cat_map = {"Appliances": "appliances", "Electronics": "electronics", "Home & Kitchen": "home-garden"}
                slug = cat_map.get(choice, "appliances")
                self._log(f"Fetching '{choice}'...")
                df = fetch_category_bestsellers(slug)
                save_products_csv(df, self.current_csv_path)
                self._log(f"Retrieved and saved {len(df)} items.")

            self._log("Finished! Saved to CSV.")
            self.after(100, self.reload_csv_data)
        except Exception as e:
            self._log(f"Error: {e}")
        finally:
            self.fetch_btn.configure(state="normal", text="Fetch Bestsellers")

    # --- Page 3: Display Products ---
    def _build_display_products_page(self, title, description):
        page = ctk.CTkFrame(self.content)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 2))

        # Filter bar
        filter_bar = ctk.CTkFrame(page)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        filter_bar.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(filter_bar, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.cat_filter = ctk.CTkOptionMenu(
            filter_bar,
            values=["All", "Appliances", "Electronics", "Home & Kitchen"],
            command=lambda _: self._render_products(),
        )
        self.cat_filter.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(filter_bar, text="Search:").grid(row=0, column=2, padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="Search title or ASIN...")
        self.search_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        search_btn = ctk.CTkButton(filter_bar, text="Filter", width=60, command=self._render_products)
        search_btn.grid(row=0, column=4, padx=5, pady=5)

        self.display_scroll_frame = ctk.CTkScrollableFrame(page)
        self.display_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        return page

    def _render_products(self):
        if not hasattr(self, "display_scroll_frame"):
            return

        for w in self.display_scroll_frame.winfo_children():
            w.destroy()

        if self.df.empty:
            ctk.CTkLabel(self.display_scroll_frame, text="No products found. Go to 'Fetch Data' to gather products.").pack(pady=20)
            return

        data = self.df.copy()
        cat = self.cat_filter.get()
        if cat != "All":
            data = data[data["category"].astype(str) == cat]

        query = self.search_entry.get().strip().lower()
        if query:
            match = data["title"].astype(str).str.lower().str.contains(query, na=False) | data["asin"].astype(str).str.lower().str.contains(query, na=False)
            data = data[match]

        for _, row in data.head(40).iterrows():
            card = ctk.CTkFrame(self.display_scroll_frame)
            card.pack(fill="x", padx=5, pady=3, expand=True)

            rank = f"#{int(row['rank'])}" if pd.notna(row.get("rank")) else "#-"
            title = str(row.get("title", ""))[:65]
            price = str(row.get("price_raw", "")) or "N/A"
            rating = f"★ {row['rating']}" if pd.notna(row.get("rating")) else ""
            cat_name = str(row.get("category", ""))

            line = f"{rank:5} | {title} | {price} | {rating} | {cat_name}"
            ctk.CTkLabel(card, text=line, anchor="w").pack(side="left", padx=10, pady=6)

    def show_page(self, name):
        for page_name, page in self.pages.items():
            page.grid_forget()
            self.buttons[page_name].configure(fg_color="transparent")

        self.pages[name].grid(row=0, column=0, sticky="nsew")
        self.buttons[name].configure(fg_color=("gray75", "gray25"))
