import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split,GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

df = pd.read_excel('better_data.xlsx',index_col=None)

X = df.drop(columns=['tomorrow peak load','date'])

y = df['tomorrow peak load']

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

model = RandomForestRegressor(n_estimators=150,criterion='squared_error',random_state=42,max_depth=10,min_samples_leaf=2,min_samples_split=10)

model.fit(X_train,y_train)

y_pred = model.predict(X_test)

mse = mean_squared_error(y_test,y_pred)

print("Error = ",np.sqrt(mse))

joblib.dump(model,'loadpredai.pkl')
