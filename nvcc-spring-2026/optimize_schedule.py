"""
Course Schedule Optimizer

This script finds the best combination of classes to maximize online enrollment
while maintaining GI Bill BAH eligibility (at least 1 in-person/hybrid class).

The optimizer:
1. Reads all course sections from the CSV
2. Generates all possible schedule combinations
3. Scores each combination based on preferences
4. Outputs the top 20 schedules to JSON
"""

import csv
import re
from datetime import datetime
from itertools import product
import json

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "nvcc_spring_2026_schedule_data.csv"
OUTPUT_FILE = "optimized_schedules.json"

# Required courses (exclude ITN 260 per user request)
REQUIRED_COURSES = [
    "ITD 256",
    "ITN 101",
    "ITN 170",
    "ITN 213",
    "ITN 254"
]

# Campus preferences (higher score = better)
# User is driving from Haymarket, so closer campuses score higher
CAMPUS_SCORES = {
    "Manassas": 100,      # Closest
    "Woodbridge": 50,     # Moderate distance
    "Annandale": 30,      # Further
    "Alexandria": 10,     # Far
    "Loudoun": 5,         # Far
    "Reston Center": 5,   # Far
    "NOVA Online": 0      # No commute
}

def parse_time_to_minutes(time_str):
    """
    Convert time string like '11:10A' to minutes from midnight.
    
    This makes it easy to do math with times. For example:
    - '08:00A' = 8*60 = 480 minutes
    - '01:00P' = 13*60 = 780 minutes
    
    Args:
        time_str: Time in format like "11:10A" or "02:30P"
    
    Returns:
        int: Minutes from midnight, or None if parsing fails
    """
    try:
        # %I = Hour (12-hour), %M = Minute, %p = AM/PM
        dt = datetime.strptime(time_str, "%I:%M%p")
        return dt.hour * 60 + dt.minute
    except (ValueError, AttributeError):
        return None

def parse_days_time(days_time_str):
    """
    Parse the "Days/Time" field into structured data.
    
    Example input: "MW 09:35A - 10:55A"
    Example output: {
        "days": "MW",
        "start_time": "09:35A",
        "end_time": "10:55A",
        "start_min": 575,
        "end_min": 655
    }
    
    Args:
        days_time_str: String like "MW 09:35A - 10:55A"
    
    Returns:
        dict or None: Parsed schedule info, or None if online/no schedule
    """
    # Regex pattern to match: Days (M/T/W/R/F/S/U) + Time range
    match = re.match(r"([MTWRFSU]+)\s+(\d{1,2}:\d{2}[AP])\s*-\s*(\d{1,2}:\d{2}[AP])", days_time_str)
    
    if match:
        return {
            "days": match.group(1),           # e.g., "MW"
            "start_time": match.group(2),     # e.g., "09:35A"
            "end_time": match.group(3),       # e.g., "10:55A"
            "start_min": parse_time_to_minutes(match.group(2)),
            "end_min": parse_time_to_minutes(match.group(3))
        }
    return None

def check_conflict(section1, section2):
    """
    Check if two course sections have a time conflict.
    
    Two classes conflict if they:
    1. Share at least one day (e.g., both meet on Monday)
    2. Have overlapping times
    
    Example conflict:
    - Class A: MW 10:00A - 11:20A
    - Class B: M 11:00A - 12:20P
    - They both meet Monday, and 11:00-11:20 overlaps
    
    Args:
        section1: First section dictionary with "schedule" field
        section2: Second section dictionary with "schedule" field
    
    Returns:
        bool: True if they conflict, False otherwise
    """
    # Online courses never conflict (no fixed meeting time)
    if not section1["schedule"] or not section2["schedule"]:
        return False
    
    s1 = section1["schedule"]
    s2 = section2["schedule"]
    
    # Check if they share any days
    # Convert days string to a set: "MW" -> {'M', 'W'}
    days1 = set(s1["days"])
    days2 = set(s2["days"])
    
    if not days1.intersection(days2):
        return False  # No shared days = no conflict
    
    # Check time overlap
    # Two time ranges overlap if: start1 < end2 AND start2 < end1
    if s1["start_min"] is None or s2["start_min"] is None:
        return False
    
    return (s1["start_min"] < s2["end_min"] and 
            s2["start_min"] < s1["end_min"])

def load_courses():
    """
    Load courses from CSV and organize by course code.
    
    Reads the CSV file and creates a dictionary where:
    - Keys are course codes (e.g., "ITN 101")
    - Values are lists of section dictionaries
    
    Only includes courses in REQUIRED_COURSES list.
    
    Returns:
        dict: {course_code: [section1, section2, ...]}
    """
    courses = {}
    
    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            course_code = row["Course Code"]
            
            # Only keep required courses
            if course_code not in REQUIRED_COURSES:
                continue
            
            # Determine if in-person/hybrid or online
            delivery = row["Delivery Method"]
            is_in_person = delivery in ["In-Person", "Hybrid"]
            
            # Parse schedule (returns None for online courses)
            schedule = parse_days_time(row["Days/Time"])
            
            # Create a section dictionary with all info we need
            section = {
                "course_code": course_code,
                "class_number": row["Class Number"],
                "section": row["Section Number"],
                "instructor": row["Instructor"],
                "days_time": row["Days/Time"],
                "location": row["Location"],
                "delivery": delivery,
                "is_in_person": is_in_person,
                "schedule": schedule,
                "start_date": row["Start Date"],
                "end_date": row["End Date"]
            }
            
            # Add to courses dictionary
            if course_code not in courses:
                courses[course_code] = []
            courses[course_code].append(section)
    
    return courses

