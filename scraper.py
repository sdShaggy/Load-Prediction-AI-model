from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
from meteostat import Point, Daily
from datetime import datetime, timedelta,date
import requests
from bs4 import BeautifulSoup


EXCEL_FILE = "better_data_1.xlsx"
SLDC = "https://delhisldc.org/Loadcurve.aspx?Loc=0805"
HOL_URL = "https://www.qppstudio.net/publicholidays2025/india-delhi.htm"
DELHI_LOC = Point(28.7041, 77.1025)

options = Options()
options.headless = True
service = Service("C:/chromedriver-win64/chromedriver.exe")  # Path to chrome driver. 
driver = webdriver.Chrome(service=service, options=options)

def extract_peak_loads(date):
    date_str = date.strftime("%d/%m/%Y")
    try:
        driver.get(SLDC)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder2_SelectedDate"))
        )
        date_input = driver.find_element(By.ID, "ContentPlaceHolder2_SelectedDate")
        driver.execute_script("arguments[0].value = '';", date_input)
        date_input.send_keys(date_str)
        driver.find_element(By.ID, "ContentPlaceHolder2_Button1").click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolder2_dgdetails"))
        )
        time.sleep(1)  

        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find(id="ContentPlaceHolder2_dgdetails")
        if not table:
            print(f"No SLDC table in HTML for {date_str}")
            return None

        rows = table.find_all("tr")[1:]  

        discom_map = {"BRPL": "BRPL", "BYPL": "BYPL", "NDPL": "TPDDL", "NDMC": "NDMC"}
        peak_loads = {}

        for r in rows:
            cols = r.find_all("td")
            if len(cols) < 2:
                continue

            entity = cols[0].get_text(strip=True)
            peak = cols[1].get_text(strip=True)

            if entity == "Delhi":
                try:
                    peak_loads["today_peak_load"] = float(peak)
                except:
                    peak_loads["today_peak_load"] = None
            elif entity in discom_map:
                try:
                    peak_loads[discom_map[entity]] = float(peak)
                except:
                    peak_loads[discom_map[entity]] = None

        for k in ["BRPL", "TPDDL", "BYPL", "NDMC"]:
            peak_loads.setdefault(k, None)
        peak_loads.setdefault("today_peak_load", None)

        return peak_loads

    except TimeoutException:
        print(f"Table didn't load in time on {date_str}")
        return None
    except Exception as e:
        print(f"Error extracting {date_str}: {e}")
        return None

# print(extract_peak_loads(date(2025, 7, 17)))
# print(extract_peak_loads(date(2025, 7, 16)))

def fetch_holidays_set():
    response = requests.get(HOL_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    holidays = set()
    table = soup.select_one("body > page-content > table") or soup.find("table")
    if not table:
        print("No table found on holidays page.")
        return holidays

    rows = table.find("tbody").find_all("tr")
    for row in rows:
        time_tag = row.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            try:
                holiday_date = datetime.strptime(time_tag["datetime"], "%Y-%m-%d").date()
                holidays.add(holiday_date)
            except Exception as e:
                print(f"Failed to parse date from '{time_tag['datetime']}': {e}")

    return holidays

holidays_set = fetch_holidays_set()
# print("Fetched holidays:", sorted(holidays_set))

def is_public_holiday(date):
    return int(date in holidays_set)

# print (is_public_holiday(date(2025, 12, 25)))

def fetch_weather(date):
    date_dt = datetime.combine(date, datetime.min.time())
    data = Daily(DELHI_LOC, date_dt, date_dt).fetch()

    if data.empty:
        return {
            "temperature": None,
            "precipitation": None,
            "wind_speed": None
        }

    return {
        "temperature": data["tavg"].iloc[0],
        "precipitation": data["prcp"].iloc[0],
        "wind_speed": data["wspd"].iloc[0],
    }

if pd.io.common.file_exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    df["date"] = pd.to_datetime(df["date"])
    last_date = df["date"].max().date()
else:
    df = pd.DataFrame(columns=[
        "date", "BRPL", "TPDDL", "BYPL", "NDMC", "today_peak_load",
        "public_holiday", "temperature", "precipitation", "wind_speed", "tomorrow peak load"
    ])
    last_date = datetime.today().date() - timedelta(days=1)

today = datetime.today().date()
new_rows = []
start_date =  max(last_date + timedelta(days=1), datetime(2025, 1, 18).date())
current = start_date

while current <= today:
    print(f"\nScraping for {current}")
    current_dt = datetime.combine(current, datetime.min.time())
    try:
        peak_loads = extract_peak_loads(current)
        if peak_loads is None:
            print(f"No SLDC data for {current}, skipping.")
            current += timedelta(days=1)
            continue

        if not all(peak_loads[d] is not None for d in ["BRPL", "TPDDL", "BYPL", "NDMC"]):
            print(f"Incomplete SLDC data for {current}, skipping.")
            current += timedelta(days=1)
            continue

        weather = fetch_weather(current)
        holiday = is_public_holiday(current)

        row = {
            "date": current_dt,
            "BRPL": peak_loads["BRPL"],
            "TPDDL": peak_loads["TPDDL"],
            "BYPL": peak_loads["BYPL"],
            "NDMC": peak_loads["NDMC"],
            "today_peak_load": peak_loads["today_peak_load"],
            "public_holiday": holiday,
            **weather,
            "tomorrow peak load": pd.NA
        }

        print("Row added:", row)
        new_rows.append(row)

    except Exception as e:
        print(f"Error on {current}: {e}")
    print(f"New rows collected: {len(new_rows)}")

    current += timedelta(days=1)

print(f"Total new rows scraped: {len(new_rows)}")

if new_rows:
    df_new = pd.DataFrame(new_rows)
    df_new.dropna(subset=["BRPL", "TPDDL", "BYPL", "NDMC", "today_peak_load"], how='all', inplace=True)
    print("df_new preview:\n", df_new)
    df = pd.concat([df, df_new], ignore_index=True)

df["date"] = pd.to_datetime(df["date"])
for i in range(1, len(df)):
    prev_date = df.loc[i - 1, 'date']
    current_date = df.loc[i, 'date']
    if (current_date - prev_date).days == 1:
        if pd.isna(df.loc[i - 1, 'tomorrow peak load']) and pd.notna(df.loc[i, 'today_peak_load']):
            df.loc[i - 1, 'tomorrow peak load'] = df.loc[i, 'today_peak_load']

df.drop_duplicates(subset=["date"], keep="last", inplace=True)

with pd.ExcelWriter(EXCEL_FILE, engine='xlsxwriter', date_format='yyyy-mm-dd') as writer:
    df.to_excel(writer, index=False)

print(f"\nSaved to {EXCEL_FILE}. Total rows: {len(df)}")
driver.quit()
