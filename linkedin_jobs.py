from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains

# Initialize the WebDriver (assuming Chrome)
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-blink-features=AutomationControlled')  # Avoid WebDriver detection
options.add_argument(
    # Spoof User-Agent
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=options)

# Disable WebDriver detection by modifying properties
script_to_disable_webdriver = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script_to_disable_webdriver})

# Function to login to LinkedIn


def linkedin_login(driver):
    driver.get("https://www.linkedin.com/login")
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")

        ActionChains(driver).move_to_element(username_field).click().send_keys("vasily.souzdenkov@gmail.com").perform()
        ActionChains(driver).move_to_element(password_field).click().send_keys("Godric23!").perform()

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        ActionChains(driver).move_to_element(login_button).click().perform()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.ID, "global-nav")))  # Wait until the main page loads
    except Exception as e:
        print(f"Error during login: {e}")
        # # # driver.quit()  # Commented out to keep the browser open for debugging  # Commented out to keep the browser open for debugging
        # exit()


# Login to LinkedIn
linkedin_login(driver)

# Load URLs from linkedin_jobs.csv
try:
    df_jobs = pd.read_csv('linkedin_jobs.csv')
    job_links = df_jobs['URL'].tolist()
except Exception as e:
    print(f"Error loading URLs from CSV: {e}")
    driver.quit()
    exit()

# Extract detailed job information


def get_job_details(driver, url):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        job_title = company_name = job_description = date_posted = location = remote_status = salary = None

        # Expand job description if available
        try:
            show_more_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '.feed-shared-inline-show-more-text__see-more-less-toggle')))
            ActionChains(driver).move_to_element(show_more_button).click().perform()
            time.sleep(2)
        except Exception as e:
            print(f"Show more button not found or could not be clicked: {e}")
            time.sleep(2)  # Retry after a brief wait
            try:
                show_more_button = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.feed-shared-inline-show-more-text__see-more-less-toggle')))
                ActionChains(driver).move_to_element(show_more_button).click().perform()
                time.sleep(2)
            except Exception as e:
                print(f"Retry failed to click show more button: {e}")

        # Extract job title
        try:
            job_title_element = driver.find_element(By.CSS_SELECTOR, 'h1')
            job_title = job_title_element.text.strip()
        except Exception as e:
            print(f"Job title not found: {e}")

        # Extract company name
        try:
            company_name_element = driver.find_element(
                By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a')
            company_name = company_name_element.text.strip()
        except Exception as e:
            print(f"Company name not found: {e}")

        # Extract job description
        try:
            job_description_elements = driver.find_elements(By.CSS_SELECTOR, 'div.description__text *')
            job_description = " ".join([elem.text.strip() for elem in job_description_elements if elem.text.strip()])
            job_description = re.sub(r'[^\w\s]', '', job_description).replace('\n', ' ').strip()
        except Exception as e:
            print(f"Job description not found: {e}")

        # Extract remote status and salary
        try:
            # Extract salary, typically the first span that starts with '$'
            salary_element = driver.find_element(By.XPATH, "//span[contains(text(), '$')]")
            salary = salary_element.text.strip()
        except Exception as e:
            print(f"Salary not found: {e}")

        try:
            # Extract remote status ('Remote', 'Onsite', 'Hybrid')
            remote_status_element = driver.find_element(
                By.XPATH, "//span[contains(text(), 'Remote') or contains(text(), 'Onsite') or contains(text(), 'Hybrid')]")
            remote_status = remote_status_element.text.strip()
        except Exception as e:
            print(f"Remote status not found, assuming Onsite: {e}")
            remote_status = 'Onsite'

        # Extract location
        try:
            # Locate the first span inside the primary description container, which typically contains the location
            primary_description_container = driver.find_element(
                By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__primary-description-container')
            location_element = primary_description_container.find_element(
                By.XPATH, './/span[contains(@class, "tvm__text")]')
            location = location_element.text.strip()
        except Exception as e:
            print(f"Location not found: {e}")

        # Extract date posted
        try:
            date_posted_element = driver.find_element(By.CSS_SELECTOR, 'span.tvm__text.tvm__text--low-emphasis')
            date_posted_text = date_posted_element.text.strip()
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

        return job_title, company_name, job_description, date_posted, location, remote_status, salary
    except Exception as e:
        print(f"Failed to retrieve details from {url}: {e}")
        return None, None, None, None


# Extract detailed job descriptions from the loaded URLs
job_titles = []
company_names = []
job_descriptions = []
dates_posted = []
locations = []
remote_statuses = []
salaries = []

for link in job_links:
    title, company, description, date_posted, location, remote_status, salary = get_job_details(driver, link)
    job_titles.append(title)
    company_names.append(company)
    job_descriptions.append(description)
    dates_posted.append(date_posted)
    locations.append(location)
    remote_statuses.append(remote_status)
    salaries.append(salary)

# Add extracted details to the DataFrame
df_jobs['Job Title'] = job_titles
df_jobs['Company Name'] = company_names
df_jobs['Job Description'] = job_descriptions
df_jobs['Date Posted'] = dates_posted
df_jobs['Location'] = locations
df_jobs['Remote Status'] = remote_statuses
df_jobs['Salary'] = salaries

# Save to CSV
df_jobs.to_csv('linkedin_jobs_with_details.csv', index=False)
print("Jobs data saved to 'linkedin_jobs_with_details.csv'")

# Close the driver
driver.quit()
