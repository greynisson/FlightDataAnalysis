## Import libraries:

from datetime import datetime, timedelta
from pathlib import Path
import os
import pandas as pd
import time
import requests
import json
import random
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

## Define functions:

# def IsFilenameAlreadyExisting(filename):
#     directory_actual = os.path.join("PlaneTicketData",)
#     data_files_existing = os.listdir(directory_actual) + os.listdir(directory_plan)
#     if filename in data_files_existing:
#         return True
#     return False
        
def PauseRandomlyLong():
    delay = round(random.randint(31, 53) / float(17),2)
    time.sleep(delay)

def PauseRandomlyShort():
    delay = round(random.randint(17, 31) / float(17),2)
    time.sleep(delay)
    
def GetIcelandairURL(dest, date_out_str):
    url= f"""https://www.icelandair.com/api/instantSearch/v1/bestPrice/byDay/return/multipleReturnsPerDeparture?
    departure=KEF
    &arrival={dest}
    &locale=is-IS
    &period=0
    &tripDuration=1
    &tripDurationFlexibility=21
    &fromDate={date_out_str}
    &fallbackToRouteCurrency=true
    """
    return url.replace("\n", "").replace(" ", "")

# def SampleDataFromPlay(dataFromRequest, samplingList):
#     data_home = dataFromRequest.json()['data']['lowestPrices']['homebound']
#     data_out = dataFromRequest.json()['data']['lowestPrices']['outbound']

#     for out in data_out:
#         for home in data_home:
#             if home['date'] <= out['date']: continue

#             cost = int(home['price']) + int(out['price'])

#             samplingList.append(
#                 {'Airline': 'Play',
#                  'C_Date': today_str,
#                  'DateOut': out['date'],
#                  'DateBack': home['date'],
#                  'Destination': dest,
#                  'Price': cost})
            
#     return samplingList

def SampleDataFromIcelandair(samplingList):
    dates_back = sorted(response.json()['inbound'].keys())

    for date_back_str in dates_back:
        samplingList.append(
        {'Airline': 'Icelandair',
         'C_Date': today_str,
         'DateOut': date_out_str,
         'DateBack': date_back_str,
         'Destination': dest,
         'Price': response.json()['inbound'][date_back_str]['totalFareAmount']})
    
    return samplingList

def ChooseDestinations(dest_from, dest_to):
    btn_dest_dep.click()
    time.sleep(2)
    input_dest_dep = browser.find_element_by_id("airportsAutocomplete")
    input_dest_dep.send_keys(dest_from + Keys.DOWN + Keys.ENTER)
    time.sleep(2)
    input_dest_dep = browser.find_element_by_id("airportsAutocomplete")
    input_dest_dep.send_keys(dest_to + Keys.DOWN + Keys.ENTER)
    time.sleep(2)
    btn_date_dep.click()
    time.sleep(2)

def GetYearMonth():
    month_ids = {
        'janúar': '01',
        'febrúar': '02',
        'mars': '03',
        'apríl': '04',
        'maí': '05',
        'júní': '06',
        'júlí': '07',
        'ágúst': '08',
        'september': '09',
        'október': '10',
        'nóvember': '11',
        'desember': '12'
    }
#     html = soup.find("div",{"class":"rdp-month", 'class':'rdp-caption_first'})
    year_month_arr = soup.find('div', {'class': 'rdp-caption'}).text.split(" ")[::-1]
    year_month_arr[1] = month_ids[year_month_arr[1]]
    return year_month_arr


def GetSoup():
    current_month_xpath = "//*[@id=\"__next\"]/div[2]/div[2]/header/div[2]/div[1]/div/div[2]/div/div[1]/form/div/div[4]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div/div[1]"
    current_month = browser.find_element(By.XPATH, current_month_xpath)
    html = current_month.get_attribute('innerHTML')
    soup = bs(html, 'html.parser')
    return soup

def GetCalendarCells(soup):
    calendar_cells = soup.find_all('div', {'class': 'css-e4o1c'})
    return calendar_cells

def GetDate(calendar_cell):
    date_arr = GetYearMonth()
    day_raw = calendar_cell.find('span').text
    day = day_raw if len(day_raw) > 1 else '0' + day_raw
    date_arr.append(day)
    return '-'.join(date_arr)

def GetTicketPrice(calendar_cell):
    ticket_price = int(calendar_cell.find('div', {'class': 'css-1mowg62'}).text.replace(',', ''))
    return ticket_price

def IsTripTooLong(date_out, date_home, max_trip_length = 21):
    date_out_array = [int(x) for x in date_out.split('-')]
    date_home_array = [int(x) for x in date_home.split('-')]
    
    day_count_out = sum([a * b for a,b in zip(date_out_array,  [365, 30, 1])])
    day_count_home = sum([a * b for a,b in zip(date_home_array,  [365, 30, 1])])
    
    trip_length = day_count_home - day_count_out
    
    return trip_length > max_trip_length

def GoToNextMonth():
    btn_next = browser.find_element(By.XPATH, "//*[@id=\"__next\"]/div[2]/div[2]/header/div[2]/div[1]/div/div[2]/div/div[1]/form/div/div[4]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div/div[2]/div/div[2]/button")
    btn_next.click()
    time.sleep(2)
    
