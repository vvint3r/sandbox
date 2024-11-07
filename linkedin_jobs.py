from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re  # Import the regex module
import pandas as pd

# Initialize the WebDriver (assuming Chrome)
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=options)


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
            job_title = job_title_element.text.strip()
            job_title = re.sub(r'[^a-zA-Z0-9\s]', '', job_title)  # Remove quotes and other non-alphanumeric characters
        except Exception as e:
            print(f"Job title not found: {e}")
            job_title = None

        # Locate and clean the company name
        try:
            company_name_element = driver.find_element(
                By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a')
            company_name = company_name_element.text.strip()
            company_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name)  # Remove quotes and other non-alphanumeric characters
        except Exception as e:
            print(f"Company name not found: {e}")
            company_name = None

        # Locate and clean the job description
        try:
            job_description_elements = driver.find_elements(By.CSS_SELECTOR, 'div.feed-shared-inline-show-more-text *')
            job_description = " ".join([elem.text.strip() for elem in job_description_elements if elem.text.strip()])
            # Remove quotes and other non-alphanumeric characters
            job_description = re.sub(r'[^a-zA-Z0-9\s]', '', job_description)
        except Exception as e:
            print(f"Job description not found: {e}")
            job_description = None

        return job_title, company_name, job_description

    except Exception as e:
        print(f"Failed to retrieve details from {url}: {e}")
        return None, None, None


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

    # Loop through each URL in the CSV
    for index, row in df.iterrows():
        url = row['URL']  # Assuming the column in the CSV is named 'URL'
        print(f"Processing {url}")
        job_title, company_name, job_description = get_job_details(driver, url)
        job_titles.append(job_title)
        company_names.append(company_name)
        job_descriptions.append(job_description)

    # Add the extracted data to the dataframe
    df['Job Title'] = job_titles
    df['Company Name'] = company_names
    df['Job Description'] = job_descriptions

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
