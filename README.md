# Carbon Emission Prediction Web Application

A simple Flask web application for predicting total carbon emissions based on waste and transport details.

## Files Structure

```
Full System/Official/
├── app.py                      # Flask backend application
├── carbon_emission_model.pkl   # Trained Random Forest model (needs to be copied here)
├── templates/
│   └── index.html             # Frontend HTML form
└── README.md                  # This file
```

## Prerequisites

Before running the application, make sure you have the following installed:

1. **Python 3.7 or higher**
2. **Required Python packages:**
   - Flask
   - pandas
   - scikit-learn
   - joblib
   - numpy

## Installation Steps

### Step 1: Install Required Packages

Open a terminal/command prompt and run:

```bash
pip install flask pandas scikit-learn joblib numpy
```

Or if you prefer using a requirements file, create `requirements.txt` with:

```
Flask>=2.0.0
pandas>=1.3.0
scikit-learn>=1.0.0
joblib>=1.0.0
numpy>=1.21.0
```

Then install with:
```bash
pip install -r requirements.txt
```

### Step 2: Copy Model File

Make sure the `carbon_emission_model.pkl` file is in the same directory as `app.py`. 

If the model file is in a different location, you have two options:

**Option A:** Copy the model file to `Full System/Official/` directory
```bash
# From the project root, copy the model file
copy "prediction model\Official\carbon_emission_model.pkl" "Full System\Official\carbon_emission_model.pkl"
```

**Option B:** Update the MODEL_PATH in `app.py` to point to the correct location
```python
MODEL_PATH = '../prediction model/Official/carbon_emission_model.pkl'
```

### Step 3: Run the Application

Navigate to the application directory:

```bash
cd "Full System\Official"
```

Then run the Flask application:

```bash
python app.py
```

You should see output similar to:
```
Model loaded successfully from carbon_emission_model.pkl
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

### Step 4: Access the Web Application

Open your web browser and navigate to:

```
http://localhost:5000
```

or

```
http://127.0.0.1:5000
```

## Usage

1. Fill in the form fields:
   - **Waste Type** (required): Select from Sludge, Waste Oil, or Water Waste
   - **Treatment Method** (required): Select from Physical, Chemical, Biological, Pre-Treatment, or Dewatering
   - **Vehicle Type** (required): Select from Light Truck, Medium Truck, or Heavy Truck
   - **Quantity** (required): Enter the waste quantity in tons
   - **Transport Distance** (required): Enter the transport distance in kilometers
   - **Facility Efficiency** (required): Enter the facility efficiency percentage (0-100)
   - **Transport Emission** (optional): Enter transport emission in kg CO₂e
   - **Treatment Emission** (optional): Enter treatment emission in kg CO₂e

2. Click the "Predict Total Emission" button

3. The predicted total carbon emission will be displayed below the form in kg CO₂e

## Troubleshooting

### Error: "Model file not found"
- Make sure `carbon_emission_model.pkl` is in the same directory as `app.py`
- Check the file path in `app.py` if the model is in a different location

### Error: "Module not found"
- Install missing packages using `pip install <package-name>`
- Make sure you're using the correct Python environment

### Port already in use
- The default port is 5000. If it's already in use, you can change it in `app.py`:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to another port
  ```

## Stopping the Application

Press `CTRL+C` in the terminal where the Flask app is running to stop the server.

## Notes

- The model was trained without `transport_emission_kgCO2e` and `treatment_emission_kgCO2e` fields (to avoid data leakage), so these fields are collected from the form but not used in the prediction
- The application runs in debug mode by default, which is suitable for development but should be changed for production use
- Make sure all required fields are filled before submitting the form

