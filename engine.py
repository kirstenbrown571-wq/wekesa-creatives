"""
TERRA Carbon Calculation Engine
Emission factors sourced from:
  - IPCC AR6 (2021)
  - IEA Emission Factors 2023
  - Kenya Power Grid Emission Factor (KPLC, 2023): 0.233 kgCO2/kWh
  - GHG Protocol Corporate Standard
"""

GRID_FACTORS = {
    "Kenya":        0.233,
    "Nigeria":      0.430,
    "South Africa": 0.928,
    "Ghana":        0.284,
    "Ethiopia":     0.013,
    "United Kingdom":0.193,
    "Germany":      0.366,
    "France":       0.052,
    "United States":0.386,
    "India":        0.708,
    "Other":        0.350,
}

ROADMAP_ACTIONS = [
    {
        "title": "Switch to 100% renewable electricity",
        "description": "Source electricity from solar/wind PPA or install rooftop solar.",
        "scope": "Scope 2",
        "reduction_pct": 30,
        "capex": 15000,
        "annual_saving": 18000,
        "payback_years": 0.8,
        "difficulty": "Medium",
    },
    {
        "title": "Electrify vehicle fleet (EVs / e-bikes)",
        "description": "Replace petrol/diesel fleet vehicles with electric alternatives.",
        "scope": "Scope 1",
        "reduction_pct": 18,
        "capex": 40000,
        "annual_saving": 22000,
        "payback_years": 1.8,
        "difficulty": "Medium",
    },
    {
        "title": "Remote-first travel policy",
        "description": "Replace >70% of flights with video conferencing.",
        "scope": "Scope 3",
        "reduction_pct": 12,
        "capex": 500,
        "annual_saving": 9500,
        "payback_years": 0.05,
        "difficulty": "Easy",
    },
    {
        "title": "LED lighting + smart HVAC",
        "description": "Upgrade lighting to LED and install smart building management.",
        "scope": "Scope 2",
        "reduction_pct": 7,
        "capex": 8000,
        "annual_saving": 14000,
        "payback_years": 0.57,
        "difficulty": "Easy",
    },
    {
        "title": "Supplier sustainability programme",
        "description": "Engage top 10 suppliers to measure and reduce their emissions.",
        "scope": "Scope 3",
        "reduction_pct": 10,
        "capex": 3000,
        "annual_saving": 5000,
        "payback_years": 0.6,
        "difficulty": "Hard",
    },
    {
        "title": "Waste reduction + circular economy",
        "description": "Divert 80% of waste from landfill, implement composting.",
        "scope": "Scope 3",
        "reduction_pct": 4,
        "capex": 2000,
        "annual_saving": 4000,
        "payback_years": 0.5,
        "difficulty": "Easy",
    },
    {
        "title": "Green procurement policy",
        "description": "Mandate environmental criteria in all procurement decisions.",
        "scope": "Scope 3",
        "reduction_pct": 8,
        "capex": 1000,
        "annual_saving": 3000,
        "payback_years": 0.33,
        "difficulty": "Medium",
    },
]


