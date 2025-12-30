# Formulas and Sources for Gas Breakdown Calculation

## Overview
This document describes the formulas and scientific sources used to calculate the breakdown of CO₂, CH₄, and N₂O contributions to total CO₂e emissions.

---

## 1. CO₂ Equivalent (CO₂e) Formula

### Formula:
```
CO₂e_total = CO₂_mass + (CH₄_mass × GWP_CH₄) + (N₂O_mass × GWP_N₂O)
```

### Where:
- **CO₂_mass**: Mass of CO₂ in kilograms
- **CH₄_mass**: Mass of CH₄ in kilograms  
- **N₂O_mass**: Mass of N₂O in kilograms
- **GWP_CH₄**: Global Warming Potential of CH₄ = 28
- **GWP_N₂O**: Global Warming Potential of N₂O = 298

### Source:
**IPCC Fifth Assessment Report (AR5), 2013**
- Report: Climate Change 2013: The Physical Science Basis
- Working Group I Contribution
- Chapter 8: Anthropogenic and Natural Radiative Forcing
- Table 8.7: Global Warming Potentials (GWP)

**Citation:**
```
Myhre, G., et al. (2013). "Anthropogenic and Natural Radiative Forcing." 
In: Climate Change 2013: The Physical Science Basis. Contribution of 
Working Group I to the Fifth Assessment Report of the Intergovernmental 
Panel on Climate Change. Cambridge University Press, Cambridge, UK and 
New York, NY, USA.
```

**URL:** https://www.ipcc.ch/report/ar5/wg1/

### GWP Values Used:
- **CO₂**: GWP = 1 (baseline, by definition)
- **CH₄**: GWP = 28 (100-year time horizon, without climate-carbon feedbacks)
- **N₂O**: GWP = 298 (100-year time horizon, without climate-carbon feedbacks)

**Note:** These values represent the warming impact over a 100-year period relative to CO₂.

---

## 2. Treatment Emissions Calculation

### Formula:
```
Gas_mass (kg) = Emission_Factor (kg gas/kg waste) × Quantity (kg waste)
```

This is applied separately for each gas (CO₂, CH₄, N₂O).

### Current Status:
⚠️ **IMPORTANT**: The emission factors currently in the code are **ESTIMATED/PLACEHOLDER VALUES**.

### Recommended Sources for Emission Factors:

#### A. IPCC Guidelines
- **IPCC 2006 Guidelines for National Greenhouse Gas Inventories**
- Volume 5: Waste
- Chapter 6: Wastewater Treatment and Discharge
- **URL:** https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol5.html

#### B. EPA Emission Factors
- **EPA AP-42**: Compilation of Air Pollutant Emission Factors
- Contains emission factors for various industrial processes
- **URL:** https://www.epa.gov/air-emissions-factors-and-quantification/ap-42-compilation-air-emissions-factors

- **EPA GHG Emission Factors Hub**
- **URL:** https://www.epa.gov/climateleadership/ghg-emission-factors-hub

#### C. Scientific Literature
- Peer-reviewed journals on waste management:
  - Waste Management (Elsevier)
  - Journal of Cleaner Production (Elsevier)
  - Resources, Conservation and Recycling (Elsevier)
- Life Cycle Assessment (LCA) studies on waste treatment processes

#### D. LCA Databases
- Ecoinvent Database
- USLCI Database
- OpenLCA Nexus

---

## 3. Transport Emissions Calculation

### Formula:
```
Transport_CO₂e (kg) = Transport_Factor (kg CO₂e/km/ton) × Distance (km) × Quantity (tons)
```

### Gas Distribution in Transport Emissions:
Transport emissions from diesel/petrol vehicles are primarily CO₂ with small contributions from CH₄ and N₂O:
- **CO₂**: ~99% (complete combustion products)
- **CH₄**: ~0.8% (incomplete combustion)
- **N₂O**: ~0.2% (from catalytic converters and combustion processes)

### Sources:
1. **EPA MOVES Model** (Motor Vehicle Emission Simulator)
   - EPA's official model for estimating emissions from on-road vehicles
   - **URL:** https://www.epa.gov/moves

2. **GREET Model** (Greenhouse gases, Regulated Emissions, and Energy use in Transportation)
   - Argonne National Laboratory
   - **URL:** https://greet.es.anl.gov/

3. **IPCC Guidelines**
   - Volume 3: Industrial Processes and Product Use
   - Chapter 3: Mobile Combustion

---

## 4. Percentage Breakdown Calculation

### Formula:
```
Gas_Percentage (%) = (Gas_CO₂e / Total_CO₂e) × 100
```

Where `Gas_CO₂e` is the CO₂e contribution from a specific gas (CO₂, CH₄, or N₂O).

---

## 5. Implementation Approach

### Step-by-Step Process:

1. **Calculate Treatment Emissions:**
   - Use emission factors to calculate CO₂, CH₄, and N₂O masses from treatment
   - Convert to CO₂e using GWP values

2. **Calculate Transport Emissions:**
   - Estimate total transport CO₂e based on distance, quantity, and vehicle type
   - Distribute across gases using typical ratios

3. **Combine Contributions:**
   - Sum treatment and transport CO₂e for each gas
   - Scale to match the model's predicted total (accounts for other factors)

4. **Calculate Percentages:**
   - Calculate each gas's percentage contribution to total CO₂e

---

## 6. Recommendations for Improvement

### Immediate Actions:
1. ✅ Replace placeholder emission factors with validated values from EPA/IPCC sources
2. ✅ Document specific sources for each emission factor
3. ✅ Add uncertainty ranges if available from sources
4. ✅ Validate calculations against published case studies

### Future Enhancements:
1. Allow user to select different GWP time horizons (20-year, 100-year)
2. Consider AR6 GWP values (2021): CH₄ = 29.8, N₂O = 273
3. Include uncertainty quantification in the results
4. Add country-specific emission factors where applicable

---

## 7. References

### Primary Sources:
1. IPCC AR5 (2013). Climate Change 2013: The Physical Science Basis. Cambridge University Press.
2. IPCC (2006). 2006 IPCC Guidelines for National Greenhouse Gas Inventories. IGES, Japan.
3. US EPA. AP-42: Compilation of Air Pollutant Emission Factors.
4. US EPA. MOVES (Motor Vehicle Emission Simulator) Model.

### Additional Resources:
- EPA GHG Emission Factors Hub
- GREET Model (Argonne National Laboratory)
- Ecoinvent Database
- IPCC AR6 (2021) for updated GWP values (optional)

---

**Last Updated:** 2024
**Code Location:** `app.py` - `calculate_gas_breakdown()` function

