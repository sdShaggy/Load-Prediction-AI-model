import optuna
import xgboost as xgb
from xgboost import XGBRegressor
import lightgbm as lgb
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import root_mean_squared_error,mean_absolute_error
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

df = pd.read_excel('better_data_1.xlsx', parse_dates=['date'])

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
TARGET_COL = 'tomorrow peak load'

X = df[FEATURE_COLS].values
y = df[TARGET_COL].values

split_id = int(len(X) * 0.8)
X_train, X_test = X[:split_id], X[split_id:]
y_train, y_test = y[:split_id], y[split_id:]

scaler = StandardScaler()
X_train_df = pd.DataFrame(X_train, columns=FEATURE_COLS)
X_train = scaler.fit_transform(X_train_df)
X_test = scaler.transform(X_test)

def objective(trial):
    params = {
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15),
        'n_estimators': 200,
        'max_depth': trial.suggest_int('max_depth', 3, 8),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'subsample': trial.suggest_float('subsample', 0.7, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 2.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 1.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 1.0, log=True),
        'random_state': 42,
        'objective': 'reg:squarederror',
        'tree_method': 'hist',
        'verbosity': 0
    }

    tss = TimeSeriesSplit(n_splits=5)
    rmses = []

    for train_id, val_id in tss.split(X_train):
        X_tr, X_val = X_train[train_id], X_train[val_id]
        y_tr, y_val = y_train[train_id], y_train[val_id]

        model = XGBRegressor(**params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        preds = model.predict(X_val)
        rmse = root_mean_squared_error(y_val, preds)
        rmses.append(rmse)

    return np.mean(rmses)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100, timeout=3600)

print("Best parameters:", study.best_params)
print("best CV rmse:", study.best_value)

best_params = study.best_params.copy()
best_params.update({
    'objective': 'reg:squarederror',
    'tree_method': 'hist',
    'random_state': 42,
    'verbosity': 0,
    'n_estimators': 300  
})

early_stopping_rounds = 50

final_model = XGBRegressor(**best_params)
final_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], 
                early_stopping_rounds=early_stopping_rounds, verbose=True)

y_pred_xgb = final_model.predict(X_test)
xgb_rmse = root_mean_squared_error(y_test, y_pred_xgb)
print(f"xgboost rmse : {xgb_rmse:.2f}")

lgb_train = lgb.Dataset(X_train, y_train)
params_lgb = {
    'objective': 'regression',
    'metric': 'rmse',
    'verbosity': -1,
    'boosting_type': 'gbdt',
    'random_state': 42,
    'learning_rate': 0.05,
    'num_leaves': 31,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
}

lgb_model = lgb.train(params_lgb, lgb_train, num_boost_round=500)
y_pred_lgb = lgb_model.predict(X_test)

stacked_features = np.vstack([y_pred_xgb, y_pred_lgb]).T
meta_model = Ridge(alpha=1.0)
meta_model.fit(stacked_features, y_test)
stacked_preds = meta_model.predict(stacked_features)
stacked_mae = mean_absolute_error(y_test, stacked_preds)
stacked_rmse = root_mean_squared_error(y_test, stacked_preds)
print(f"stacked rmse : {stacked_rmse:.2f}")
print(f"stacked MAE : {stacked_mae:.2f} ")

joblib.dump({
    'xgb': final_model,
    'lgb': lgb_model,
    'meta': meta_model,
    'scaler': scaler
}, 'model_2.pkl')
print("models saved to model_2.pkl")
