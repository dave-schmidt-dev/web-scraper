"""
Generate interactive HTML viewer for optimized schedules.
"""

import json

INPUT_FILE = "optimized_schedules.json"
OUTPUT_FILE = "schedule_optimizer.html"

def generate_html():
    """Generate interactive HTML from JSON schedules."""
    
    # Load schedules
    with open(INPUT_FILE, 'r') as f:
        schedules = json.load(f)
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NVCC Schedule Optimizer - Spring 2026</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .summary h2 {
            margin-top: 0;
            color: #27ae60;
        }
        
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
        
        .schedule-card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;
        }
        
        .schedule-card.hidden {
            display: none;
        }
        
        .schedule-header {
            display: flex;
            justify-content: space-between;
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
            background: #3498db;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .gi-bill-info {
            background: #e8f5e9;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 3px solid #27ae60;
        }
        
        .gi-bill-info strong {
            color: #27ae60;
        }
        
        .class-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .class-table th {
            background: #ecf0f1;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .class-table td {
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .class-table tr:hover {
            background: #f8f9fa;
        }
        
        .gi-bill-class {
            background: #fff3cd !important;
            font-weight: bold;
        }
        
        .gi-bill-marker {
            color: #27ae60;
            font-size: 1.2em;
            margin-right: 5px;
        }
        
        .delivery-badge {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .delivery-online {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .delivery-inperson {
            background: #fff3e0;
            color: #f57c00;
        }
        
        .delivery-hybrid {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        
        .campus-tag {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>🎓 Spring 2026 Schedule Optimizer</h1>
    
    <div class="summary">
        <h2>✅ Optimization Complete</h2>
        <p><strong>Found:</strong> """ + str(len(schedules)) + """ valid schedules</p>
        <p><strong>Strategy:</strong> Maximize online courses (4 online) while maintaining GI Bill eligibility (1 in-person/hybrid)</p>
        <p><strong>Courses:</strong> ITD 256, ITN 101, ITN 170, ITN 213, ITN 254</p>
        <p><strong>Campus Priority:</strong> Manassas &gt; Woodbridge &gt; Annandale</p>
    </div>
    
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
    
    <div id="scheduleContainer">
"""
    
    # Generate schedule cards
    for i, schedule in enumerate(schedules[:20], 1):  # Top 20
        html += f"""
    <div class="schedule-card" data-campus="{next(c['location'] for c in schedule['classes'] if c['is_gi_bill_class'])}" data-course="{schedule['in_person_course']}">
        <div class="schedule-header">
            <div class="schedule-title">Option {i}</div>
            <div class="score-badge">Score: {schedule['score']}</div>
        </div>
        
        <div class="gi-bill-info">
            <strong>★ GI Bill Qualifying Class:</strong> {schedule['in_person_course']} 
            ({next(c['location'] for c in schedule['classes'] if c['is_gi_bill_class'])})
        </div>
        
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
        
        for cls in schedule['classes']:
            row_class = 'gi-bill-class' if cls['is_gi_bill_class'] else ''
            marker = '★ ' if cls['is_gi_bill_class'] else ''
            
            # Delivery badge class
            if 'Online' in cls['delivery']:
                badge_class = 'delivery-online'
            elif 'Hybrid' in cls['delivery']:
                badge_class = 'delivery-hybrid'
            else:
                badge_class = 'delivery-inperson'
            
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
        
        html += """
            </tbody>
        </table>
    </div>
"""
    
    html += """
    </div>
    
    <script>
        function filterSchedules() {
            const campusFilter = document.getElementById('campusFilter').value;
            const courseFilter = document.getElementById('courseFilter').value;
            const cards = document.querySelectorAll('.schedule-card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                const campus = card.dataset.campus;
                const course = card.dataset.course;
                
                const campusMatch = campusFilter === 'all' || campus === campusFilter;
                const courseMatch = courseFilter === 'all' || course === courseFilter;
                
                if (campusMatch && courseMatch) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });
            
            document.getElementById('resultCount').textContent = visibleCount;
        }
    </script>
</body>
</html>
"""
    
    return html

def main():
    """Generate and save HTML."""
    html = generate_html()
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    
    print(f"Generated {OUTPUT_FILE}")
    print("Open this file in your browser to explore schedule options!")

if __name__ == "__main__":
    main()
