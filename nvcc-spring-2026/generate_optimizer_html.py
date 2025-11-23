"""
Interactive HTML Generator for Optimized Schedules

This script takes the JSON output from optimize_schedule.py and creates
a beautiful, interactive HTML page where you can:
1. View the top 20 schedules
2. Filter by campus or course
3. See which class is the GI Bill qualifying class
4. Easily find Class Numbers for registration
"""

import json

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "optimized_schedules.json"
OUTPUT_FILE = "schedule_optimizer.html"

def generate_html():
    """
    Generate the complete HTML page from the JSON schedules.
    
    This function:
    1. Loads the optimized schedules from JSON
    2. Builds an HTML page with CSS styling
    3. Creates interactive schedule cards
    4. Adds JavaScript for filtering
    
    Returns:
        str: Complete HTML document as a string
    """
    
    # Load the schedules from the JSON file created by optimize_schedule.py
    with open(INPUT_FILE, 'r') as f:
        schedules = json.load(f)
    
    # Start building the HTML document
    # We use triple-quoted strings to write multi-line HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NVCC Schedule Optimizer - Spring 2026</title>
    <style>
        /* ===== GENERAL PAGE STYLING ===== */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;  /* Don't make it too wide */
            margin: 0 auto;     /* Center the content */
            padding: 20px;
            background-color: #f5f5f5;  /* Light gray background */
        }
        
        h1 {
            color: #2c3e50;  /* Dark blue-gray */
            text-align: center;
        }
        
        /* ===== SUMMARY BOX (at the top) ===== */
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;  /* Rounded corners */
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);  /* Subtle shadow */
        }
        
        .summary h2 {
            margin-top: 0;
            color: #27ae60;  /* Green for success */
        }
        
        /* ===== FILTER CONTROLS ===== */
        .filters {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .filter-group {
            margin-bottom: 10px;
        }
        
        .filter-group label {
            font-weight: bold;
            margin-right: 10px;
        }
        
        select {
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        /* ===== SCHEDULE CARD STYLING ===== */
        .schedule-card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;  /* Blue accent bar */
        }
        
        /* Hidden class for filtering */
        .schedule-card.hidden {
            display: none;
        }
        
        .schedule-header {
            display: flex;
            justify-content: space-between;  /* Push title and score apart */
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .schedule-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .score-badge {
            background: #3498db;  /* Blue */
            color: white;
            padding: 5px 15px;
            border-radius: 20px;  /* Pill shape */
            font-weight: bold;
        }
        
        /* ===== GI BILL INFO BOX ===== */
        /* This highlights which class qualifies for GI Bill */
        .gi-bill-info {
            background: #e8f5e9;  /* Light green */
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 3px solid #27ae60;  /* Green accent */
        }
        
        .gi-bill-info strong {
            color: #27ae60;
        }
        
        /* ===== TABLE STYLING ===== */
        .class-table {
            width: 100%;
            border-collapse: collapse;  /* No gaps between cells */
        }
        
        .class-table th {
            background: #ecf0f1;  /* Light gray */
            padding: 10px;
            text-align: left;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .class-table td {
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        /* Hover effect on table rows */
        .class-table tr:hover {
            background: #f8f9fa;
        }
        
        /* Highlight the GI Bill qualifying class */
        .gi-bill-class {
            background: #fff3cd !important;  /* Yellow highlight */
            font-weight: bold;
        }
        
        .gi-bill-marker {
            color: #27ae60;
            font-size: 1.2em;
            margin-right: 5px;
        }
        
        /* ===== DELIVERY METHOD BADGES ===== */
        .delivery-badge {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        /* Color-code delivery methods */
        .delivery-online {
            background: #e3f2fd;  /* Light blue */
            color: #1976d2;       /* Dark blue text */
        }
        
        .delivery-inperson {
            background: #fff3e0;  /* Light orange */
            color: #f57c00;       /* Dark orange text */
        }
        
        .delivery-hybrid {
            background: #f3e5f5;  /* Light purple */
            color: #7b1fa2;       /* Dark purple text */
        }
        
        /* ===== CAMPUS TAG ===== */
        .campus-tag {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>🎓 Spring 2026 Schedule Optimizer</h1>
    
    <!-- SUMMARY SECTION -->
    <div class="summary">
        <h2>✅ Optimization Complete</h2>
        <p><strong>Found:</strong> """ + str(len(schedules)) + """ valid schedules</p>
        <p><strong>Strategy:</strong> Maximize online courses (4 online) while maintaining GI Bill eligibility (1 in-person/hybrid)</p>
        <p><strong>Courses:</strong> ITD 256, ITN 101, ITN 170, ITN 213, ITN 254</p>
        <p><strong>Campus Priority:</strong> Manassas &gt; Woodbridge &gt; Annandale</p>
    </div>
    
    <!-- FILTER CONTROLS -->
    <div class="filters">
        <div class="filter-group">
            <label for="campusFilter">Filter by GI Bill Campus:</label>
            <select id="campusFilter" onchange="filterSchedules()">
                <option value="all">All Campuses</option>
                <option value="Manassas">Manassas Only</option>
                <option value="Woodbridge">Woodbridge Only</option>
                <option value="Annandale">Annandale Only</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label for="courseFilter">Filter by GI Bill Course:</label>
            <select id="courseFilter" onchange="filterSchedules()">
                <option value="all">All Courses</option>
                <option value="ITN 101">ITN 101</option>
                <option value="ITN 170">ITN 170</option>
                <option value="ITD 256">ITD 256</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Showing: <span id="resultCount">""" + str(min(20, len(schedules))) + """</span> schedules</label>
        </div>
    </div>
    
    <!-- SCHEDULE CARDS CONTAINER -->
    <div id="scheduleContainer">
"""
    
    # ==========================================
    # GENERATE SCHEDULE CARDS
    # ==========================================
    # Loop through the top 20 schedules and create a card for each
    for i, schedule in enumerate(schedules[:20], 1):
        # Find which class is the GI Bill class for data attributes
        gi_bill_location = next(c['location'] for c in schedule['classes'] if c['is_gi_bill_class'])
        
        html += f"""
    <!-- SCHEDULE CARD {i} -->
    <div class="schedule-card" data-campus="{gi_bill_location}" data-course="{schedule['in_person_course']}">
        <!-- Card Header with Title and Score -->
        <div class="schedule-header">
            <div class="schedule-title">Option {i}</div>
            <div class="score-badge">Score: {schedule['score']}</div>
        </div>
        
        <!-- GI Bill Info Box -->
        <div class="gi-bill-info">
            <strong>★ GI Bill Qualifying Class:</strong> {schedule['in_person_course']} 
            ({gi_bill_location})
        </div>
        
        <!-- Course Table -->
        <table class="class-table">
            <thead>
                <tr>
                    <th>Course</th>
                    <th>Class #</th>
                    <th>Section</th>
                    <th>Instructor</th>
                    <th>Schedule</th>
                    <th>Location</th>
                    <th>Delivery</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Loop through each class in this schedule
        for cls in schedule['classes']:
            # Highlight the GI Bill class
            row_class = 'gi-bill-class' if cls['is_gi_bill_class'] else ''
            marker = '★ ' if cls['is_gi_bill_class'] else ''
            
            # Determine badge color based on delivery method
            if 'Online' in cls['delivery']:
                badge_class = 'delivery-online'
            elif 'Hybrid' in cls['delivery']:
                badge_class = 'delivery-hybrid'
            else:
                badge_class = 'delivery-inperson'
            
            # Add a table row for this class
            html += f"""
                <tr class="{row_class}">
                    <td><span class="gi-bill-marker">{marker}</span>{cls['course']}</td>
                    <td><strong>{cls['class_number']}</strong></td>
                    <td>{cls['section']}</td>
                    <td>{cls['instructor']}</td>
                    <td>{cls['days_time']}</td>
                    <td><span class="campus-tag">{cls['location']}</span></td>
                    <td><span class="delivery-badge {badge_class}">{cls['delivery']}</span></td>
                </tr>
"""
        
        # Close the table and card
        html += """
            </tbody>
        </table>
    </div>
"""
    
    # ==========================================
    # JAVASCRIPT FOR FILTERING
    # ==========================================
    # This code runs in the browser to hide/show cards based on filters
    html += """
    </div>
    
    <script>
        /**
         * Filter schedules based on dropdown selections.
         * 
         * This function:
         * 1. Gets the current filter values from the dropdowns
         * 2. Loops through all schedule cards
         * 3. Hides cards that don't match the filters
         * 4. Updates the count of visible schedules
         */
        function filterSchedules() {
            // Get current filter values
            const campusFilter = document.getElementById('campusFilter').value;
            const courseFilter = document.getElementById('courseFilter').value;
            const cards = document.querySelectorAll('.schedule-card');
            let visibleCount = 0;
            
            // Check each card
            cards.forEach(card => {
                // Get the card's data attributes
                const campus = card.dataset.campus;
                const course = card.dataset.course;
                
                // Check if this card matches the filters
                const campusMatch = campusFilter === 'all' || campus === campusFilter;
                const courseMatch = courseFilter === 'all' || course === courseFilter;
                
                // Show or hide the card
                if (campusMatch && courseMatch) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });
            
            // Update the count display
            document.getElementById('resultCount').textContent = visibleCount;
        }
    </script>
</body>
</html>
"""
    
    return html

def main():
    """
    Main function: Generate the HTML and save it to a file.
    
    This is the entry point when you run the script.
    """
    html = generate_html()
    
    # Write the HTML string to a file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    
    print(f"Generated {OUTPUT_FILE}")
    print("Open this file in your browser to explore schedule options!")

if __name__ == "__main__":
    main()
