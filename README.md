# CS 122 Project: Amazon Product Analysis

## Authors
- Daniel Nguyen
- Nyi Htet

## Project Description
Amazon Product Analysis is an interactive desktop application designed to help users identify trending products and evaluate potential selling opportunities on Amazon. The application analyzes product and sales-related metrics across selected categories to help users make data-driven decisions about which products may be worth selling. Users will be able to filter between different product types and view price history. The goal of this project is to apply data analysis and visualization techniques to e-commerce product data, helping users better understand product trends and potential selling opportunities. The application will be built fully in Python.

## Project Outline/Plan
### Interface Plan
- **Frontend:** Python's Tkinter library
- **Pages:** Home screen and pop-up window for user input's & data visualizations
- **Widgets:** Search bars for specific items, drop-down for specific products, and buttons to interact with data and submit inputs.

### Data Collection and Storage Plan
- **Data Source:** Using [Rain Forest API](https://docs.trajectdata.com/rainforestapi/product-data-api/overview) to obtain real data From Amazon (top products, pricing, reviews, product details)
- **Storage Method:** Store API response in local `.csv` files to reduce future API calls and for data visualization.

### Data Analysis and Visualization Plan
#### Features
- **Product Analysis:** Explore product information across selected Amazon categories.
- **Trend Identification:** Analyze product metrics to identify potentially trending products.
- **Profitability Analysis:** Evaluate available pricing and sales metrics to assess potential selling opportunities.
- **Data Visualization:** Use charts to explore relationships and patterns in product data.

## Technologies
- **Python** — Data processing and analysis
- **Pandas** — Data manipulation
- **Numpy, Scipy, Seaborn** — Statistical data visualization
- **Matplotlib** — Chart rendering
- **Web Framework:** Tkinter for GUI
