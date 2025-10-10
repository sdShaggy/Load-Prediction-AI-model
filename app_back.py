from flask import Flask, render_template
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

models = joblib.load('models/model_2.pkl')
xgb_model = models['xgb']
lgb_model = models['lgb']
meta_model = models['meta']
scaler = models['scaler'] 

df = pd.read_excel('better_data_1.xlsx',parse_dates=['date'])

df['dow'] = df['date'].dt.dayofweek
df['is_weekend'] = df['dow'].isin([5, 6]).astype(int)
df['lag1'] = df['today_peak_load'].shift(1)
df['lag7'] = df['today_peak_load'].shift(7)
df['roll3'] = df['today_peak_load'].rolling(3).mean()
df['roll7'] = df['today_peak_load'].rolling(7).mean()
df = df.dropna()

FEATURE_COLS = [
    'BRPL', 'TPDDL', 'BYPL', 'NDMC',
    'today_peak_load', 'public_holiday',
    'temperature', 'precipitation', 'wind_speed',
    'dow', 'is_weekend',
    'lag1', 'lag7', 'roll3', 'roll7'
]

@app.route('/')
def home():
    new_df = df.dropna(subset=FEATURE_COLS + ['tomorrow peak load'])
    last_row = new_df.iloc[-1]
    features = last_row[FEATURE_COLS].values.reshape(1, -1)
    features_scaled = scaler.transform(features)

    pred_xgb = xgb_model.predict(features_scaled)[0]
    pred_lgb = lgb_model.predict(features_scaled)[0]
    pred_stack = meta_model.predict(np.array([[pred_xgb, pred_lgb]]))[0]

    # print("FEATURES:", features)
    # print("SCALED FEATURES:", features_scaled)
    # print("PREDICTION (XGB):", pred_xgb)

    max_today = df['today_peak_load'].iloc[-1]
    actual = last_row['tomorrow peak load']
    rel_perc_error = (abs(pred_xgb - actual) / actual)*100 
    rel_rmse = (float(np.sqrt((pred_xgb - actual) ** 2)) / actual )

    today_str = datetime.now().strftime("%A, %d %b %Y")
    
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%A, %d %b %Y")

    return render_template(
        'UI.html',
        today_date=today_str,
        tomorrow_date=tomorrow_str,
        predicted_load=f"{pred_xgb:.2f}",
        rmse=f"{rel_rmse:.2f}",
        abs_error=f"{rel_perc_error:.2f}",
        max_today=f"{max_today:.2f}"
    )
    
if __name__ == '__main__':
    app.run(debug=True)

