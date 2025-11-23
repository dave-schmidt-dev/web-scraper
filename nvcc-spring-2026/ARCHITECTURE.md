# Project Architecture & Logic Flow

This document explains **how** the NVCC Schedule Scraper works at a high level. It is designed to help you understand the "big picture" before diving into the code.

## 🏗️ High-Level Design

The project is split into three main phases:

1. **Data Collection (Scraping)**: Getting the raw information from the internet.
2. **Data Visualization**: Turning that raw information into something easy to read.
3. **Schedule Optimization**: Finding the best course combinations based on your requirements.

### The "Pipeline"

Think of this as a factory assembly line:

1. **Input**: A list of course names (e.g., "ITN 260").
2. **Step 1 (Scraper)**: A "robot" (Selenium) goes to the website, looks up each course, and writes down the details.
3. **Storage (CSV)**: The robot saves its notes into a spreadsheet (CSV file).
4. **Step 2 (Visualizer)**: A "designer" (Python script) reads the spreadsheet and draws a calendar.
5. **Step 3 (Optimizer)**: An "advisor" (Python script) analyzes all combinations to find the best schedule.
6. **Output**: Interactive HTML files you can view in your browser.

---

## 🧩 Component Breakdown

### 1. The Scraper (`scrape_nvcc.py`)

**Goal**: Mimic a human browsing the NVCC website to get course data.

* **Why Selenium?**
  * The NVCC website is "dynamic," meaning it uses JavaScript to load data. Standard tools like `requests` (which just download a file) can't see this data.
  * Selenium launches a real Google Chrome browser (hidden in the background) so it can click buttons and wait for things to load, just like you would.

* **Logic Flow**:
    1. **Setup**: Open the hidden browser.
    2. **Loop**: For each subject (ITN, ITD):
        * Go to the search page.
        * **Wait**: Don't do anything until the "Course" headers appear.
        * **Read**: Grab the HTML (the code behind the web page).
        * **Parse**: Use `BeautifulSoup` (a library) to find the text we care about.
        * **Extract**: Use `Regex` (pattern matching) to pull out specific bits like "11:10A" or "Room 302".
        * **Paginate**: If there's a "Next" button, click it and repeat.
    3. **Save**: Write everything to `nvcc_spring_2026_schedule_data.csv`.

### 2. The Visualizer (`visualize_schedule.py`)

**Goal**: Turn the CSV data into a visual weekly calendar.

* **Logic Flow**:
    1. **Read**: Open the CSV file and load the rows.
    2. **Filter**: Ignore online courses for the grid (since they don't have a specific "time").
    3. **Calculate**:
        * Convert times (e.g., "9:00 AM") into "minutes from midnight" (e.g., 540 minutes).
        * This lets us do math: `End Time - Start Time = Height of the block`.
    4. **Draw (Generate HTML)**:
        * Create a grid where 1 minute = 1 pixel (or similar ratio).
        * Place colored blocks on the grid using CSS absolute positioning (`top` and `height`).
    5. **List Online**: Append a separate list at the bottom for online classes.

### 3. The Optimizer (`optimize_schedule.py`)

**Goal**: Find the best course combinations that meet your requirements.

* **Logic Flow**:
    1. **Read**: Load all course sections from the CSV.
    2. **Categorize**: Split into in-person/hybrid vs. online courses.
    3. **Generate Combinations**: Create all possible schedules (cartesian product).
    4. **Score Each**:
        * +200 points: Exactly 1 in-person class (GI Bill requirement)
        * +100 points: In-person class at Manassas (closest campus)
        * +50/+30/+10: Other preferred campuses
        * +5 points: Online Asynchronous vs Virtual Real-Time
        * -500 points: Schedule conflicts (overlapping times)
    5. **Sort**: Rank all valid schedules by score.
    6. **Save**: Export top 20 to JSON.

* **Conflict Detection**:
  * Parse days (M, T, W, R, F, S, U) and times.
  * Check if two classes share any days.
  * Check if time ranges overlap.

---

## 📂 File Structure

* `scrape_nvcc.py`: The worker script. Runs the browser.
* `visualize_schedule.py`: The artist script. Draws the calendar.
* `optimize_schedule.py`: The advisor script. Finds best schedules.
* `generate_optimizer_html.py`: Creates interactive schedule explorer.
* `nvcc_spring_2026_schedule_data.csv`: The bridge. Holds data between components.
* `schedule_view.html`: Visual calendar output.
* `schedule_optimizer.html`: Interactive schedule comparison tool.
* `optimized_schedules.json`: Top schedule combinations.

## 🧠 Key Concepts for Beginners

* **DOM (Document Object Model)**: The tree structure of HTML tags that makes up a webpage. We "traverse" this tree to find data.
* **Headless Browser**: A web browser without a graphical user interface. It runs faster and is perfect for bots.
* **Regex (Regular Expressions)**: A special language for finding patterns in text (like finding a phone number or a time format).
