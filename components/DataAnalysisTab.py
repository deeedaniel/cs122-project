import os

import customtkinter as ctk
from PIL import Image
import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
class DataAnalysisTab(ctk.CTkFrame):
    """Left sidebar menu + a content area that swaps between three pages."""

    PAGES = {
        "Unique Products": "Do number of unique products in each category", 
        "Price Distribution over Categories": "Fetch the data from the API here.",
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

        self.show_page("Unique Products")  # page shown on startup

    def _build_page(self, title, description):
        """Create one page frame. Put each page's real widgets in here."""
        
        # page 1
        if title == "Unique Products": 
            return self._build_unique_products(title, description)
        elif title == "Price Distribution over Categories":
            return self._build_price_distribution(title, description)
        
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
        
    def _build_unique_products(self, title, description):
        page = ctk.CTkFrame(self.content)
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)
        df = pd.read_csv("./data/amazon_products.csv")
        print(df.nunique().to_string())
        
        ctk.CTkLabel(
            page, text=title, font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 2))

        ctk.CTkLabel(page, text=description).grid(
            row=1, column=0, sticky="w", padx=20
        )
        
        # count of products in each categories
        counts = (
            df.groupby("category")["asin"]
                .nunique()
                .sort_values(ascending=False)
        )
                
        print(counts)
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        sns.barplot(x=counts.values, y=counts.index, color="orange", ax=ax)
        ax.set_xlabel("Unique products")
        ax.set_ylabel("Category")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=page)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=2, column=0, sticky="nsew", padx=20, pady=10
        )
        
        price_df = pd.read_csv("./data/keepa_history.csv")
        print(price_df.head())
        return page
    
    def _build_price_distribution(self, title, description):
        page = ctk.CTkFrame(self.content)
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)
        df = pd.read_csv("./data/amazon_products.csv")
        # Distribution of prices over each category
        for value in df["category"].unique():
            category_df = df[df["category"] == value]
            
            # only take the unique products with the latest captured_at timestamp and non-null price
            unique_products = (
                category_df
                .dropna(subset=["price"])
                .sort_values("captured_at")
                .drop_duplicates(subset=["asin"], keep="last")
            )
            print(f"Category: {value}, Count: {len(unique_products)}")
            print(unique_products["price"].describe())
            
            # plt.figure(figsize=(10, 6))
            # sns.catplot(
            #             data = unique_products,
            #             x = "price_raw",
            #             y = "title", 
            #             aspect = 2,
            #             kind = "box",
            #             height = 10, 
            #             hue = "title"
            #         )
            
            # plt.title(f"Price distribution for category: {value}")
        df["captured_at"] = pd.to_datetime(
            df["captured_at"], utc=True, errors="coerce"
        )
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

        price_data = (
            df.dropna(subset=["category", "asin", "price", "captured_at"])
            .sort_values("captured_at")
            .drop_duplicates(subset=["category", "asin"], keep="last")
        )

        price_fig = Figure(figsize=(7, 4), dpi=100)
        price_ax = price_fig.add_subplot(111)

        sns.boxplot(
            data=price_data,
            x="price",
            y="category",
            color="orange",
            ax=price_ax,
        )
        
        price_ax.set_xlim(0, 200)  # limit x-axis to 95th percentile
        price_ax.set_xlabel("Price ($)")
        price_ax.set_ylabel("Category")
        price_ax.set_title("Product price distribution by category")
        price_fig.tight_layout()

        price_canvas = FigureCanvasTkAgg(price_fig, master=page)
        price_canvas.draw()
        price_canvas.get_tk_widget().grid(
            row=3, column=0, sticky="nsew", padx=20, pady=10
        )
        
        return page