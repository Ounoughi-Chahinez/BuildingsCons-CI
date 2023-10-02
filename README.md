# ReadMe

### Required python packages:

1. pandas

2. numpy 

3. keras

4. selenium

5. bs4


### Required files/inputs:

1. The Meters dictionary: Data/Meters_dictionary.csv

2. The Model: Model/Model-CNNLSTM.h5

3. The path to save the predictions: Results/preds.csv

4. The Weather Condition dictionary: Data/WeatherCondition_dictionary.csv

5. The Weather Wind dictionary: Data/WeatherWind_dictionary.csv

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

python3 Predictions.py --Meter_name=ICT_JK1_EM1.Total --new_value=0.08536 --d_path=Meters_dictionary.csv --d_WC_path=Data/WeatherCondition_dictionary.csv --d_WW_path=Data/WeatherWind_dictionary.csv --model_path=Model/Model-CNNLSTM.h5 --pred_path=Results/preds.csv
