# NVCC Schedule Scraper & Visualizer

A Python-based toolset designed to scrape course schedule data from the Northern Virginia Community College (NVCC) website and visualize it in an interactive HTML calendar.

## 🚀 Features

* **Robust Scraping**: Uses **Selenium** and **Headless Chrome** to handle dynamic content, pagination, and JavaScript-driven search results on the NVCC schedule site.
* **Data Extraction**: Parses unstructured course details (Section, Instructor, Time, Location, Delivery Method) using regular expressions.
* **CSV Export**: Saves clean, structured data to a CSV file for analysis.
* **Visualization**: Generates a responsive **HTML Calendar** view to easily visualize weekly class blocks and online course timelines.
* **Schedule Optimizer**: Intelligent course selection tool that finds optimal schedule combinations based on GI Bill requirements, campus preferences, and conflict detection.
* **Educational Code**: The source code is heavily commented to serve as a learning resource for beginners interested in web scraping and automation.
* **Architecture Guide**: See [ARCHITECTURE.md](ARCHITECTURE.md) for a high-level explanation of how the system works.

## 🛠️ Technologies

* **Python 3.x**
* **Selenium WebDriver**: For browser automation.
* **BeautifulSoup4**: For HTML parsing.
* **HTML/CSS**: For the schedule visualization.

## 📦 Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/nvcc-schedule-scraper.git
    cd nvcc-schedule-scraper
    ```

2. **Set up a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:

    ```bash
    pip install selenium webdriver-manager beautifulsoup4
    ```

## 📖 Usage

### 1. Scrape the Schedule

Run the scraper script to fetch the latest data. You can modify the `TARGET_COURSES` list in `scrape_nvcc.py` to search for different classes.

```bash
python scrape_nvcc.py
```

*Output*: `nvcc_spring_2026_schedule_data.csv`

### 2. Visualize the Data

Generate an HTML calendar view from the scraped CSV data.

```bash
python visualize_schedule.py
```

*Output*: `schedule_view.html`

### 3. View Results

Open `schedule_view.html` in your web browser to see your color-coded weekly schedule.

### 4. Optimize Your Schedule (Optional)

Find the best course combinations that maximize online enrollment while maintaining GI Bill BAH eligibility.

```bash
python optimize_schedule.py
python generate_optimizer_html.py
```

*Outputs*:

* `optimized_schedules.json` - Top 20 schedule combinations
* `schedule_optimizer.html` - Interactive tool to explore options

The optimizer:

* Ensures at least 1 in-person/hybrid class for GI Bill requirements
* Maximizes online courses for convenience
* Prioritizes preferred campuses
* Detects and avoids time conflicts
* Displays **Class Numbers** for easy registration

## ⚠️ Disclaimer

This tool is for educational purposes and personal use to assist with schedule planning. It is not affiliated with or endorsed by Northern Virginia Community College.
