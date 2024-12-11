import requests
import pandas as pd
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
from dotenv import load_dotenv
from datastorage import save_to_database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_url(path):
    df = pd.read_excel(path)
    list = []
    url_list = []
    stock_name = []
    for cell_value in df["SYMBOL"]:
        c = cell_value
        list.append(c)
    for i in list:
        url = 'https://stocktwits.com/symbol/'+i
        stock_name.append(i)
        url_list.append(url)
    return url_list,stock_name

def log_in(driver,account,key):
    sign_up = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'SignUpButtons_logInLink')]")))
    sign_up.click()
    time.sleep(2)
    account_id = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='login']")))
    account_id.send_keys(account)
    time.sleep(0.5)
    account_keys = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    account_keys.send_keys(key)
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='log-in-submit']").click()
    time.sleep(5)
    return None

def scroll(driver, fetch_interval=5, step_size=1500, pause_time=0.5):
    for _ in range(fetch_interval):
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        time.sleep(pause_time)
    time.sleep(pause_time*2)

def scroll_to_bottom(driver, wait_time=5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def get_comments_one_page(driver):
    comment_time = []
    comments = []
    sentiments_tag = []
    influence = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//time[contains(@class, 'StreamMessage_timestamp')]"))
        )
        time_elements = driver.find_elements(By.XPATH, "//time[contains(@class, 'StreamMessage_timestamp')]")
        comments_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'RichTextMessage_body')]")
        time.sleep(2)
        if len(time_elements) == len(comments_elements) - 1:
            for i in range(0,len(time_elements)):
                try:
                    datetime = time_elements[i].get_attribute("datetime")
                    pos = datetime.find("T")
                    comment_time.append(datetime[:pos])
                    comments.append(comments_elements[i+1].text)
                    try:
                        parent_element1 = comments_elements[i+1].find_element(By.XPATH, "..")
                        sentiment_element = parent_element1.find_elements(By.XPATH, ".//span[contains(@class, 'StreamMessage_sentimentText')]")
                        if sentiment_element:
                            sentiments_tag.append(sentiment_element[0].text)
                        else:
                            sentiments_tag.append(None)
                    except:
                        sentiments_tag.append(None)
                    try:
                        parent_element2 = comments_elements[i + 1].find_element(By.XPATH, "./ancestor::div[contains(@class, 'StreamMessage_main')]")
                        influence_elements = parent_element2.find_elements(By.XPATH, ".//span[contains(@class, 'StreamMessageLabelCount_labelCount')]")
                        if len(influence_elements) == 4:
                            label_sum = sum(int(el.text) if el.text.strip() else 0 for el in influence_elements)
                        else:
                            label_sum = 0
                        influence.append(label_sum)
                    except Exception as e:
                        influence.append(0)
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
        elif len(time_elements) == len(comments_elements):
            for i in range(0,len(time_elements)):
                try:
                    datetime = time_elements[i].get_attribute("datetime")
                    pos = datetime.find("T")
                    comment_time.append(datetime[:pos])
                    comments.append(comments_elements[i].text)
                    try:
                        parent_element = comments_elements[i].find_element(By.XPATH, "..")
                        sentiment_element = parent_element.find_elements(By.XPATH, ".//span[contains(@class, 'StreamMessage_sentimentText')]")
                        if sentiment_element:
                            sentiments_tag.append(sentiment_element[0].text)
                        else:
                            sentiments_tag.append(None)
                    except:
                        sentiments_tag.append(None)
                    try:
                        parent_element2 = comments_elements[i].find_element(By.XPATH, "./ancestor::div[contains(@class, 'StreamMessage_main')]")
                        influence_elements = parent_element2.find_elements(By.XPATH, ".//span[contains(@class, 'StreamMessageLabelCount_labelCount')]")
                        if len(influence_elements) == 4:
                            label_sum = sum(int(el.text) if el.text.strip() else 0 for el in influence_elements)
                        else:
                            label_sum = 0
                        influence.append(label_sum)
                    except Exception as e:
                        influence.append(0)
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
        else:
            print(len(time_elements),len(comments_elements))
            pass
    except Exception as e:
        print(e)
    return comment_time,comments,sentiments_tag,influence

def write_csv(data, company, path):
    file_path = os.path.join(path, f"{company}.csv")
    write_header = not os.path.exists(file_path) 
    data.to_csv(file_path, mode='a+', index=False, header=write_header, sep=',')

def get_comments_one_stock(driver, stock, session, csv_path, max_duration=11000):
    all_information = pd.DataFrame()
    old_information = pd.DataFrame()
    time.sleep(1)
    scroll(driver, fetch_interval=2, step_size=1000, pause_time=0.5)
    n = 0
    start_time = time.time()
    while n<1400:
        elapsed_time = time.time() - start_time
        if elapsed_time > max_duration:
            print(f"Reached max duration for stock, exiting after {elapsed_time:.2f} seconds.")
            break
        try:
            comment_time,comments,sentiments_tag,influence = get_comments_one_page(driver)
            time.sleep(1)
            current_information = pd.DataFrame({
                "comment_time": comment_time,
                "comments": comments,
                "sentiment_tag": sentiments_tag,
                "influence": influence
            })
            if not old_information.empty:
                current_information = current_information[~current_information["comments"].isin(old_information["comments"])]
            if not current_information.empty:
                current_information.insert(loc=0, column='stock', value=stock)
                all_information = pd.concat([all_information, current_information], ignore_index=True)
                try:
                    save_to_database(current_information, session)
                except Exception as e:
                    print(f"Error saving to database for stock {stock}: {e}")
                try:
                    write_csv(current_information, stock, csv_path)
                except Exception as e:
                    print(f"Error writing to CSV for stock {stock}: {e}")
            old_information = current_information
            if n<5:
                scroll(driver, fetch_interval=5, step_size=1500, pause_time=0.5)
            elif n>10:
                scroll(driver, fetch_interval=5, step_size=1000, pause_time=0.5)
            else:
                scroll_to_bottom(driver, wait_time=5)
            n += 1
            time.sleep(1)
        except Exception as e:
            n += 1
            time.sleep(1)
            continue
    return all_information

def get_comments_all_stock(path,account,key,session):
    url_list,stock_name = get_url(path)
    csv_path = "./comments"
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    for url, stock in zip(url_list, stock_name):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            time.sleep(5)
            log_in(driver, account, key)
            get_comments_one_stock(driver, stock, session, csv_path)
        except Exception as e:
            print(f"Error while scraping stock {stock}: {e}")
        finally:
            driver.quit()
            time.sleep(5)
    return None

if __name__ == "__main__":
    account = ""
    key = ""
    path = "data/Dow_Jones_Average_Index_companies.xlsx"
    load_dotenv()
    DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_DATABASE = os.getenv("DATABASE_DATABASE")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DATABASE}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    get_comments_all_stock(path, account, key, session)


