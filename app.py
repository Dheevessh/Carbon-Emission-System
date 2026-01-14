"""
Flask Web Application for Carbon Emission Prediction
====================================================
Simple web interface for predicting total carbon emissions
based on waste and operational details.

NOTE:
- This version EXCLUDES any explicit transport-emission calculation.
- The model may still use transport-related inputs as features, but the
  gas breakdown is computed without any transport-emission component.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import os
import numpy as np
import re

app = Flask(__name__)

# =============================================================================
# GLOBAL WARMING POTENTIALS (GWP) - 100-year horizon
# =============================================================================
# CO2 baseline GWP = 1
GWP_CH4 = 28
GWP_N2O = 298

# =============================================================================
# EMISSION FACTORS (kg gas per kg waste) - treatment-related only
# NOTE: These are estimated/placeholder values and should be replaced
# with validated factors aligned to the organisation’s reporting basis.
# =============================================================================
EMISSION_FACTORS = {
    'Sludge': {
        'Physical': {'CO2': 0.015, 'CH4': 0.008, 'N2O': 0.001},
        'Chemical': {'CO2': 0.020, 'CH4': 0.005, 'N2O': 0.002},
        'Biological': {'CO2': 0.025, 'CH4': 0.015, 'N2O': 0.005},
        'Pre-Treatment': {'CO2': 0.018, 'CH4': 0.006, 'N2O': 0.001},
        'Dewatering': {'CO2': 0.030, 'CH4': 0.030, 'N2O': 0.018}
    },
    'Waste Oil': {
        'Physical': {'CO2': 0.050, 'CH4': 0.001, 'N2O': 0.0001},
        'Chemical': {'CO2': 0.085, 'CH4': 0.0, 'N2O': 0.0},
        'Biological': {'CO2': 0.040, 'CH4': 0.002, 'N2O': 0.0005},
        'Pre-Treatment': {'CO2': 0.085, 'CH4': 0.0, 'N2O': 0.0},
        'Dewatering': {'CO2': 0.045, 'CH4': 0.001, 'N2O': 0.0002}
    },
    'Water Waste': {
        'Physical': {'CO2': 0.006, 'CH4': 0.003, 'N2O': 0.001},
        'Chemical': {'CO2': 0.020, 'CH4': 0.005, 'N2O': 0.005},
        'Biological': {'CO2': 0.020, 'CH4': 0.020, 'N2O': 0.010},
        'Pre-Treatment': {'CO2': 0.010, 'CH4': 0.004, 'N2O': 0.002},
        'Dewatering': {'CO2': 0.008, 'CH4': 0.006, 'N2O': 0.003}
    }
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'carbon_emission_model.pkl')


def load_model():
    """Load the trained model pipeline."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def _safe_predict(pipeline, input_df: pd.DataFrame) -> float:
    """
    Run prediction and auto-fill any missing required columns with default values.
    This helps if the saved pipeline expects extra columns (e.g., from prior experiments).
    """
    df = input_df.copy()

    for _ in range(4):
        try:
            return float(pipeline.predict(df)[0])
        except Exception as e:
            msg = str(e)
            missing = set()

            m1 = re.search(r"columns are missing: \{([^}]*)\}", msg)
            if m1:
                raw = m1.group(1)
                for part in raw.split(","):
                    name = part.strip().strip("'").strip('"')
                    if name:
                        missing.add(name)

            m2 = re.search(r"now missing:\s*\[([^\]]*)\]", msg)
            if m2:
                raw = m2.group(1)
                for part in raw.split(","):
                    name = part.strip().strip("'").strip('"')
                    if name:
                        missing.add(name)

            if not missing:
                raise

            for col in missing:
                if col not in df.columns:
                    df[col] = 0.0

    return float(pipeline.predict(df)[0])


