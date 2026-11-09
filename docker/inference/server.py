from flask import Flask, request, jsonify
import numpy as np
import joblib
import os
from datetime import datetime

app = Flask(__name__)

MODEL_PATH = "/app/models/wine_model.pkl"
LOG_PATH = "/app/logs/predictions.log"

model = None

# TODO: Load the trained model from the shared volume. Use joblib.load() with MODEL_PATH.
# Only load it if the file exists: if the volume is empty the server should still start,
# so /health can report "model not found" instead of the container crashing.
model = ...

# Wine feature names for reference (13 features):
# alcohol, malic_acid, ash, alcalinity_of_ash, magnesium, total_phenols,
# flavanoids, nonflavanoid_phenols, proanthocyanins, color_intensity,
# hue, od280/od315_of_diluted_wines, proline

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # TODO: Get the input array from the request JSON body
        # The request body should have a key "input" with a list of 13 feature values
        data = request.get_json()
        features = ...

        # TODO: Convert to numpy array, reshape for single prediction, and predict
        # HINT: use np.array().reshape(1, -1)
        prediction = ...

        # Map prediction to wine class name
        wine_classes = {0: "class_0", 1: "class_1", 2: "class_2"}
        result = wine_classes.get(int(prediction[0]), "unknown")

        # TODO: Log the prediction to the bind-mounted log file
        # Append a line to LOG_PATH with the timestamp, input features, and prediction result
        # Example log line: "2026-02-09 12:00:00 | input: [13.2, 1.78, ...] | prediction: class_0"


        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def hello():
    return 'Welcome to the Wine Classifier - MESW0023 Docker lab'

@app.route('/health')
def health():
    global model
    model_exists = os.path.exists(MODEL_PATH)
    return jsonify({
        "status": "healthy" if model_exists else "model not found",
        "model_loaded": model is not None
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