def GetTicketPrices():
    prices = {}
    
    for i in range(0, number_of_months):
        soup = GetSoup()
        calendar_cells = GetCalendarCells(soup)
        print('-'.join(GetYearMonth()))
        time.sleep(1)
        
        for cell in calendar_cells:
            prices[GetDate(cell)] = GetTicketPrice(cell)
            
        time.sleep(2)
        GoToNextMonth()
            
    return prices

def GetTripPrices(prices):
    for out_date in data_out:
        for home_date in data_home:
            if home_date > out_date:
                if IsTripTooLong(out_date, home_date): break
                trip_cost = data_out[out_date] + data_home[home_date]
                prices.append(
                    {'Airline': 'Play',
                     'C_Date': today_str,
                     'DateOut': out_date,
                     'DateBack': home_date,
                     'Destination': dest,
                     'Price': trip_cost
                    })
    return prices

## Initialize directories:

dir_play = os.path.join('PlaneTicketData', 'Play')
dir_iceair = os.path.join('PlaneTicketData', 'Icelandair')

Path('PlaneTicketData').mkdir(parents=True, exist_ok=True)
Path(dir_play).mkdir(parents=True, exist_ok=True)
Path(dir_iceair).mkdir(parents=True, exist_ok=True)

## Steal prices from Play:

today = datetime.now()
today_str = today.strftime('%Y-%m-%d')

number_of_months = 4
dests = ['ALC', 'AMS', 'BER', 'CDG', 'CPH', 'STN', 'TFS']

dest_counter = 1

trip_prices = []

target_filename = f"PlaneTicketPrice_Play_{today_str}.csv"
target_filename_path = os.path.join('PlaneTicketData', 'Play') 

if target_filename not in os.listdir(target_filename_path):
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: Data sampling started.")
    
    browser = webdriver.Chrome(os.path.join(os.getcwd(), "chromedriver.exe"))
    browser.get(f"https://www.flyplay.com/is/")
    browser.implicitly_wait(10)

    btn_dest_dep = browser.find_element_by_id("originAirportButton")
    btn_date_dep = browser.find_element_by_id("departureDateButton")

    for dest in dests:
        data_out = {}
        data_home = {}
    
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time}: Sampling data for {dest}.")
        ChooseDestinations('kef', dest)

        for i in range(0, number_of_months):
            soup = GetSoup()
            calendar_cells = GetCalendarCells(soup)

            for cell in calendar_cells:
                data_out[GetDate(cell)] = GetTicketPrice(cell)

            time.sleep(2)

            GoToNextMonth()

        time.sleep(2)

        ChooseDestinations(dest, 'kef')

        for i in range(0, number_of_months):
            soup = GetSoup()
            calendar_cells = GetCalendarCells(soup)

            for cell in calendar_cells:
                data_home[GetDate(cell)] = GetTicketPrice(cell)

            time.sleep(2)

            GoToNextMonth()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time}: Data sampling for {dest} completed ({dest_counter} / {len(dests)})")
        time.sleep(2)

        trip_prices = GetTripPrices(trip_prices)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: Data sampling finished.")
    
    if trip_prices:
        df = pd.DataFrame(trip_prices)
        df.to_csv(os.path.join(target_filename_path, target_filename), index=False)
        print(f'Data has been saved to a file: {target_filename}')
    else:
        print("No data was added to the database.")

    browser.close()

else:
    print(f'File already exists: {target_filename}')


## Steal prices from Icelandair:

today = datetime.now() + timedelta(days=-1)
today_str = today.strftime('%Y-%m-%d')

number_of_days = 31
random.seed(today)

dest_counter = 1

dests = ['AMS', 'BER', 'BOS', 'ORD', 'DEN',
         'DUB', 'FRA', 'CPH', 'LHR', 'MAN', 
         'MUC', 'NYC', 'MCO', 'OSL', 'CDG', 
         'SEA', 'ARN', 'TFS', 'YTO', 'IAD',]

target_filename = f"PlaneTicketPrice_Icelandair_{today_str}.csv"
target_filename_path = os.path.join('PlaneTicketData', 'Icelandair') 

if target_filename not in os.listdir(target_filename_path):

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: Data sampling started.")
    
    trip_prices = []

    for dest in dests:
        
        for i in range(1, number_of_days):
            date_out = today + timedelta(days=i)
            date_out_str = date_out.strftime('%Y-%m-%d')

            url = GetIcelandairURL(dest, date_out_str)
            
            response = requests.get(url)
            PauseRandomlyShort()
            
            if (response.status_code == 200):
                
                print(f"{date_out_str}: Found flights to {dest} ({i}/{number_of_days - 1})")
                
                trip_prices = SampleDataFromIcelandair(trip_prices)
            else:
                print(f"No flights available to {dest} ({i}/{number_of_days - 1})")
        
        dest_counter += 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time}: Data sampling for {dest} completed ({dest_counter}/{len(dests)})")
        PauseRandomlyLong()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time}: Data sampling finished.")
    if trip_prices:
        df = pd.DataFrame(trip_prices)
        df.to_csv(os.path.join(target_filename_path, target_filename), index=False)
        print(f'Data has been saved to a file: {target_filename}')
    else:
        print("No data was sampled in this run.")

else:
    print('File already exists.')