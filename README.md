# Load-Prediction-AI-model

A comprehensive AI-based solution for **next-day electricity peak load prediction** in Delhi. This suite includes data scraping, preprocessing, advanced ML modeling, a live web dashboard (Flask), and detailed error visualization using Jupyter.

---

## 🌟 Features :

- 📊 **Daily Load Forecasting** using ensemble ML models
- 🔄 **Web Scraping** from:
  - SLDC (real-time DISCOM peak loads)
  - Meteostat (weather features)
  - Public Holiday from www.qppstudio.net
- 🧠 **Stacked Model** (XGBoost + LightGBM → Ridge Regression)
- 🌐 **Web Dashboard** using Flask + HTML/CSS
- 📈 **Performance Analysis** via `predictor.ipynb`
- 💾 Trained model exported as `model_2.pkl`

---

## 🚀 How to Run :

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

## 2️⃣ Run Data Scraper
Scrape DISCOM data, holidays, and weather → auto-generate better_data_1.xlsx
```bash
python scraper.py
```

## 3️⃣ Train Model
Train XGBoost + LightGBM + Ridge stacking model and save to model_2.pkl
```bash
python model_1.py
```

## 4️⃣ Launch Flask Web App
Runs a local dashboard showing predicted peak load for tomorrow
```bash
python model_1.py
```
- Open http://localhost:5000 in your browser.
- Auto-refreshes hourly.
- Displays predicted load, today’s load, RMSE, and error %.

## 5️⃣ Explore Metrics & Error Analysis
Run the Jupyter notebook:
```bash
jupyter notebook predictor.ipynb
```
- Visualizes prediction accuracy (APE plots, prediction vs actual).
- Calculates RMSE and APE for all three models.

---

## 🧠 Model Details :

### Model Inputs :-
- DISCOM loads: BRPL, TPDDL, BYPL, NDMC
- Weather: temperature, precipitation, wind_speed
- Date Features: day-of-week, is_weekend, public_holiday
- Lag features: lag1, lag7, roll3, roll7

### Model Stack :-
- Base: XGBoost, LightGBM
- Meta: Ridge Regression
- Tuned with Optuna, evaluated with TimeSeriesSplit CV

### Output :-
- Final model exported as model_2.pkl
  - Includes: xgb, lgb, meta models and StandardScaler

---

## 🧰 Tech Stack Used :

### 📌 Languages & Frameworks :
- Python - Core Language
- Flask – Web backend and dashboard
- HTML + CSS – Web UI (template via UI.html)
- Jupyter Notebook – Visual analytics and error reporting

### 📦 Machine Learning & Optimization :
- XGBoost – Gradient boosting model
- LightGBM – Light-weight gradient boosting
- Ridge Regression – Meta-learner for model stacking
- Optuna – Hyperparameter tuning
- scikit-learn – Data splitting, evaluation, and scaling
- Joblib – Model serialization

### 📊 Data Handling :
- Pandas – Data wrangling and feature engineering
- NumPy – Numerical operations

### 🌤️ Web Scraping & External Data :
- Selenium – Scraping SLDC data (DISCOM loads)
- BeautifulSoup – Parsing holiday information from web
- Meteostat – Fetching weather data (temperature, wind, precipitation)
- Requests – HTTP calls to fetch holiday data

### 📈 Visualization :
- Matplotlib – Error plots and performance graphs

### 🧾 File Formats & Storage :
- Excel (.xlsx) – Dataset output from scraper (better_data_1.xlsx)
- Pickle (.pkl) – Trained model storage (model_2.pkl)

---

## 📦 Requirements :
- xgboost
- lightgbm
- optuna
- pandas
- numpy
- scikit-learn
- matplotlib
- openpyxl
- selenium
- bs4
- meteostat
- Flask
- xlsxwriter

---

## 👤 Author :
This project was developed by Sarvagya Dwivedi and Team Load Logix AI as part of a personal learning initiative.







