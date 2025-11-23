import csv
import time
import re
from bs4 import BeautifulSoup

# Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# CONFIGURATION
# ==========================================
# The set of courses we want to scrape.
TARGET_COURSES = {
    "ITD 256",
    "ITN 101",
    "ITN 170",
    "ITN 213",
    "ITN 254",
    "ITN 260"
}

# The subjects (prefixes) to search for on the NVCC site.
SUBJECTS = ["ITN", "ITD"]

# The name of the file where we will save the data.
OUTPUT_FILE = "nvcc_spring_2026_schedule_data.csv"

# The URL of the NVCC Spring 2026 Schedule Search.
BASE_URL = "https://www.nvcc.edu/academics/schedule/crs2262/search"

def setup_driver():
    """
    Initializes and returns a headless Chrome WebDriver.
    
    'Headless' means the browser runs in the background without a visible UI window.
    This is faster and better for automated scripts.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without a window
    chrome_options.add_argument("--no-sandbox") # Bypass OS security model (required for some environments)
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    chrome_options.add_argument("--window-size=1920,1080") # Set a standard window size
    
    # Set a 'User-Agent' to make our script look like a real browser (Mac Chrome).
    # This helps avoid being blocked by the website's security filters.
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Automatically download and install the correct Chrome driver for the installed Chrome version.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main():
    """
    Main execution function.
    1. Sets up the browser.
    2. Iterates through each subject.
    3. Navigates pages and extracts data.
    4. Saves the results to a CSV file.
    """
    driver = setup_driver()
    all_data = [] # List to hold all the course dictionaries we find
    
    try:
        # Loop through each subject we need to check (e.g., "ITN", "ITD")
        for subject in SUBJECTS:
            url = f"{BASE_URL}?subject={subject}"
            print(f"Navigating to {url}")
            driver.get(url)
            
            # Loop to handle pagination (clicking "Next" until done)
            while True:
                # ------------------------------------------
                # 1. WAIT FOR CONTENT TO LOAD
                # ------------------------------------------
                # Dynamic websites load content with JavaScript. We must wait for the content 
                # to appear before we try to read it. We wait up to 10 seconds for an <h3> tag.
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "h3"))
                    )
                except:
                    print("Timeout waiting for content or no courses found.")
                    break
                
                # ------------------------------------------
                # 2. PARSE THE PAGE WITH BEAUTIFULSOUP
                # ------------------------------------------
                # Selenium gives us the current state of the HTML (driver.page_source).
                # BeautifulSoup allows us to easily search and extract text from that HTML.
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Find all course headers. On this site, course titles are in <h3> tags.
                course_headers = soup.find_all('h3')
                
                for header in course_headers:
                    header_text = header.get_text(strip=True)
                    # Example Header: "ITN 100 - Intro to Telecommunications"
                    
                    # Check if this header contains one of our target courses
                    found_course = None
                    for target in TARGET_COURSES:
                        if target in header_text:
                            found_course = target
                            break
                    
                    if found_course:
                        # ------------------------------------------
                        # 3. EXTRACT DETAILS
                        # ------------------------------------------
                        # If we found a course, we need to find its details (Section, Time, etc.).
                        # The details are usually in a container div surrounding the header.
                        container = header.find_parent('div') 
                        if not container:
                            container = header.find_parent('li') # Fallback if it's a list item
                            
                        if container:
                            # Get all text from the container, separated by pipes '|' to make parsing easier.
                            text_content = container.get_text(separator=' | ', strip=True)
                            
                            # Use Regular Expressions (Regex) to find specific patterns in the text.
                            
                            # Extract Class Number (the registration identifier)
                            # Matches "Class Nbr: | 77473"
                            class_nbr_match = re.search(r'Class Nbr:\s*\|\s*(\d+)', text_content)
                            class_number = class_nbr_match.group(1) if class_nbr_match else "N/A"
                            
                            # Extract Section Number (e.g., "Section: | 001A")
                            section_match = re.search(r'Section:\s*\|\s*([A-Z0-9]+)', text_content)
                            section = section_match.group(1) if section_match else "N/A"
                            
                            # Extract Instructor
                            instructor = "Not Listed"
                            if "Instructor" in text_content:
                                instr_match = re.search(r'Instructor:\s*\|\s*([^|]+)', text_content)
                                if instr_match:
                                    instructor = instr_match.group(1).strip()
                            
                            # Extract Dates (e.g., "01/20/26 - 05/11/26")
                            date_match = re.search(r'Date:\s*\|\s*(\d{2}/\d{2}/\d{2})\s*-\s*(\d{2}/\d{2}/\d{2})', text_content)
                            start_date = date_match.group(1) if date_match else "See Syllabus"
                            end_date = date_match.group(2) if date_match else "See Syllabus"
                            
                            # Extract Time (e.g., "11:10A - 12:30P")
                            time_match = re.search(r'Time:\s*\|\s*([^|]+)', text_content)
                            time_str = time_match.group(1).strip() if time_match else "Check Schedule"
                            
                            # Extract Days (e.g., "MoWe")
                            days_match = re.search(r'Days:\s*\|\s*([^|]+)', text_content)
                            days_str = days_match.group(1).strip() if days_match else ""
                            
                            # Combine Days and Time for a cleaner output
                            days_time = f"{days_str} {time_str}".strip()
                            
                            # Extract Campus Location
                            campus_match = re.search(r'Campus:\s*\|\s*([^|]+)', text_content)
                            campus = campus_match.group(1).strip() if campus_match else "Unknown"
                            
                            # Extract Delivery Mode (e.g., "In-person", "WW", "CV")
                            mode_match = re.search(r'Mode:\s*\|\s*([^|]+)', text_content)
                            mode_code = mode_match.group(1).strip() if mode_match else ""
                            
                            # Translate Mode Codes to Human-Readable Text
                            delivery = "In-Person"
                            if mode_code == "WW":
                                delivery = "Online Asynchronous"
                            elif mode_code == "CV":
                                delivery = "Virtual Real-Time"
                            elif mode_code == "HY":
                                delivery = "Hybrid"
                            elif mode_code == "In-person":
                                delivery = "In-Person"
                            else:
                                delivery = mode_code # Fallback
                                
                            # Create a dictionary for this row of data
                            row = {
                                "Course Code": found_course,
                                "Class Number": class_number,
                                "Section Number": section,
                                "Instructor": instructor,
                                "Days/Time": days_time,
                                "Location": campus,
                                "Delivery Method": delivery,
                                "Start Date": start_date,
                                "End Date": end_date,
                                "Raw Data": text_content[:200] # Save snippet for debugging
                            }
                            all_data.append(row)
                            print(f"Found {found_course} Section {section}")

                # ------------------------------------------
                # 4. HANDLE PAGINATION
                # ------------------------------------------
                # Look for the "Next" button to go to the next page of results.
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Next"]')
                    
                    # Check if the button is disabled (meaning we are on the last page)
                    parent = next_button.find_element(By.XPATH, '..')
                    if "disabled" in parent.get_attribute("class"):
                        print("Reached last page")
                        break
                    
                    print("Clicking Next...")
                    # Use JavaScript to click because sometimes elements overlap the button
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3) # Simple wait to allow the new page to load
                except Exception as e:
                    print(f"Pagination stopped: {e}")
                    break
                    
    finally:
        # Always close the browser, even if an error occurs
        driver.quit()
        
    # ------------------------------------------
    # 5. SAVE DATA TO CSV
    # ------------------------------------------
    if all_data:
        with open(OUTPUT_FILE, 'w', newline='') as f:
            fieldnames = ["Course Code", "Class Number", "Section Number", "Instructor", "Days/Time", "Location", "Delivery Method", "Start Date", "End Date", "Raw Data"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
        print(f"Successfully wrote {len(all_data)} rows to {OUTPUT_FILE}")
    else:
        print("No data found.")

if __name__ == "__main__":
    main()