class CarbonEngine:

    def calculate(self, inputs: dict) -> dict:
        """
        Returns full emissions breakdown.
        All factors in kgCO2e, converted to tCO2e at end.
        """
        country  = inputs.get("country", "Kenya")
        grid_f   = GRID_FACTORS.get(country, 0.350)
        emp      = max(1, int(inputs.get("employees", 1)))

        # ── Scope 1 ──────────────────────────────────────────────
        # Natural gas: 2.040 kgCO2e / m³ (IPCC)
        gas_co2  = inputs.get("gas", 0) * 12 * 2.040

        # Diesel: 2.680 kgCO2e / litre
        diesel_co2 = inputs.get("diesel", 0) * 12 * 2.680

        # Fleet (average car: 0.171 kgCO2e / km)
        fleet_co2 = inputs.get("fleet_km", 0) * 12 * 0.000171 * 1000

        # Refrigerant leakage (already in kgCO2e)
        refrig_co2 = inputs.get("refrigerant", 0)

        scope1 = (gas_co2 + diesel_co2 + fleet_co2 + refrig_co2) / 1000

        # ── Scope 2 ──────────────────────────────────────────────
        # Electricity: grid emission factor
        elec_co2  = inputs.get("elec", 0) * 12 * grid_f

        # Steam / district heating: 0.27 kgCO2e / kWh
        steam_co2 = inputs.get("steam", 0) * 12 * 1000 * 0.270

        scope2 = (elec_co2 + steam_co2) / 1000

        # ── Scope 3 ──────────────────────────────────────────────
        # Flights: 0.255 kgCO2e/km, ~800 km/hr avg
        flights_co2 = inputs.get("flights", 0) * 800 * 0.255 * 2.7  # RFI multiplier

        # Supply chain: MRIO spend-based 0.30 kgCO2e per USD
        supply_co2  = inputs.get("supply", 0) * 12 * 1000 * 0.30

        # Waste: landfill 0.587 tCO2e per tonne (EPA)
        waste_co2   = inputs.get("waste", 0) * 12 * 587.0

        # Employee commute: avg car 0.171 kgCO2e/km, 220 working days
        commute_co2 = inputs.get("commute", 0) * 220 * 0.171

        scope3 = (flights_co2 + supply_co2 + waste_co2 + commute_co2) / 1000

        total  = round(scope1 + scope2 + scope3, 2)
        per_e  = round(total / emp, 2)

        # ESG score: inverse of intensity vs. global avg (8.5 t/emp)
        intensity_ratio = per_e / 8.5
        esg_raw = max(0, min(100, 100 - (intensity_ratio - 0.3) * 35))
        esg     = round(esg_raw)

        esg_msgs = {
            range(80, 101): "Outstanding. Top 10% globally. Green bond eligible.",
            range(65,  80): "Strong. Minor improvements will unlock A grade.",
            range(50,  65): "Average. Meeting minimum standards. Action needed.",
            range(35,  50): "Below average. Investor ESG screens may flag risk.",
            range(0,   35): "Critical. Immediate action required. Regulatory risk.",
        }
        esg_msg = next((v for r, v in esg_msgs.items() if esg in r),
                       "Calculating...")

        breakdown = {
            "Electricity": round(scope2 * elec_co2/(elec_co2+steam_co2+1e-9), 1),
            "Fleet/Diesel": round(scope1 * (diesel_co2+fleet_co2)/(gas_co2+diesel_co2+fleet_co2+refrig_co2+1e-9), 1),
            "Gas":          round(scope1 * gas_co2/(gas_co2+diesel_co2+fleet_co2+refrig_co2+1e-9), 1),
            "Flights":      round(flights_co2/1000, 1),
            "Supply chain": round(supply_co2/1000, 1),
        }

        return {
            "total":     total,
            "scope1":    round(scope1, 2),
            "scope2":    round(scope2, 2),
            "scope3":    round(scope3, 2),
            "per_emp":   per_e,
            "esg":       esg,
            "esg_msg":   esg_msg,
            "breakdown": breakdown,
            "country":   country,
            "grid_f":    grid_f,
        }

    def get_roadmap(self, results: dict) -> list:
        """Return actions sorted by CO2 reduction / capex ratio."""
        total = results['total']
        actions = []
        for a in ROADMAP_ACTIONS:
            co2_saved = round(total * a['reduction_pct'] / 100, 1)
            roi = a['annual_saving'] / max(a['capex'], 1)
            actions.append({
                **a,
                "co2_saved":     co2_saved,
                "roi":           round(roi, 2),
            })
        # Sort by CO2/capex efficiency
        return sorted(actions, key=lambda x: x['co2_saved'] / max(x['capex'], 1), reverse=True)