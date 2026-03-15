import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def create_high_accuracy_dataset(n=50000):
    np.random.seed(42)
    
    # 1. Base Features
    flow = np.random.choice([1, 2, 3], n, p=[0.25, 0.50, 0.25])
    fatigue = np.random.choice([0, 1], n, p=[0.75, 0.25])
    dizziness = np.random.choice([0, 1], n, p=[0.85, 0.15])
    pale_skin = np.random.choice([0, 1], n, p=[0.92, 0.08])
    cycle_len = np.random.randint(21, 40, n) # Longer range
    
    # 2. Advanced Scoring Logic (Adding weighted noise)
    # Some people are naturally more resilient; others more sensitive.
    resilience_factor = np.random.normal(0, 1, n) 
    
    risk = []
    for i in range(n):
        # Calculate base risk score
        score = (flow[i] * 2.0) + (fatigue[i] * 2.5) + (dizziness[i] * 2.5) + (pale_skin[i] * 4.0)
        
        # Short cycles (frequent bleeding) increase risk
        if cycle_len[i] < 24:
            score += 1.5
            
        # Add random biological variance
        score += resilience_factor[i]
        
        # Assign Classes
        if score > 9.5: risk.append(2)    # High
        elif score > 5.5: risk.append(1)  # Moderate
        else: risk.append(0)              # Low
            
    return pd.DataFrame({
        'flow': flow, 'fatigue': fatigue, 'dizziness': dizziness, 
        'pale_skin': pale_skin, 'cycle_len': cycle_len, 'risk': risk
    })

# --- Execution ---
print("Generating high-variance dataset...")
df = create_high_accuracy_dataset()

X = df.drop('risk', axis=1).values
y = df['risk'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Using more estimators and limited depth to prevent overfitting
model = RandomForestClassifier(
    n_estimators=200, 
    max_depth=12, 
    min_samples_split=5,
    random_state=42
)

print("Training model...")
model.fit(X_train, y_train)

# --- Evaluation ---
y_pred = model.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nDetailed Report:\n", classification_report(y_test, y_pred))

# Save
joblib.dump(model, 'anemia_model.pkl')
print("Optimized model saved.")