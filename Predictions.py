import sys, os
import argparse
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import datetime, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pytz

def get_shared_arg_parser():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--Meter_name', type=int,  help='The Meter name')
    parser.add_argument('--new_value', type=float, default=0, help='The new consumption value comming from the meter')
    parser.add_argument('--d_path', type=str,default='Meters_dictionary.csv', help='Meters codes Dictionary path')
    parser.add_argument('--d_WC_path', type=str,default='WeatherCondition_dictionary.csv', help='Weather Condition Dictionary path')
    parser.add_argument('--d_WW_path', type=str,default='WeatherWind_dictionary.csv', help='Weather Wind Dictionary path')
    parser.add_argument('--model_path',type=str, default='Model-CNNLSTM.h5', help='Model path')
    parser.add_argument('--pred_path', type=str,default='preds.csv', help='Save predictions path')
    
    return parser

def get_latest_downloaded_file(directory_path):
    try:
        # List all files in the directory
        files = [os.path.join(directory_path, filename) for filename in os.listdir(directory_path)]
        # Filter out directories (if any)
        files = [file for file in files if os.path.isfile(file)]
        if not files:
            return None
        # Sort the files by modification time in descending order (latest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        # Return the path of the latest downloaded file
        return files[0]
    except Exception as e:
        # Handle any exceptions, e.g., directory not found
        print(f"An error occurred file: {e}")
        return None
    

    
def download_and_process_csv_data(base_url, download_dir, start_time, end_time,driver):
    try:
        # Construct the URL with start and end times
        url = f"{base_url}&start={start_time}&end={end_time}"

        # Open the website
        driver.get(url)
        # Wait for the page to load (you may need to adjust the waiting time)
        time.sleep(5)
        # Locate and click the CSV download button
        # Find all elements with the specified class
        buttons = driver.find_elements(By.CSS_SELECTOR, '.btn.btn-secondary.btn-xs.removecaret')
        # Loop through the buttons and click the one with the text "CSV"
        for button in buttons:
            if button.text == "CSV":
                button.click()
                break  # Exit the loop after clicking the "CSV" button

        # Wait for the download to complete (you may need to adjust the waiting time)
        time.sleep(15)
        # Get the downloaded file's name (assuming it's the only file in the directory)
        downloaded_file = get_latest_downloaded_file(download_dir)

        # Specify the full path to the downloaded CSV file
        csv_file_path = os.path.join(download_dir, downloaded_file)

        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path, encoding='ISO-8859-1', sep=';')

        df['Kuupäev (Eesti aeg)'] = pd.to_datetime(df['Kuupäev (Eesti aeg)'])
        df.drop('Ajatempel (UTC)', axis=1,inplace=True)
#         df.dropna(axis=1, how='all', inplace=True)
        # Convert specific columns to float (e.g., 'Column1' and 'Column2')
        columns_to_convert = df.columns[1:]
        for column in columns_to_convert:
            df[column] = df[column].astype(str)
            df[column] = df[column].str.replace(',','.').astype(float)   
        return df

    except Exception as e:
        print(f"An error occurred csv: {e}")
        return None
    
# scarping elering lanned data:
def planned_energy(current_datetime):
    
    current_datetime = current_datetime.astimezone(pytz.utc) - datetime.timedelta(hours=3)
    # Calculate the datetime 12 hours from now
    end_datetime = current_datetime + datetime.timedelta(hours=15)
    # Format the datetime in the desired format
    start_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
    end_datetime = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
   
    
    download_dir = os.getcwd() +"/Data"
    # Set Chrome options to specify the download directory
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    chrome_options.add_argument('--headless')

    # Initialize the webdriver with Chrome options
    driver = webdriver.Chrome(options=chrome_options)

    url1 = "https://dashboard.elering.ee/en/transmission/cross-border-planned-trade?interval=hours&period=months"
    url2 = "https://dashboard.elering.ee/en/system/with-plan/production-consumption?interval=minute&period=days"
    url3 = "https://dashboard.elering.ee/en/system/with-plan/production-renewable?interval=minute&period=days"
    url4 = "https://dashboard.elering.ee/en/system/with-plan/production-solar?interval=minute&period=days"

    # Download and process data from each URL
    df1 = download_and_process_csv_data(url1, download_dir, start_datetime, end_datetime,driver)
    df2 = download_and_process_csv_data(url2, download_dir, start_datetime, end_datetime,driver)
    df3 = download_and_process_csv_data(url3, download_dir, start_datetime, end_datetime,driver)
    df4 = download_and_process_csv_data(url4, download_dir, start_datetime, end_datetime,driver)
    

    # Merge the DataFrames based on the 'Time' column
    merged_df = pd.merge(df1, df2, on='Kuupäev (Eesti aeg)', how='inner')
    merged_df = pd.merge(merged_df, df3, on='Kuupäev (Eesti aeg)', how='inner')
    merged_df = pd.merge(merged_df, df4, on='Kuupäev (Eesti aeg)', how='inner')
    # Close the browser
    driver.quit()
    
    return merged_df

