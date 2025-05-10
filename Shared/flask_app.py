from flask import Flask, request, jsonify
import xgboost as xgb
import pandas as pd
import os

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "speed_predictor.json")

# Load model
model = xgb.XGBRegressor()
model.load_model(model_path)

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Speed Prediction API</h1>
    <p>To get a speed prediction, send a POST request to /predict_speed with JSON data:</p>
    <pre>
    {
        "time": 9,
        "location_id": 101
    }
    </pre>
    <p>Example using curl:</p>
    <pre>
    curl -X POST -H "Content-Type: application/json" -d '{"time": 9, "location_id": 101}' http://localhost:5000/predict_speed
    </pre>
    """

@app.route("/predict_speed", methods=["POST"])
def predict_speed():
    data = request.json  # Expecting {"time": 9, "location_id": 101}
    df = pd.DataFrame([data])
    pred = model.predict(df)
    return jsonify({'predicted_speed': float(pred[0])})

if __name__ == "__main__":
    app.run(debug=True)
