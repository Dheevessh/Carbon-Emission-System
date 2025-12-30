"""
Flask Web Application for Carbon Emission Prediction
====================================================
Simple web interface for predicting total carbon emissions
based on waste and transport details.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import os
import numpy as np

app = Flask(__name__)

# =============================================================================
# GLOBAL WARMING POTENTIALS (GWP) - IPCC AR5 (2013)
# Source: IPCC Fifth Assessment Report (AR5), Working Group I, Chapter 8
# https://www.ipcc.ch/report/ar5/wg1/
# =============================================================================
# GWP values represent the relative warming impact of a gas compared to CO2
# over a 100-year time horizon
GWP_CH4 = 28   # CH4 GWP = 28 (without climate-carbon feedbacks)
               # CH4 GWP = 34 (with climate-carbon feedbacks) - using conservative value
GWP_N2O = 298  # N2O GWP = 298 (without climate-carbon feedbacks)
               # N2O GWP = 298 (with climate-carbon feedbacks)

# =============================================================================
# EMISSION FACTORS (kg gas per kg waste)
# NOTE: These are currently ESTIMATED/PLACEHOLDER values
# TODO: Replace with validated emission factors from:
#   - EPA Emission Factor Database
#   - IPCC Guidelines for National Greenhouse Gas Inventories
#   - Peer-reviewed literature specific to waste treatment processes
#   - Life Cycle Assessment (LCA) databases
# =============================================================================
# Formula for treatment emissions:
#   Gas_mass (kg) = Emission_Factor (kg gas/kg waste) × Quantity (kg waste)
#
# Sources for emission factors should include:
#   - EPA AP-42: Compilation of Air Pollutant Emission Factors
#   - IPCC 2006 Guidelines: Wastewater Treatment and Discharge (Chapter 6)
#   - Journal articles on waste treatment emissions (e.g., Waste Management)
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

# Load the trained model
MODEL_PATH = 'carbon_emission_model.pkl'

def load_model():
    """Load the trained model pipeline."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def calculate_gas_breakdown(waste_type, treatment_method, quantity_tons, transport_distance_km, vehicle_type, total_co2e):
    """
    Calculate CO2, CH4, and N2O breakdown from total CO2e using emission factors.
    
    FORMULAS USED:
    ==============
    
    1. CO2 Equivalent (CO2e) Calculation (IPCC Standard Formula):
       -----------------------------------------------------------
       CO2e_total = CO2_mass + (CH4_mass × GWP_CH4) + (N2O_mass × GWP_N2O)
       
       Where:
       - CO2_mass: mass of CO2 in kg
       - CH4_mass: mass of CH4 in kg
       - N2O_mass: mass of N2O in kg
       - GWP_CH4 = 28 (IPCC AR5)
       - GWP_N2O = 298 (IPCC AR5)
    
    2. Treatment Gas Emissions:
       ------------------------
       Gas_mass (kg) = Emission_Factor (kg gas/kg waste) × Quantity (kg waste)
       
       Applied separately for CO2, CH4, and N2O using specific emission factors
       for each waste_type and treatment_method combination.
    
    3. Transport Emissions:
       --------------------
       Transport_CO2e (kg) = Transport_Factor (kg CO2e/km/ton) × Distance (km) × Quantity (tons)
       
       Transport emissions are primarily CO2 (99%), with small CH4 (0.8%) and N2O (0.2%)
       contributions from incomplete fuel combustion.
    
    4. Percentage Calculation:
       -----------------------
       Gas_Percentage (%) = (Gas_CO2e / Total_CO2e) × 100
    
    SOURCES:
    ========
    
    GWP Values:
    - IPCC AR5 (2013): Climate Change 2013: The Physical Science Basis
      Chapter 8: Anthropogenic and Natural Radiative Forcing
      Table 8.7: Global Warming Potentials (GWP)
      https://www.ipcc.ch/report/ar5/wg1/
    
    Emission Factors:
    - Currently using estimated values - REPLACE with:
      * EPA AP-42: Compilation of Air Pollutant Emission Factors
        https://www.epa.gov/air-emissions-factors-and-quantification/ap-42-compilation-air-emissions-factors
      * IPCC 2006 Guidelines for National Greenhouse Gas Inventories
        Volume 5: Waste - Chapter 6: Wastewater Treatment and Discharge
        https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol5.html
      * EPA GHG Emission Factors Hub
        https://www.epa.gov/climateleadership/ghg-emission-factors-hub
    
    Transport Factors:
    - EPA MOVES (Motor Vehicle Emission Simulator) model
    - GREET Model (Argonne National Laboratory)
    - Default factors approximate typical diesel truck emissions
    
    Uses IPCC AR5 Global Warming Potentials (GWP):
    - CO2: GWP = 1 (baseline)
    - CH4: GWP = 28 (over 100 years, without climate-carbon feedbacks)
    - N2O: GWP = 298 (over 100 years, without climate-carbon feedbacks)
    
    Parameters:
    -----------
    waste_type : str
        Type of waste (Sludge, Waste Oil, Water Waste)
    treatment_method : str
        Treatment method applied
    quantity_tons : float
        Quantity of waste in tons
    transport_distance_km : float
        Transport distance in km
    vehicle_type : str
        Type of vehicle used
    total_co2e : float
        Total CO2 equivalent emissions in kg CO2e (from model prediction)
    
    Returns:
    --------
    dict : Dictionary containing individual gas CO2e contributions and percentages
    """
    # Get treatment emission factors (kg gas per kg waste)
    factors = EMISSION_FACTORS.get(waste_type, {}).get(treatment_method, {})
    
    if not factors:
        # Default factors if combination not found
        factors = {'CO2': 0.020, 'CH4': 0.010, 'N2O': 0.005}
    
    # Convert quantity from tons to kg
    quantity_kg = quantity_tons * 1000
    
    # Calculate treatment-related individual gas masses (kg)
    treatment_co2_mass = factors['CO2'] * quantity_kg
    treatment_ch4_mass = factors['CH4'] * quantity_kg
    treatment_n2o_mass = factors['N2O'] * quantity_kg
    
    # Calculate treatment CO2e using IPCC GWP formula
    treatment_co2e_co2 = treatment_co2_mass * 1  # CO2 GWP = 1
    treatment_co2e_ch4 = treatment_ch4_mass * GWP_CH4  # CH4 GWP = 28
    treatment_co2e_n2o = treatment_n2o_mass * GWP_N2O  # N2O GWP = 298
    
    # Calculate total treatment CO2e
    treatment_co2e_total = treatment_co2e_co2 + treatment_co2e_ch4 + treatment_co2e_n2o
    
    # Estimate transport emissions (primarily CO2 from fuel combustion)
    # Transport emission factors (kg CO2e per km per ton) - approximate values
    transport_factors = {
        'Light Truck': 0.15,
        'Medium Truck': 0.25,
        'Heavy Truck': 0.40
    }
    transport_co2e_per_km_per_ton = transport_factors.get(vehicle_type, 0.25)
    
    # Calculate transport CO2e (primarily CO2, minimal CH4 and N2O from fuel combustion)
    transport_co2e = transport_co2e_per_km_per_ton * transport_distance_km * quantity_tons
    transport_co2e_co2 = transport_co2e * 0.99  # 99% CO2 from transport
    transport_co2e_ch4 = transport_co2e * 0.008  # ~0.8% CH4 from transport
    transport_co2e_n2o = transport_co2e * 0.002  # ~0.2% N2O from transport
    
    # Combine treatment and transport CO2e contributions
    total_co2e_co2 = treatment_co2e_co2 + transport_co2e_co2
    total_co2e_ch4 = treatment_co2e_ch4 + transport_co2e_ch4
    total_co2e_n2o = treatment_co2e_n2o + transport_co2e_n2o
    calculated_total_co2e = total_co2e_co2 + total_co2e_ch4 + total_co2e_n2o
    
    # Scale to match the model's predicted total (accounts for other factors)
    if calculated_total_co2e > 0:
        scale_factor = total_co2e / calculated_total_co2e
    else:
        scale_factor = 1.0
    
    # Final scaled CO2e contributions
    final_co2e_co2 = total_co2e_co2 * scale_factor
    final_co2e_ch4 = total_co2e_ch4 * scale_factor
    final_co2e_n2o = total_co2e_n2o * scale_factor
    
    # Calculate percentages of total CO2e
    if total_co2e > 0:
        pct_co2 = (final_co2e_co2 / total_co2e) * 100
        pct_ch4 = (final_co2e_ch4 / total_co2e) * 100
        pct_n2o = (final_co2e_n2o / total_co2e) * 100
    else:
        pct_co2 = pct_ch4 = pct_n2o = 0
    
    return {
        'co2': {
            'co2e_kg': round(final_co2e_co2, 2),
            'percentage': round(pct_co2, 2)
        },
        'ch4': {
            'co2e_kg': round(final_co2e_ch4, 2),
            'percentage': round(pct_ch4, 2)
        },
        'n2o': {
            'co2e_kg': round(final_co2e_n2o, 2),
            'percentage': round(pct_n2o, 2)
        },
        'total_co2e': round(total_co2e, 2)
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
        # Get form data (can be JSON or form data)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Extract input values (note: model was trained without transport_emission and treatment_emission)
        waste_type = data.get('waste_type')
        treatment_method = data.get('treatment_method')
        vehicle_type = data.get('vehicle_type')
        quantity_tons = float(data.get('quantity_tons', 0))
        transport_distance_km = float(data.get('transport_distance_km', 0))
        
        # Note: transport_emission_kgCO2e and treatment_emission_kgCO2e are collected 
        # from the form but not used in prediction (model was trained without them)
        # facility_efficiency_% is required by the model but not shown in the form (using default value)
        
        # Create DataFrame with correct column names and order matching training data
        input_data = pd.DataFrame({
            'waste_type': [waste_type],
            'treatment_method': [treatment_method],
            'quantity_tons': [quantity_tons],
            'vehicle_type': [vehicle_type],
            'transport_distance_km': [transport_distance_km],
            'facility_efficiency_%': [75.0]  # Default value since field is not in form
        })
        
        # Make prediction
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        prediction = model.predict(input_data)[0]
        
        # Calculate gas breakdown using IPCC GWP formula
        gas_breakdown = calculate_gas_breakdown(
            waste_type, treatment_method, quantity_tons, transport_distance_km, vehicle_type, prediction
        )
        
        # Return result with gas breakdown
        return jsonify({
            'success': True,
            'prediction': round(prediction, 2),
            'unit': 'kg CO₂e',
            'gas_breakdown': gas_breakdown
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

