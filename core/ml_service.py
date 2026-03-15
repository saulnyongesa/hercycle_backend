def analyze_health_data(cycles, symptoms):
    """
    Analyzes historical cycle and symptom data to determine anemia risk.
    """
    # 1. Extract risk factors
    heavy_cycles = [c for c in cycles if c.flow_intensity.lower() == 'heavy']
    
    # Check for anemia-specific symptoms (fatigue, dizziness) with high severity
    critical_symptoms = [
        s for s in symptoms 
        if s.symptom_type.lower() in ['fatigue', 'dizziness', 'headache', 'pale skin'] 
        and s.severity >= 3
    ]

    # 2. Base Classification Logic
    risk_level = "Low"
    suggestions = ["Cycle patterns appear normal. Maintain a balanced diet."]

    if len(heavy_cycles) >= 2 and len(critical_symptoms) >= 1:
        risk_level = "High"
        suggestions = [
            "High risk of anemia detected due to recurring heavy flow and severe fatigue/dizziness.",
            "Recommend immediate iron supplements (e.g., IFAS).",
            "Refer the girl to the nearest health facility for a hemoglobin (Hb) test."
        ]
    elif len(heavy_cycles) >= 1 or len(critical_symptoms) >= 1:
        risk_level = "Moderate"
        suggestions = [
            "Moderate risk factors present. Monitor flow intensity closely next cycle.",
            "Advise increasing intake of iron-rich foods (spinach, beans, fortified cereals)."
        ]

    # 3. Return the payload
    return {
        "anemia_risk": risk_level,
        "insights": suggestions,
        "heavy_cycles_count": len(heavy_cycles),
        "critical_symptoms_count": len(critical_symptoms)
    }