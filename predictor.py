import joblib
import numpy as np
import pandas as pd

egdata = pd.read_excel('test_data.xlsx')

model = joblib.load('loadpredai.pkl')

error = []

for i in range(0,171):
    data = egdata.iloc[i, 1:9]

    newdata = pd.DataFrame([data],columns=['BRPL','TPDDL','BYPL','NDMC','today_peak_load','public_holiday','temperature','precipitation','wind_speed'])

    prediction = model.predict(newdata)
    actual = egdata.iloc[i,10]
    
    error.append(abs((actual-prediction)*100/actual))

error.sort()
for i,e in enumerate(error):
    print(i,'   ',e)