# scraping weather data:
def scrape_weather(current_datetime,d_WW,d_WC):
    # URL of the webpage you want to inspect
    url = 'https://www.wunderground.com/hourly/EEKA'  # Replace with the URL of the webpage you're interested in

    # Configure Chrome options to run in headless mode (optional)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)

    # Initialize the WebDriver with Chrome options
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the webpage
        driver.get(url)
        time.sleep(5)
        # Execute JavaScript code to get the content of the element with the provided JavaScript path
        js_path = "#hourly-forecast-table"
        element_content = driver.execute_script(f"return document.querySelector('{js_path}').outerHTML;")
        # Parse the element's content with BeautifulSoup
        soup = BeautifulSoup(element_content, 'html.parser')
        # Find the table element (adjust the CSS selector as needed)
        table = soup.find('table', class_='mat-table cdk-table')
        # Initialize empty lists to store table data
        data = []
        # Extract the table data
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all('td'):
                row_data.append(cell.text.strip())
            data.append(row_data)
            
        filtered_list = [sublist for sublist in data if sublist]
        # Convert the data into a pandas DataFrame
        df = pd.DataFrame(filtered_list, columns=["Time","Conditions","Temp.","Feels Like", "Precip","Amount","Cloud Cover","Dew Point","Humidity","Wind","Pressure"])  # Replace with actual column names
        df = df[["Time","Temp.","Dew Point","Humidity","Wind","Pressure","Precip","Conditions"]]
        # Weather data preprocessing:
        df['Temp.'] = df['Temp.'].str.replace('°F','').astype(int)
        df['Dew Point'] = df['Dew Point'].str.replace('°F','').astype(int)
        df['Humidity'] = df['Humidity'].str.replace('°%','').astype(int)
        df['Precip'] = df['Precip'].str.replace('°%','').astype(float)
        df['Pressure'] = df['Pressure'].str.replace('°in','').astype(float)
        df[['Wind Speed', 'Wind']] = df['Wind'].str.split('°mph ',n=1, expand=True)
        df['Wind Speed'] = df['Wind Speed'].astype(float)
        # Replace values in the 'Wind' column using d_WW
        df['Wind'] = df['Wind'].replace(' ','')
        df['Wind'] = df['Wind'].replace(d_WW.set_index('Wind')['index'])
        # Replace values in the 'Conditions' column using d_WC
        df['Conditions'] = df['Conditions'].replace(d_WC.set_index('Condition')['index'])
        df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%H:%M:%S')
        df['Time'] = pd.to_datetime(df['Time'])
        # Save the DataFrame to a CSV file
        df.to_csv('Data/Weather_data_'+str(current_datetime.strftime("%Y-%m-%d"))+'.csv', index=False)
        return df

    except Exception as e:
        print(f"An error occurred weather: {e}")
    finally:
        # Close the browser
        driver.quit()
    

# Prepare the data for the prediction task:
def prepare_data(Meter_name, d, d_WC, d_WW, current_datetime, new_value):
    # Meter Code
    meter_code = d[d['Meters'] == Meter_name].iloc[0,0]
    # Weather data preprocessing:
    weather = scrape_weather(current_datetime,d_WW,d_WC)
    filtered_weather = weather[weather['Time'].dt.hour == current_datetime.hour + 1]
    # Elering data preprocessing
    elering = planned_energy(current_datetime)
    filtered_elering = elering[elering['Kuupäev (Eesti aeg)'].dt.hour == current_datetime.hour][['ee_fi', 'ee_lv', 'ee_ru','Tarbimine','Tootmine', 'Tuuleparkide toodang','Päikeseenergia toodang']]
    return elering, filtered_weather[['Temp.', 'Dew Point', 'Humidity',
       'Wind Speed', 'Pressure', 'Precip', 'Wind', 'Conditions']].iloc[0,:].tolist()+filtered_elering.iloc[0,:].tolist()+ [current_datetime.month, current_datetime.hour,current_datetime.weekday()] + [meter_code, new_value]
    

