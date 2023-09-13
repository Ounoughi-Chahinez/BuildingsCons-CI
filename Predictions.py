import sys
import argparse
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import datetime



def get_shared_arg_parser():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--elering_path', type=str, default='Data/elering-data.csv', help='Elering data path')
    parser.add_argument('--weather_path', type=str, default='Data/weather-data.csv', help='Weather data path')
    parser.add_argument('--new_value', type=float, default=0, help='The new consumption value comming from the meter')
    parser.add_argument('--Meter_name', type=int,  help='The Meter name')
    parser.add_argument('--d_path', type=str,default='Data/Meters_dictionary.csv', help='Meters codes Dictionary path')
    parser.add_argument('--d_WC_path', type=str,default='Data/WeatherCondition_dictionary.csv', help='Weather Condition Dictionary path')
    parser.add_argument('--d_WW_path', type=str,default='Data/WeatherWind_dictionary.csv', help='Weather Wind Dictionary path')
    parser.add_argument('--model_path',type=str, default='Model/Model-CNNLSTM.h5', help='Model path')
    parser.add_argument('--pred_path', type=str,default='Results/preds.csv', help='Save predictions path')
    
    return parser


# Prepare the data for the prediction task:
def prepare_data(Meter_name, new_value, elering, weather, d, d_WC, d_WW):
    # Get current time
    current_datetime = datetime.datetime.now()
    # Meter Code
    meter_code = d[d['Meters'] == Meter_name].iloc[0,0]
    # Weather data preprocessing:
    weather['Temperature'] = weather['Temperature'].str.replace('°F','').astype(int)
    weather['Dew Point'] = weather['Dew Point'].str.replace('°F','').astype(int)
    weather['Humidity'] = weather['Humidity'].str.replace('%','').astype(int)
    weather['Wind Speed'] = weather['Wind Speed'].str.replace('mph','').astype(int)
    weather['Wind Gust'] = weather['Wind Gust'].str.replace('mph','').astype(int)
    weather['Precip.'] = weather['Precip.'].str.replace('in','').astype(float)
    weather['Pressure'] = weather['Pressure'].str.replace('in','').astype(float)
    
    weather['Wind'] = d_WW[d_WW['Wind'] == weather['Wind'][0]].iloc[0,0]
    weather['Condition'] = d_WC[d_WC['Condition'] == weather['Condition'][0]].iloc[0,0]
    

    return weather[['Temperature', 'Dew Point', 'Humidity',
       'Wind Speed', 'Wind Gust', 'Pressure', 'Precip.', 'Wind', 'Condition']].iloc[0,:].tolist()+elering[['Soome', 'Läti', 'Venemaa(Leningrad)', 'Venemaa(Pihkva)','Tarbimine','Tootmine', 'Tuuleparkide toodang','Päikeseenergia toodang']].iloc[0,:].tolist()+ [current_datetime.month, current_datetime.hour,current_datetime.weekday()] + [meter_code, new_value]
    

# Function that returns the next 12h consumption prediction values:
def Future_Preditcion(Meter_name, new_value, elering, weather, d, d_WC, d_WW, model):
    Input_data = prepare_data(Meter_name, new_value, elering, weather, d, d_WC, d_WW)
    pred = model.predict(np.array(Input_data).reshape(1, 22, 1).astype(np.float32))
#     print('\n\nNext 12h consumption predictions values: '+str(pred)+' of the meter: ' + str(Meter_name))
    return pred

# Compute the CI for the next 12 hours based on the prediction of the energy:
def CarbonIntensity(Meter_name, pred, elering, d):
    G = []
    I = 0
    E = 0
    # Compute total imported and exported energy: otal minus exports, total positive imports
    if elering['Soome'][0]>0:
        I = I + elering['Soome'][0]
    else:
        E = E + elering['Soome'][0]
        
    if elering['Läti'][0]>0:
        I = I + elering['Läti'][0]
    else:
        E = E + elering['Läti'][0]
        
    if elering['Venemaa(Leningrad)'][0]>0:
        I = I + elering['Venemaa(Leningrad)'][0]
    else:
        E = E + elering['Venemaa(Leningrad)'][0]
        
    if elering['Venemaa(Pihkva)'][0]>0:
        I = I + elering['Venemaa(Pihkva)'][0]
    else:
        E = E + elering['Venemaa(Pihkva)'][0]
    
    F = elering['Tootmine'][0] - (elering['Tuuleparkide toodang'][0] + elering['Päikeseenergia toodang'][0])
    
    for i in pred: 
        G.append((F + (I*0.1))/ (E+pred))
        
    return G


def main(elering_path, weather_path, new_value, Meter_name, d_path, d_WC_path, d_WW_path,model_path, pred_path):
    
    # Read the current data:
    elering = pd.read_csv(elering_path)
    weather = pd.read_csv(weather_path)

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
    
    pred = Future_Preditcion(Meter_name, new_value, elering, weather, d, d_WC, d_WW, model)
    CI = CarbonIntensity(Meter_name, pred, elering, d)
    predictions = pd.read_csv(pred_path)
    
    if len(predictions)>0:
        index = -1
    else:
        index = 0
        
    predictions.at[index, 'Timestamp'] = datetime.datetime.now()
    predictions.at[index, 'Meter_name'] = Meter_name
    j = 0
    for i in range(2, 25, 2):
        predictions.iloc[index,i] = pred[0][j]
        predictions.iloc[index,i+1] = CI[0][0][j]
        j = j + 1
        
    predictions.index = predictions.index + 1 
    predictions = predictions.sort_index()
    predictions.to_csv(pred_path, index=False)
    
    return datetime.datetime.now(), Meter_name, pred, CI



if __name__ == "__main__":
    parser = get_shared_arg_parser()
    args = parser.parse_args()
    main(args.elering_path,args.weather_path,args.new_value,args.Meter_name,args.d_path,args.model_path, args.pred_path)