from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import csv
import sys
import random
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver import ActionChains

# Store credentials securely in environment variables
APOLLO_EMAIL = os.getenv('APOLLO_EMAIL', 'vasily.souzdenkov@gmail.com')
APOLLO_PASSWORD = os.getenv('APOLLO_PASSWORD', 'Souzdenkov23!')

# Initialize the WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--dns-prefetch-disable")  # Disable DNS prefetching
options.add_argument("--no-sandbox")  # Helps with some network issues in certain environments
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems in Docker environments
options.add_argument(
    # Spoof User-Agent
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
try:
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
except Exception as e:
    print(f"Error initializing WebDriver: {e}")
    exit(1)

# Create CSV file to store data with UTF-8 encoding
output_file = 'apollo_records.csv'
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Title", "Company", "Email", "Links", "Location", "# Employees", "Industry", "Keywords"])

try:
    # Step 1: Navigate to Apollo login page
    retries = 3
    for attempt in range(retries):
        try:
            driver.get("https://app.apollo.io/#/login")
            break
        except WebDriverException as e:
            if attempt < retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(random.uniform(3, 7))  # Randomized delay
            else:
                print(f"Failed to load page after {retries} attempts: {e}")
                driver.quit()
                exit(1)

    # Step 2: Enter credentials and log in
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_input.send_keys(APOLLO_EMAIL)
    time.sleep(random.uniform(1, 3))  # Random delay between typing actions

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(APOLLO_PASSWORD)
    time.sleep(random.uniform(1, 3))  # Random delay between typing actions

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    ActionChains(driver).move_to_element(login_button).click().perform()

    # Wait for login to complete and the People tab to appear
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.LINK_TEXT, "People"))
    ).click()

    # Step 3: Iterate through each page and handle each record
    max_pages = int(os.getenv('MAX_PAGES', 10))  # Use an environment variable to set the limit
    page_count = 1
    while page_count <= max_pages:
        try:
            # Wait until all rows on the page are present
            records = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'table-row-')]")
                                                    ))

            for index in range(len(records)):
                try:
                    record_xpath = f"//div[@id='table-row-{index}']"
                    record = driver.find_element(By.XPATH, record_xpath)
                    try:
                        access_button = record.find_element(By.XPATH, ".//button[span[text()='Access email']]")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", access_button)
                        time.sleep(random.uniform(1, 3))  # Random delay to simulate human interaction
                        driver.execute_script("arguments[0].click();", access_button)
                        time.sleep(random.uniform(3, 6))  # Wait to ensure the email is unlocked
                    except NoSuchElementException:
                        # Email is already unlocked, proceed to data collection
                        pass

                    # Collect data for the record
                    name = record.find_element(By.XPATH, ".//a[@data-to]/span").text
                    title = record.find_element(By.XPATH, ".//span[contains(@class, 'zp_xvo3G')]").text
                    company = record.find_element(By.XPATH, ".//a[@data-link-variant='default']/span").text
                    email = record.find_element(By.XPATH, ".//span[contains(@class, 'zp_hdyyu')]/span").text

                    # Updated link extraction logic to handle missing elements
                    try:
                        links_element = record.find_element(By.XPATH, ".//a[contains(@href, 'linkedin')]")
                        links = links_element.get_attribute("href")
                    except NoSuchElementException:
                        links = "N/A"

                    # Added safety check to collect location and other fields that might be missing
                    try:
                        location = record.find_element(
                            By.XPATH, ".//span[contains(@class, 'zp_xvo3G') and contains(text(), ',')]").text
                    except NoSuchElementException:
                        location = "N/A"

                    try:
                        employees = record.find_element(By.XPATH, ".//span[contains(@data-count-size, 'small')]").text
                    except NoSuchElementException:
                        employees = "N/A"

                    try:
                        industry = record.find_element(By.XPATH, ".//span[contains(@class, 'zp_CEZf9')]").text
                    except NoSuchElementException:
                        industry = "N/A"

                    try:
                        keywords = record.find_element(
                            By.XPATH, ".//div[contains(@class, 'zp_ofXB9')]//span[contains(@class, 'zp_CEZf9')]").text
                    except NoSuchElementException:
                        keywords = "N/A"

                    # Write data to CSV file
                    with open(output_file, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([name, title, company, email, links, location, employees, industry, keywords])

                    print(f"Name: {name}, Title: {title}, Company: {company}, Email: {email}, Links: {links}, Location: {
                        location}, Employees: {employees}, Industry: {industry}, Keywords: {keywords}")
                except NoSuchElementException as e:
                    print(f"Error processing record {index}: {e}")
                    continue

            # Step 4: Click the next page button if available
            next_page_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//i[contains(@class, 'apollo-icon-chevron-arrow-right')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_button)
            driver.execute_script("arguments[0].click();", next_page_button)
            time.sleep(random.uniform(3, 7))  # Random delay for next page loading
            page_count += 1
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            print(f"No more pages available or an error occurred: {e}")
            break

finally:
    # Close the driver
    driver.quit()
