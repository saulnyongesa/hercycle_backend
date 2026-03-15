import joblib
import os
import numpy as np

# Load the brain
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'anemia_model.pkl')

try:
    anemia_model = joblib.load(model_path)
except:
    anemia_model = None

def analyze_health_data(cycles, symptoms):
    if not anemia_model:
        return {"anemia_risk": "Low", "insights": ["System in standby."]}

    # 1. Feature Extraction
    flow_map = {'Light': 1, 'Medium': 2, 'Heavy': 3}
    recent_flow = flow_map.get(cycles[0].flow_intensity, 2) if cycles else 2
    
    symp_types = [s.symptom_type.lower() for s in symptoms[:10]]
    fatigue = 1 if 'fatigue' in symp_types else 0
    dizziness = 1 if 'dizziness' in symp_types else 0
    pale_skin = 1 if 'pale skin' in symp_types else 0
    
    cycle_len = 28
    if len(cycles) >= 2:
        delta = cycles[0].start_date - cycles[1].start_date
        cycle_len = abs(delta.days) # Use absolute to prevent negative lengths

    # 2. SEND AS NUMPY ARRAY (Fixes the ValueError)
    # The order must match: flow, fatigue, dizziness, pale_skin, cycle_len
    features = np.array([[recent_flow, fatigue, dizziness, pale_skin, cycle_len]])

    # 3. Predict
    try:
        prediction = anemia_model.predict(features)[0]
    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return {"anemia_risk": "Unknown", "insights": ["Analysis engine error."]}
    
    risk_map = {0: 'Low', 1: 'Moderate', 2: 'High'}
    risk = risk_map.get(prediction, 'Low')

    # Insights
    insights = []
    if risk == 'High':
        insights = ["High Risk: Heavy flow + clinical symptoms.", "Clinical referral is strongly advised."]
    elif risk == 'Moderate':
        insights = ["Warning: Pattern suggests early iron deficiency.", "Increase consumption of iron-rich foods."]
    else:
        insights = ["Status normal. Adolescent should keep logging."]

    return {"anemia_risk": risk, "insights": insights}