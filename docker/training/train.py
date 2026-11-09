from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

# Load the Wine dataset
wine = load_wine()
X, y = wine.data, wine.target

# Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# TODO: Create a RandomForestClassifier and train it on the training data
clf = ...
clf.fit(...)

# Evaluate on test set
y_pred = clf.predict(X_test)
print(f"Training complete. Test accuracy: {accuracy_score(y_test, y_pred):.4f}")

# TODO: Save the trained model to the shared volume
model_dir = "/app/models"
os.makedirs(model_dir, exist_ok=True)

joblib.dump(...)

print("Model saved to /app/models/wine_model.pkl")
