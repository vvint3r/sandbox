import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_job_details(driver, url):
    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load

        # Locate and clean the job title
        job_title_element = driver.find_element(By.CSS_SELECTOR, 'h1.top-card-layout__title')
        job_title = job_title_element.text.strip().replace('"', '').replace("'", "")

        # Locate and clean the company name
        company_name_element = driver.find_element(By.CSS_SELECTOR, 'a.topcard__org-name-link')
        company_name = company_name_element.text.strip().replace('"', '').replace("'", "")

        # Locate and clean the job description
        job_description_element = driver.find_element(By.CSS_SELECTOR, 'div.description__text')
        job_description = job_description_element.text.strip().replace('"', '').replace("'", "")

        return job_title, company_name, job_description

    except Exception as e:
        print(f"Failed to retrieve details from {url}: {e}")
        return None, None, None


def extract_job_details_from_csv(csv_file, output_csv):
    # Read the CSV containing LinkedIn URLs
    df = pd.read_csv(csv_file)

    # Set up Selenium WebDriver with additional arguments
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")  # Required for some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems
    chrome_options.add_argument('--remote-debugging-port=9222')  # Avoid DevTools port issues

    service = Service('chromedriver.exe')  # Replace with your chromedriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)

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

    # Close the browser
    driver.quit()


# Example usage
input_csv = 'linkedin_jobs.csv'  # Input CSV file containing LinkedIn URLs
output_csv = 'linkedin_jobs_with_details.csv'  # Output CSV file to store job details
extract_job_details_from_csv(input_csv, output_csv)
