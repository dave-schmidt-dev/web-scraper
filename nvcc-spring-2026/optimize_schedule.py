"""
Course Schedule Optimizer
Finds the best combination of classes to maximize online enrollment
while maintaining GI Bill BAH eligibility (at least 1 in-person/hybrid class).
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
# User is driving from Haymarket
CAMPUS_SCORES = {
    "Manassas": 100,
    "Woodbridge": 50,
    "Annandale": 30,
    "Alexandria": 10,
    "Loudoun": 5,
    "Reston Center": 5,
    "NOVA Online": 0
}

def parse_time_to_minutes(time_str):
    """
    Convert time string like '11:10A' to minutes from midnight.
    Returns None if parsing fails.
    """
    try:
        dt = datetime.strptime(time_str, "%I:%M%p")
        return dt.hour * 60 + dt.minute
    except (ValueError, AttributeError):
        return None

def parse_days_time(days_time_str):
    """
    Parse Days/Time field into structured data.
    Example: "MW 09:35A - 10:55A" -> {days: "MW", start: 09:35A, end: 10:55A}
    Returns None if online/no schedule.
    """
    match = re.match(r"([MTWRFSU]+)\s+(\d{1,2}:\d{2}[AP])\s*-\s*(\d{1,2}:\d{2}[AP])", days_time_str)
    if match:
        return {
            "days": match.group(1),
            "start_time": match.group(2),
            "end_time": match.group(3),
            "start_min": parse_time_to_minutes(match.group(2)),
            "end_min": parse_time_to_minutes(match.group(3))
        }
    return None

def check_conflict(section1, section2):
    """
    Check if two sections have a time conflict.
    Returns True if they conflict.
    """
    # Online courses never conflict
    if not section1["schedule"] or not section2["schedule"]:
        return False
    
    s1 = section1["schedule"]
    s2 = section2["schedule"]
    
    # Check if they share any days
    days1 = set(s1["days"])
    days2 = set(s2["days"])
    
    if not days1.intersection(days2):
        return False  # No shared days
    
    # Check time overlap
    # Conflict if: start1 < end2 AND start2 < end1
    if s1["start_min"] is None or s2["start_min"] is None:
        return False
    
    return (s1["start_min"] < s2["end_min"] and 
            s2["start_min"] < s1["end_min"])

def load_courses():
    """
    Load courses from CSV and organize by course code.
    Returns: {course_code: [section, section, ...]}
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
            
            # Parse schedule
            schedule = parse_days_time(row["Days/Time"])
            
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
            
            if course_code not in courses:
                courses[course_code] = []
            courses[course_code].append(section)
    
    return courses

def score_schedule(combination, in_person_course_idx):
    """
    Score a schedule combination.
    Higher score = better schedule.
    
    Args:
        combination: List of 5 sections (one per required course)
        in_person_course_idx: Which course (0-4) is the in-person one
    """
    score = 0
    
    # Base score: Has exactly 1 in-person class
    in_person_count = sum(1 for s in combination if s["is_in_person"])
    
    if in_person_count == 0:
        return -1000  # Invalid: violates GI Bill requirement
    
    # Bonus for having exactly 1 in-person (maximize online)
    if in_person_count == 1:
        score += 200
    
    # Reward for in-person class being at preferred campus
    in_person_section = combination[in_person_course_idx]
    campus_score = CAMPUS_SCORES.get(in_person_section["location"], 0)
    score += campus_score
    
    # Penalize schedule conflicts
    for i, section1 in enumerate(combination):
        for j, section2 in enumerate(combination[i+1:], start=i+1):
            if check_conflict(section1, section2):
                score -= 500  # Major penalty for conflicts
    
    # Slight bonus for online courses being fully online (avoid virtual real-time if possible)
    for section in combination:
        if section["delivery"] == "Online Asynchronous":
            score += 5
    
    return score

def generate_schedules(courses):
    """
    Generate all possible combinations and score them.
    Returns list of schedules sorted by score (best first).
    """
    # Get all sections for each required course
    course_sections = [courses.get(course, []) for course in REQUIRED_COURSES]
    
    # Check if we have sections for all required courses
    for i, course in enumerate(REQUIRED_COURSES):
        if not course_sections[i]:
            print(f"WARNING: No sections found for {course}")
            return []
    
    schedules = []
    
    # Generate all combinations (cartesian product)
    for combination in product(*course_sections):
        # Try each course as the "in-person" course
        for in_person_idx in range(len(REQUIRED_COURSES)):
            if combination[in_person_idx]["is_in_person"]:
                score = score_schedule(list(combination), in_person_idx)
                
                if score >= 0:  # Valid schedule
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
    
    # Sort by score (descending)
    schedules.sort(key=lambda x: x["score"], reverse=True)
    
    return schedules

def main():
    """
    Main execution: Load courses, generate schedules, save results.
    """
    print("Loading course data...")
    courses = load_courses()
    
    print(f"Found sections for {len(courses)} courses")
    for course, sections in courses.items():
        in_person = sum(1 for s in sections if s["is_in_person"])
        online = len(sections) - in_person
        print(f"  {course}: {len(sections)} sections ({in_person} in-person/hybrid, {online} online)")
    
    print("\nGenerating schedule combinations...")
    schedules = generate_schedules(courses)
    
    print(f"\nFound {len(schedules)} valid schedules")
    
    if schedules:
        # Save top 20 to JSON
        top_schedules = schedules[:20]
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(top_schedules, f, indent=2)
        
        print(f"Saved top 20 schedules to {OUTPUT_FILE}")
        
        # Display top 5
        print("\n" + "="*80)
        print("TOP 5 SCHEDULE OPTIONS")
        print("="*80)
        
        for i, schedule in enumerate(top_schedules[:5], 1):
            print(f"\n--- OPTION {i} (Score: {schedule['score']}) ---")
            print(f"GI Bill Class (In-Person): {schedule['in_person_course']}")
            print()
            
            for cls in schedule['classes']:
                marker = "★ " if cls['is_gi_bill_class'] else "  "
                print(f"{marker}{cls['course']:<10} {cls['section']:<6} | {cls['delivery']:<25} | {cls['days_time']:<25} | {cls['location']}")
            print()
    else:
        print("No valid schedules found!")

if __name__ == "__main__":
    main()