def score_schedule(combination, in_person_course_idx):
    """
    Score a schedule combination based on user preferences.
    
    Scoring system:
    - +200: Exactly 1 in-person class (GI Bill requirement)
    - +100: In-person class at Manassas (closest to Haymarket)
    - +50/+30/+10: Other preferred campuses
    - +5: Each online asynchronous course (better than virtual real-time)
    - -500: Each time conflict (major penalty)
    
    Args:
        combination: List of 5 sections (one per required course)
        in_person_course_idx: Index (0-4) of which course is the in-person one
    
    Returns:
        int: Score (higher is better). Negative scores are invalid.
    """
    score = 0
    
    # Count how many in-person classes are in this combination
    in_person_count = sum(1 for s in combination if s["is_in_person"])
    
    if in_person_count == 0:
        # Invalid: No in-person class means no GI Bill BAH
        return -1000
    
    # Bonus for having exactly 1 in-person (maximizes online courses)
    if in_person_count == 1:
        score += 200
    
    # Reward for in-person class being at preferred campus
    in_person_section = combination[in_person_course_idx]
    campus_score = CAMPUS_SCORES.get(in_person_section["location"], 0)
    score += campus_score
    
    # Penalize schedule conflicts
    # Check every pair of classes for time overlap
    for i, section1 in enumerate(combination):
        for j, section2 in enumerate(combination[i+1:], start=i+1):
            if check_conflict(section1, section2):
                score -= 500  # Major penalty - this schedule won't work!
    
    # Slight bonus for fully asynchronous online courses
    # (Virtual real-time requires being online at a specific time)
    for section in combination:
        if section["delivery"] == "Online Asynchronous":
            score += 5
    
    return score

def generate_schedules(courses):
    """
    Generate all possible schedule combinations and score them.
    
    This is the "brains" of the optimizer. It:
    1. Creates every possible combination of sections (cartesian product)
    2. For each combination, tries each course as the "in-person" class
    3. Scores each valid combination
    4. Sorts by score (best first)
    
    With 5 courses having ~15 sections each, this generates thousands
    of combinations, but modern computers can handle it in seconds.
    
    Args:
        courses: Dictionary of {course_code: [sections]}
    
    Returns:
        list: Sorted list of schedule dictionaries (best first)
    """
    # Get all sections for each required course
    # This creates a list of lists:
    # [[ITD256 sections], [ITN101 sections], [ITN170 sections], ...]
    course_sections = [courses.get(course, []) for course in REQUIRED_COURSES]
    
    # Check if we have sections for all required courses
    for i, course in enumerate(REQUIRED_COURSES):
        if not course_sections[i]:
            print(f"WARNING: No sections found for {course}")
            return []
    
    schedules = []
    
    # Generate all combinations (cartesian product)
    # product([A,B], [C,D], [E,F]) gives:
    # (A,C,E), (A,C,F), (A,D,E), (A,D,F), (B,C,E), ...
    for combination in product(*course_sections):
        # Try each course as the "in-person" course for GI Bill
        for in_person_idx in range(len(REQUIRED_COURSES)):
            # Skip if this course doesn't have an in-person section
            if combination[in_person_idx]["is_in_person"]:
                score = score_schedule(list(combination), in_person_idx)
                
                # Only save valid schedules (non-negative score)
                if score >= 0:
                    schedules.append({
                        "score": score,
                        "in_person_course": REQUIRED_COURSES[in_person_idx],
                        "classes": [
                            {
                                "course": REQUIRED_COURSES[i],
                                "class_number": sec["class_number"],
                                "section": sec["section"],
                                "instructor": sec["instructor"],
                                "days_time": sec["days_time"],
                                "location": sec["location"],
                                "delivery": sec["delivery"],
                                "is_gi_bill_class": i == in_person_idx
                            }
                            for i, sec in enumerate(combination)
                        ]
                    })
    
    # Sort by score (descending = best first)
    schedules.sort(key=lambda x: x["score"], reverse=True)
    
    return schedules

def main():
    """
    Main execution function.
    
    Orchestrates the entire optimization process:
    1. Load courses from CSV
    2. Generate and score all combinations
    3. Save top results to JSON
    4. Display top 5 in terminal
    """
    print("Loading course data...")
    courses = load_courses()
    
    # Display summary of available sections
    print(f"Found sections for {len(courses)} courses")
    for course, sections in courses.items():
        in_person = sum(1 for s in sections if s["is_in_person"])
        online = len(sections) - in_person
        print(f"  {course}: {len(sections)} sections ({in_person} in-person/hybrid, {online} online)")
    
    print("\nGenerating schedule combinations...")
    schedules = generate_schedules(courses)
    
    print(f"\nFound {len(schedules)} valid schedules")
    
    if schedules:
        # Save top 20 to JSON file
        top_schedules = schedules[:20]
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(top_schedules, f, indent=2)
        
        print(f"Saved top 20 schedules to {OUTPUT_FILE}")
        
        # Display top 5 in the terminal for quick review
        print("\n" + "="*80)
        print("TOP 5 SCHEDULE OPTIONS")
        print("="*80)
        
        for i, schedule in enumerate(top_schedules[:5], 1):
            print(f"\n--- OPTION {i} (Score: {schedule['score']}) ---")
            print(f"GI Bill Class (In-Person): {schedule['in_person_course']}")
            print()
            
            for cls in schedule['classes']:
                # ★ marks the GI Bill qualifying class
                marker = "★ " if cls['is_gi_bill_class'] else "  "
                print(f"{marker}{cls['course']:<10} {cls['section']:<6} | {cls['delivery']:<25} | {cls['days_time']:<25} | {cls['location']}")
            print()
    else:
        print("No valid schedules found!")

if __name__ == "__main__":
    main()
