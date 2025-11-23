import csv
import re
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "nvcc_spring_2026_schedule_data.csv"
OUTPUT_FILE = "schedule_view.html"

# Colors for different courses to make the calendar readable.
# Hex codes represent colors like Gold, Green, Blue, Pink, Orange, etc.
COLORS = [
    "#FFD700", "#ADFF2F", "#00BFFF", "#FF69B4", "#FFA500", "#9370DB", "#20B2AA", "#F08080"
]

def parse_time(time_str):
    """
    Parses a time string like '11:10A' into minutes from midnight.
    
    Example:
    - '08:00A' -> 480 minutes
    - '01:00P' -> 780 minutes
    
    Returns:
        int: Minutes from midnight, or None if parsing fails.
    """
    try:
        # %I = Hour (12-hour clock), %M = Minute, %p = AM/PM
        dt = datetime.strptime(time_str, "%I:%M%p")
        return dt.hour * 60 + dt.minute
    except ValueError:
        return None

def generate_html(courses):
    """
    Generates the complete HTML string for the schedule visualization.
    
    Args:
        courses (list): A list of dictionaries, where each dictionary is a course row from the CSV.
    """
    
    # ------------------------------------------
    # 1. HTML HEADER & CSS STYLES
    # ------------------------------------------
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NVCC Spring 2026 Schedule</title>
        <style>
            /* General Page Styles */
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f4f9; }
            h1 { text-align: center; color: #333; }
            .container { display: flex; flex-direction: column; gap: 20px; }
            
            /* Calendar Grid Container */
            .calendar { 
                display: grid; 
                /* 8 Columns: 1 for Time Labels + 7 for Days of the Week */
                grid-template-columns: 60px repeat(7, 1fr); 
                /* Rows will be generated dynamically based on hours */
                gap: 1px; 
                background-color: #ddd; /* Grey background creates the grid lines */
                border: 1px solid #ccc;
                height: 800px;
                overflow-y: auto; /* Scroll if the day is too long */
                position: relative;
            }
            
            /* Header Row (Days of Week) */
            .header { background-color: #fff; font-weight: bold; text-align: center; padding: 5px; position: sticky; top: 0; z-index: 10; }
            
            /* Time Label Column */
            .time-slot { background-color: #fff; text-align: right; padding-right: 5px; font-size: 12px; color: #666; }
            
            /* Empty Day Columns (Background) */
            .day-col { background-color: #fff; position: relative; }
            
            /* Event Block (The Class) */
            .event {
                position: absolute; /* Positioned relative to the grid container */
                width: 90%;         /* Slightly narrower than the column */
                left: 5%;           /* Center it */
                padding: 5px;
                border-radius: 5px;
                font-size: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                overflow: hidden;
                color: #333;
                border-left: 4px solid rgba(0,0,0,0.2); /* Accent border */
            }
            .event strong { display: block; font-size: 13px; margin-bottom: 2px; }
            
            /* Online Course List Styles */
            .online-section { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .online-section h2 { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
            .course-card { border: 1px solid #eee; padding: 10px; margin-bottom: 10px; border-radius: 5px; background-color: #fafafa; }
            .course-card strong { color: #0056b3; font-size: 1.1em; }
            
            /* Legend Styles */
            .legend { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 10px; }
            .legend-item { display: flex; align-items: center; gap: 5px; font-size: 14px; }
            .color-box { width: 15px; height: 15px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Spring 2026 Schedule</h1>
        
        <!-- Legend Section -->
        <div class="legend">
    """
    
    # ------------------------------------------
    # 2. GENERATE LEGEND
    # ------------------------------------------
    # Get unique course codes to assign consistent colors
    unique_courses = sorted(list(set(c['Course Code'] for c in courses)))
    course_colors = {code: COLORS[i % len(COLORS)] for i, code in enumerate(unique_courses)}
    
    for code in unique_courses:
        html += f"""
            <div class="legend-item">
                <div class="color-box" style="background-color: {course_colors[code]}"></div>
                <span>{code}</span>
            </div>
        """
    
    html += """
        </div>
        
        <div class="container">
            <div class="calendar">
                <!-- Grid Headers -->
                <div class="header">Time</div>
                <div class="header">Mon</div>
                <div class="header">Tue</div>
                <div class="header">Wed</div>
                <div class="header">Thu</div>
                <div class="header">Fri</div>
                <div class="header">Sat</div>
                <div class="header">Sun</div>
    """
    
    # ------------------------------------------
    # 3. BUILD CALENDAR GRID
    # ------------------------------------------
    # We create a grid from 8 AM to 10 PM.
    start_hour = 8
    end_hour = 22
    
    for h in range(start_hour, end_hour + 1):
        # Format time label (e.g., "8 AM", "12 PM")
        time_label = f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"
        
        # Add the time label in the first column
        html += f"""<div class="time-slot" style="grid-row: {h - start_hour + 2}">{time_label}</div>"""
        
        # Add empty background cells for each day (Mon-Sun)
        for _ in range(7):
             html += f"""<div class="day-col" style="grid-row: {h - start_hour + 2}; border-top: 1px dotted #eee;"></div>"""

    # ------------------------------------------
    # 4. PLACE EVENTS ON GRID
    # ------------------------------------------
    # Map day characters to grid column indices (1 is Time, so Mon is 2)
    day_map = {'M': 2, 'T': 3, 'W': 4, 'R': 5, 'F': 6, 'S': 7, 'U': 8}
    
    html_events = ""
    
    for course in courses:
        # Skip online courses or those without times (they go in the bottom list)
        if "Online" in course['Delivery Method'] or "Check Schedule" in course['Days/Time']:
            continue
            
        # Parse the "Days/Time" string: e.g., "MW 09:35A - 10:55A"
        dt_str = course['Days/Time']
        match = re.match(r"([MTWRFSU]+)\s+(\d{1,2}:\d{2}[AP])\s*-\s*(\d{1,2}:\d{2}[AP])", dt_str)
        
        if match:
            days = match.group(1)       # e.g., "MW"
            start_time_str = match.group(2) # e.g., "09:35A"
            end_time_str = match.group(3)   # e.g., "10:55A"
            
            start_min = parse_time(start_time_str)
            end_min = parse_time(end_time_str)
            
            if start_min and end_min:
                # Calculate vertical position (top) and height
                # We assume 1 hour = 60px height (1 minute = 1px)
                
                grid_start_min = start_hour * 60
                
                # Calculate offset from 8:00 AM
                offset = start_min - grid_start_min
                duration = end_min - start_min
                
                # Top position = Header Height (30px) + Offset
                top_px = 30 + offset 
                height_px = duration
                
                # Create an event block for each day the class meets
                for char in days:
                    col_idx = day_map.get(char)
                    if col_idx:
                        color = course_colors.get(course['Course Code'], "#ccc")
                        html_events += f"""
                        <div class="event" style="
                            grid-column: {col_idx}; 
                            grid-row: 1 / span 16; /* Span entire grid height, use top/height to position */
                            top: {top_px}px; 
                            height: {height_px}px; 
                            background-color: {color};
                            z-index: 20;
                        ">
                            <strong>{course['Course Code']}</strong>
                            {course['Section Number']}<br>
                            {start_time_str}-{end_time_str}<br>
                            {course['Location']}
                        </div>
                        """

    # Update CSS to ensure rows are exactly 60px high (1 px per minute)
    html = html.replace("repeat(16, 1fr)", f"repeat({end_hour-start_hour+1}, 60px)")
    
    html += html_events
    
    # ------------------------------------------
    # 5. ONLINE COURSES SECTION
    # ------------------------------------------
    html += """
            </div>
            
            <div class="online-section">
                <h2>Online / Asynchronous / TBA Courses</h2>
    """
    
    for course in courses:
        if "Online" in course['Delivery Method'] or "Check Schedule" in course['Days/Time']:
             color = course_colors.get(course['Course Code'], "#eee")
             html += f"""
                <div class="course-card" style="border-left: 5px solid {color}">
                    <strong>{course['Course Code']}</strong> - Section {course['Section Number']} <br>
                    Instructor: {course['Instructor']} <br>
                    Dates: {course['Start Date']} to {course['End Date']} <br>
                    Mode: {course['Delivery Method']}
                </div>
             """
             
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def main():
    """
    Main function to read CSV and write HTML.
    """
    courses = []
    # Read the CSV data
    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(row)
            
    # Generate the HTML content
    html_content = generate_html(courses)
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html_content)
    
    print(f"Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