# Function that returns the next 12h consumption prediction values:
def future_preditcion(Meter_name, d, d_WC, d_WW, model,current_datetime, pred_path, new_value):
    elering, Input_data = prepare_data(Meter_name, d, d_WC, d_WW, current_datetime, new_value)
    pred = model.predict(np.array(Input_data).reshape(1, 20, 1).astype(np.float32))
    CI = carbon_intensity(pred, elering,current_datetime)
    predictions = pd.read_csv(pred_path)
    
    if len(predictions)>0:
        index = -1
    else:
        index = 0
        
    predictions.at[index, 'Timestamp'] = current_datetime
    predictions.at[index, 'Meter_name'] = Meter_name
    j = 0
    for i in range(2, 25, 2):
        predictions.iloc[index,i] = pred[0][j]
        predictions.iloc[index,i+1] = CI[0][j]
        j = j + 1

    
    predictions.index = predictions.index + 1 # shifting index
    predictions = predictions.sort_index()
    predictions.to_csv(pred_path, index=False)
    
    return current_datetime, Meter_name, pred, CI, predictions


# Compute the CI for the next 12 hours based on the prediction of the energy:
def carbon_intensity(pred,elering, current_datetime):
    G = []
    F = []
    elering_pred = elering[elering['Kuupäev (Eesti aeg)'].dt.hour > current_datetime.hour]
    elering_pred = elering[['ee_fi', 'ee_lv' , 'ee_ru', 'Planeeritud tootmine', 'Tuuleparkide toodangu prognoos - süsteemioperaator','Päikeseenergia toodangu prognoos - süsteemioperaator']]
  
    for i in range(len(pred)):
        I = 0
        E = 0
        # Compute total imported and exported energy: otal minus exports, total positive imports
        if elering_pred.iloc[i,0]>0:
            I = I + elering_pred.iloc[i,0]
        else:
            E = E + elering_pred.iloc[i,0]

        if elering_pred.iloc[i,1]>0:
            I = I + elering_pred.iloc[i,1]
        else:
            E = E + elering_pred.iloc[i,1]

        if elering_pred.iloc[i,2]>0:
            I = I + elering_pred.iloc[i,2]
        else:
            E = E + elering_pred.iloc[i,2]

        
        f = elering_pred.iloc[i,3] - (elering_pred.iloc[i,4] + elering_pred.iloc[i,5])
        F.append(f)
        g = (f + (I*0.1))/ (abs(E)+pred[i])

        G.append(g)
        
    return G
  

def main( Meter_name, new_value,d_path, d_WC_path, d_WW_path,model_path, pred_path):
    
    
    # Define the local time zone (replace 'America/New_York' with your local time zone)
    local_timezone = pytz.timezone('Europe/Tallinn')
    # Localize the local time to the specified time zone
    current_datetime = local_timezone.localize(datetime.datetime.now())
    # Upload the dictionaries:
    d = pd.read_csv(d_path)
    dictionary={}
    for k in range(len(d)):
        dictionary.update({d.iloc[k,1] : d.iloc[k,0] })
    # Upload the dictionaries:
    d_WW = pd.read_csv(d_WW_path)
    dictionary_WW={}
    for k in range(len(d_WW)):
        dictionary_WW.update({d_WW.iloc[k,1] : d_WW.iloc[k,0] })    
    # Upload the dictionaries:
    d_WC = pd.read_csv(d_WC_path)
    dictionary_WC={}
    for k in range(len(d_WC)):
        dictionary_WC.update({d_WC.iloc[k,1] : d_WC.iloc[k,0] })

    # Upload the model:
    model = load_model(model_path)
          
    return future_preditcion(Meter_name, d, d_WC, d_WW, model,current_datetime,pred_path,new_value)
    



if __name__ == "__main__":
    parser = get_shared_arg_parser()
    args = parser.parse_args()
    main(args.Meter_name,args.d_path,args.model_path, args.pred_path)
