import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv("speed_data.csv")  # assume columns: time, location_id, avg_speed

# Features and target
X = df[['time', 'location_id']]
y = df['avg_speed']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = xgb.XGBRegressor()
model.fit(X_train, y_train)

# Save model
model.save_model("speed_predictor.json")

print("Model trained and saved as speed_predictor.json")
