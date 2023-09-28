# ReadMe

### Required python packages:

1. pandas

2. numpy 

3. keras


### Required files/inputs:

1. The current data: elering-data.csv, weather-data.csv, elering_pred-data.csv (Future 12 hours market data)

2. The Meters dictionary: Meters_dictionary.csv

3. The Model: Model-CNNLSTM.h5

4. The path to save the predictions: preds.csv

5. The Weather Condition dictionary: WeatherCondition_dictionary.csv

6. The Weather Wind dictionary: WeatherWind_dictionary.csv

### To get the prediction:

- Replace the paths according to your directories:

- new_value: is the new energy consumption value comming from the meter.

- Meter_name: is the meter's name of of the different buildings.


### List of Meters names (18 meters in 8 different buildings):

- ICT_JK1_EM1.Total
- ICT_JK1_EM2.Total
- ITK_JK1_EM1.Total
- LIB_JK1_EM1.Total
- LIB_JK1_EM2.Total
- LIB_JK2_EM1.Total
- NRG_JK2_EM1.Total
- NRG_JK2_EM2.Total
- SOC_JK1_EM1.Total
- SOC_JK1_EM2.Total
- SPORT_JK1_EM1.Total
- SPORT_JK1_EM2.Total
- U03_JK1_EM1.Total
- U03_JK1_EM2.Total
- VK1_JK1_EM1.Total
- VK1_JK1_EM2.Total
- VK2_JK1_EM1.Total
- VK2_JK1_EM2.Total

### Run the predictions script

python3 Predictions.py --elering_path=elering-data.csv --elering_pred_path=elering_pred-data.csv --weather_path=weather-data.csv --new_value=0.08536 --Meter_name=ICT_JK1_EM1.Total  --d_path=Meters_dictionary.csv --d_WC_path WeatherCondition_dictionary.csv --d_WW_path WeatherWind_dictionary.csv --model_path=Model-CNNLSTM.h5 --pred_path=preds.csv
