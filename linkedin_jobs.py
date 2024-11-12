from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import pandas as pd

# Initialize the WebDriver (assuming Chrome)
def initialize_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless')  # Run in headless mode if specified
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Replace 'chromedriver.exe' with your chromedriver path if needed
    driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=options)
    return driver


def linkedin_login(driver):
    # Open LinkedIn login page
    driver.get("https://www.linkedin.com/login")

    # Wait for the page to load
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "username")))

    # Enter credentials
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")

    username_field.send_keys("vasily.souzdenkov@gmail.com")
    password_field.send_keys("Godric23!")

    # Click the login button
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

headless_mode = True  # Set to False to see the browser UI

driver = initialize_driver(headless=headless_mode)

linkedin_login(driver)

def get_job_details(driver, url):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)  # Explicit wait of 15 seconds

        # Locate and click the "...show more" button to expand the job description
        try:
            show_more_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".feed-shared-inline-show-more-text__see-more-less-toggle")))
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(2)  # Wait for the description to expand
        except Exception as e:
            print(f"Show more button not found or could not be clicked: {e}")

        # Locate and clean the job title
        try:
            job_title_element = driver.find_element(By.CSS_SELECTOR, 'h1')
            job_title = job_title_element.text.strip().replace('"', '').replace("'", "")
        except Exception as e:
            print(f"Job title not found: {e}")
            job_title = None

        # Locate and clean the company name
        try:
            company_name_element = driver.find_element(
                By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a')
            company_name = company_name_element.text.strip().replace('"', '').replace("'", "")
        except Exception as e:
            print(f"Company name not found: {e}")
            company_name = None

        # Locate and clean the job description
        try:
            job_description_elements = driver.find_elements(By.CSS_SELECTOR, 'div.feed-shared-inline-show-more-text *')
            job_description = " ".join([elem.text.strip() for elem in job_description_elements if elem.text.strip()])
            job_description = job_description.replace('"', '').replace("'", "")
        except Exception as e:
            print(f"Job description not found: {e}")
            job_description = None

        # Locate and extract the date posted information
        try:
            date_posted_element = driver.find_element(By.CSS_SELECTOR, 'span.tvm__text.tvm__text--low-emphasis')
            date_posted_text = date_posted_element.text.strip()
            # Translate the date posted text to an actual date
            today = pd.Timestamp('today')
            if 'day' in date_posted_text:
                days_ago = int(re.search(r'(\d+) day', date_posted_text).group(1))
                date_posted = today - pd.Timedelta(days=days_ago)
            elif 'week' in date_posted_text:
                weeks_ago = int(re.search(r'(\d+) week', date_posted_text).group(1))
                date_posted = today - pd.Timedelta(weeks=weeks_ago)
            elif 'month' in date_posted_text:
                months_ago = int(re.search(r'(\d+) month', date_posted_text).group(1))
                date_posted = today - pd.DateOffset(months=months_ago)
            else:
                date_posted = None
        except Exception as e:
            print(f"Date posted not found: {e}")
            date_posted = None

        return job_title, company_name, job_description, date_posted

    except Exception as e:
        print(f"Failed to retrieve details from {url}: {e}")
        return None, None, None, None


def extract_job_details_from_csv(csv_file, output_csv):
    # Read the CSV containing LinkedIn URLs
    df = pd.read_csv(csv_file)

    # Set up Selenium WebDriver with additional arguments
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")  # Required for some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems
    chrome_options.add_argument('--remote-debugging-port=9222')  # Avoid DevTools port issues

    service = Service('chromedriver.exe')  # Replace with your chromedriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Login to LinkedIn
    linkedin_login(driver)

    job_titles = []
    company_names = []
    job_descriptions = []
    date_posted_list = []

    # Loop through each URL in the CSV
    for index, row in df.iterrows():
        url = row['URL']  # Assuming the column in the CSV is named 'URL'
        print(f"Processing {url}")
        # Unpack all four return values from get_job_details()
        job_title, company_name, job_description, date_posted = get_job_details(driver, url)
        job_titles.append(job_title)
        company_names.append(company_name)
        job_descriptions.append(job_description)
        date_posted_list.append(date_posted)

    # Add the extracted data to the dataframe
    df['Job Title'] = job_titles
    df['Company Name'] = company_names
    df['Job Description'] = job_descriptions
    df['Date Posted'] = date_posted_list

    # Save the results to a new CSV file
    df.to_csv(output_csv, index=False)

    # Keep the browser open for inspection
    input("Press Enter to close the browser...")

    # Close the browser
    driver.quit()


# Example usage
input_csv = 'linkedin_jobs.csv'  # Input CSV file containing LinkedIn URLs
output_csv = 'linkedin_jobs_with_details.csv'  # Output CSV file to store job details
extract_job_details_from_csv(input_csv, output_csv)