def calculate_gas_breakdown(waste_type, treatment_method, quantity_tons, total_co2e, extra_treatment_co2e=0.0):
    """
    Compute CO2, CH4, and N2O contributions (in kg CO2e) for interpretability.

    This breakdown excludes any explicit transport-emission computation.

    Steps:
    1) Estimate treatment-related gas masses using emission factors:
       m_gas (kg) = EF_gas (kg gas/kg waste) × Q_kg (kg waste)

    2) Convert gas masses to CO2e:
       CO2e = CO2 + (CH4 × GWP_CH4) + (N2O × GWP_N2O)

    3) Add optional user-provided treatment adjustment (kg CO2e) to CO2 share.

    4) Scale contributions so their sum matches the model’s total CO2e.
    """
    factors = EMISSION_FACTORS.get(waste_type, {}).get(treatment_method, {})
    if not factors:
        factors = {'CO2': 0.020, 'CH4': 0.010, 'N2O': 0.005}

    # Convert quantity from tons to kg
    quantity_kg = float(quantity_tons) * 1000.0

    # Treatment-related gas masses (kg)
    treatment_co2_mass = float(factors.get('CO2', 0.0)) * quantity_kg
    treatment_ch4_mass = float(factors.get('CH4', 0.0)) * quantity_kg
    treatment_n2o_mass = float(factors.get('N2O', 0.0)) * quantity_kg

    # Convert to CO2e contributions
    raw_co2e_co2 = treatment_co2_mass * 1.0
    raw_co2e_ch4 = treatment_ch4_mass * float(GWP_CH4)
    raw_co2e_n2o = treatment_n2o_mass * float(GWP_N2O)

    # Optional adjustment: add user-provided treatment CO2e to CO2 share
    try:
        extra_treatment_co2e = float(extra_treatment_co2e or 0.0)
    except Exception:
        extra_treatment_co2e = 0.0
    if extra_treatment_co2e < 0:
        extra_treatment_co2e = 0.0

    raw_co2e_co2 += extra_treatment_co2e

    raw_total = raw_co2e_co2 + raw_co2e_ch4 + raw_co2e_n2o
    if raw_total > 0:
        scale_factor = float(total_co2e) / raw_total
    else:
        scale_factor = 1.0

    final_co2e_co2 = raw_co2e_co2 * scale_factor
    final_co2e_ch4 = raw_co2e_ch4 * scale_factor
    final_co2e_n2o = raw_co2e_n2o * scale_factor

    if float(total_co2e) > 0:
        pct_co2 = (final_co2e_co2 / float(total_co2e)) * 100.0
        pct_ch4 = (final_co2e_ch4 / float(total_co2e)) * 100.0
        pct_n2o = (final_co2e_n2o / float(total_co2e)) * 100.0
    else:
        pct_co2 = pct_ch4 = pct_n2o = 0.0

    return {
        'co2': {'co2e_kg': round(final_co2e_co2, 2), 'percentage': round(pct_co2, 2)},
        'ch4': {'co2e_kg': round(final_co2e_ch4, 2), 'percentage': round(pct_ch4, 2)},
        'n2o': {'co2e_kg': round(final_co2e_n2o, 2), 'percentage': round(pct_n2o, 2)},
        'total_co2e': round(float(total_co2e), 2)
    }


# Load model at startup
try:
    model = load_model()
    print(f"Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None


@app.route('/')
def index():
    """Render the main form page."""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Handle form submission and return prediction."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        waste_type = (data.get('waste_type') or '').strip()
        treatment_method = (data.get('treatment_method') or '').strip()
        vehicle_type = (data.get('vehicle_type') or '').strip()  # still allowed as a model feature
        quantity_tons_raw = data.get('quantity_tons', '')
        transport_distance_raw = data.get('transport_distance_km', '')  # still allowed as a model feature

        # Optional: user-provided treatment emissions (kg CO2e)
        treatment_emission_raw = data.get('treatment_emission_kgCO2e', '')

        if not waste_type:
            return jsonify({'success': False, 'error': 'Waste type is required.'}), 400
        if not treatment_method:
            return jsonify({'success': False, 'error': 'Treatment method is required.'}), 400

        try:
            quantity_tons = float(quantity_tons_raw)
        except Exception:
            return jsonify({'success': False, 'error': 'Quantity (tons) must be a valid number.'}), 400

        try:
            transport_distance_km = float(transport_distance_raw)
        except Exception:
            return jsonify({'success': False, 'error': 'Transport distance (km) must be a valid number.'}), 400

        if quantity_tons < 0 or transport_distance_km < 0:
            return jsonify({'success': False, 'error': 'Quantity and distance must be non-negative.'}), 400

        try:
            treatment_emission_kgco2e = float(treatment_emission_raw) if str(treatment_emission_raw).strip() != '' else 0.0
        except Exception:
            return jsonify({'success': False, 'error': 'Treatment emission must be a valid number.'}), 400

        if treatment_emission_kgco2e < 0:
            return jsonify({'success': False, 'error': 'Treatment emission must be non-negative.'}), 400

        # Model input (aligned with trained features)
        input_data = pd.DataFrame({
            'waste_type': [waste_type],
            'treatment_method': [treatment_method],
            'vehicle_type': [vehicle_type if vehicle_type else 'Unknown'],
            'quantity_tons': [quantity_tons],
            'transport_distance_km': [transport_distance_km],
        })

        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500

        predicted_total = _safe_predict(model, input_data)

        # Incorporate user-provided treatment emissions into the final total
        final_total = float(predicted_total) + float(treatment_emission_kgco2e)

        # Gas breakdown (no transport-emission calculation)
        gas_breakdown = calculate_gas_breakdown(
            waste_type=waste_type,
            treatment_method=treatment_method,
            quantity_tons=quantity_tons,
            total_co2e=final_total,
            extra_treatment_co2e=treatment_emission_kgco2e
        )

        return jsonify({
            'success': True,
            'prediction': round(final_total, 2),
            'unit': 'kg CO₂e',
            'gas_breakdown': gas_breakdown
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
