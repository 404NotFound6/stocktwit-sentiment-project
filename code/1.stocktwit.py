import requests
import pandas as pd
from lxml import etree
import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException

def log_in(driver,account,key):
    sign_up = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'SignUpButtons_logInLink')]")))
    sign_up.click()
    time.sleep(2)
    account_id = driver.find_element(By.CSS_SELECTOR, "input[name='login']")
    account_id.send_keys(account)
    time.sleep(0.5)
    account_keys = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    account_keys.send_keys(key)
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='log-in-submit']").click()
    time.sleep(5)
    return None

def scroll(driver,scroll_amount=800):
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

def get_comments_one_page(driver):
    comment_time = []
    comments = []
    try:
        time_elements = driver.find_elements(By.XPATH, "//time[contains(@class, 'StreamMessage_timestamp')]")
        comments_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'RichTextMessage_body')]")
        if len(time_elements) == len(comments_elements):
            for i in range(0,len(time_elements)):
                try:
                    datetime = time_elements[i].get_attribute("datetime")
                    pos = datetime.find("T")
                    comment_time.append(datetime[:pos])
                    comments.append(comments_elements[i].text)
                except:
                    pass
            else:
                pass
    except Exception as e:
        print(e)
    return comment_time,comments

def write_csv(data, company, header, path):
    data.insert(loc=0, column='company', value=company)
    file_path = os.path.join(path, "{}.csv".format(company))
    data.to_csv(file_path, mode='a+', index=False, header=header, sep=',')
    return None

def get_comments_one_stock(driver,url):
    all_information = pd.DataFrame()
    driver.get(url)
    log_in(driver,account,key)
    time.sleep(1)
    scroll(driver,scroll_amount=800)
    n = 0 
    while n<50:
        information = pd.DataFrame()
        comment_time,comments = comment_time,comments = get_comments_one_page(driver)
        time.sleep(1)
        scroll(driver,scroll_amount=1500)
        information["comment_time"] = comment_time
        information["comments"] = comments
        all_information = pd.concat([all_information, information], ignore_index=True)
        n += 1
        time.sleep(1)
    print(all_information)

if __name__ == "__main__":
    account = ""
    key = ""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    url = 'https://stocktwits.com/symbol/AAPL'
    get_comments_one_stock(driver,url)