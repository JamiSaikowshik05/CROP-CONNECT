"""
CropConnect — ML Training Script
Reads the 3 uploaded CSV files and trains models.

CSV files expected in ml_data/ folder:
  yield_data.csv
  fraud_data.csv
  quality_data.csv

Run: python train_models.py
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, mean_absolute_error,
                              classification_report)
import joblib

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'ml_data')
MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 60)
print("  CropConnect ML Training")
print("=" * 60)


# ─────────────────────────────────────────────────────────────
# MODEL 1 — CROP YIELD PREDICTOR
# File: yield_data.csv
# Columns used: crop, district, season, soil_type, land_area_acres,
#               annual_rainfall_mm, avg_temperature_c
# Target:       total_yield_qtl
# ─────────────────────────────────────────────────────────────
print("\n[1/3] Crop Yield Predictor")
print("-" * 40)

try:
    path = os.path.join(DATA_DIR, 'yield_data.csv')
    df   = pd.read_csv(path)
    print(f"  Loaded: {len(df)} rows")

    df = df.dropna(subset=['crop','district','season','soil_type',
                            'land_area_acres','annual_rainfall_mm',
                            'avg_temperature_c','total_yield_qtl'])

    # Build encoders from actual data
    crops     = sorted(df['crop'].unique().tolist())
    districts = sorted(df['district'].unique().tolist())
    seasons   = sorted(df['season'].unique().tolist())
    soils     = sorted(df['soil_type'].unique().tolist())

    crop_enc     = {c: i for i, c in enumerate(crops)}
    district_enc = {d: i for i, d in enumerate(districts)}
    season_enc   = {s: i for i, s in enumerate(seasons)}
    soil_enc     = {s: i for i, s in enumerate(soils)}

    df['crop_e']     = df['crop'].map(crop_enc)
    df['district_e'] = df['district'].map(district_enc)
    df['season_e']   = df['season'].map(season_enc)
    df['soil_e']     = df['soil_type'].map(soil_enc)

    features = ['crop_e', 'district_e', 'season_e', 'soil_e',
                 'land_area_acres', 'annual_rainfall_mm', 'avg_temperature_c']
    X = df[features]
    y = df['total_yield_qtl']

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=150, max_depth=12,
                                   random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)
    preds = model.predict(X_te)
    mae   = mean_absolute_error(y_te, preds)
    r2    = model.score(X_te, y_te)

    joblib.dump(model,        os.path.join(MODELS_DIR, 'yield_model.pkl'))
    joblib.dump(crop_enc,     os.path.join(MODELS_DIR, 'crop_enc.pkl'))
    joblib.dump(district_enc, os.path.join(MODELS_DIR, 'district_enc.pkl'))
    joblib.dump(season_enc,   os.path.join(MODELS_DIR, 'season_enc.pkl'))
    joblib.dump(soil_enc,     os.path.join(MODELS_DIR, 'soil_enc.pkl'))

    print(f"  ✅  Trained — MAE: {mae:.2f} qtl  |  R²: {r2:.3f}")
    print(f"  Crops: {crops}")
    print(f"  Districts: {len(districts)} districts")
    print(f"  Saved: yield_model.pkl + encoders")

except FileNotFoundError:
    print("  ❌  yield_data.csv not found in ml_data/")
except Exception as e:
    print(f"  ❌  Error: {e}")


# ─────────────────────────────────────────────────────────────
# MODEL 2 — FRAUD DETECTOR
# File: fraud_data.csv
# Columns: farmer_land_acres, booked_quantity_qtl,
#          quantity_per_acre, past_total_bookings,
#          past_approved_bookings, past_rejected_bookings,
#          qty_vs_avg_ratio, farmer_verified,
#          days_since_last_booking, aadhaar_bank_linked,
#          multiple_accounts_flag
# Target: is_fraudulent  (0=genuine, 1=fraud)
# ─────────────────────────────────────────────────────────────
print("\n[2/3] Fraud Detector")
print("-" * 40)

try:
    path = os.path.join(DATA_DIR, 'fraud_data.csv')
    df   = pd.read_csv(path)
    print(f"  Loaded: {len(df)} rows")

    features = ['farmer_land_acres', 'booked_quantity_qtl',
                 'quantity_per_acre', 'past_total_bookings',
                 'past_approved_bookings', 'past_rejected_bookings',
                 'qty_vs_avg_ratio', 'farmer_verified',
                 'days_since_last_booking', 'aadhaar_bank_linked',
                 'multiple_accounts_flag']

    df = df.dropna(subset=features + ['is_fraudulent'])
    print(f"  Genuine: {(df['is_fraudulent']==0).sum()}  |  "
          f"Fraudulent: {(df['is_fraudulent']==1).sum()}")

    X = df[features]
    y = df['is_fraudulent']

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                                random_state=42,
                                                stratify=y)

    model = GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                        learning_rate=0.08, random_state=42)
    model.fit(X_tr, y_tr)
    acc  = accuracy_score(y_te, model.predict(X_te))

    # Feature importance
    importances = sorted(zip(features, model.feature_importances_),
                          key=lambda x: x[1], reverse=True)

    joblib.dump(model, os.path.join(MODELS_DIR, 'fraud_model.pkl'))

    print(f"  ✅  Trained — Accuracy: {acc*100:.1f}%")
    print(f"  Top features: {importances[0][0]} ({importances[0][1]:.3f}), "
          f"{importances[1][0]} ({importances[1][1]:.3f})")
    print(f"  Saved: fraud_model.pkl")

except FileNotFoundError:
    print("  ❌  fraud_data.csv not found in ml_data/")
except Exception as e:
    print(f"  ❌  Error: {e}")


# ─────────────────────────────────────────────────────────────
# MODEL 3 — QUALITY GRADE PREDICTOR
# File: quality_data.csv
# Columns: crop, moisture_percent, foreign_matter_percent,
#          damaged_grains_percent, immature_grains_percent,
#          chalky_grains_percent, shelling_outturn_percent,
#          oil_content_percent, aflatoxin_detected
# Target: quality_grade  (FAQ / Below_FAQ / Rejected)
# ─────────────────────────────────────────────────────────────
print("\n[3/3] Quality Grade Predictor")
print("-" * 40)

try:
    path = os.path.join(DATA_DIR, 'quality_data.csv')
    df   = pd.read_csv(path)
    print(f"  Loaded: {len(df)} rows")

    features = ['crop_e', 'moisture_percent', 'foreign_matter_percent',
                 'damaged_grains_percent', 'immature_grains_percent',
                 'chalky_grains_percent', 'shelling_outturn_percent',
                 'oil_content_percent', 'aflatoxin_detected']

    grade_map    = {'FAQ': 0, 'Below_FAQ': 1, 'Rejected': 2}
    grade_labels = {0: 'FAQ', 1: 'Below_FAQ', 2: 'Rejected'}

    df['crop_e']   = df['crop'].map({'Paddy': 0, 'Groundnut': 1}).fillna(0)
    df['grade_e']  = df['quality_grade'].map(grade_map)
    df = df.dropna(subset=features + ['grade_e'])

    print(f"  FAQ: {(df['grade_e']==0).sum()}  |  "
          f"Below FAQ: {(df['grade_e']==1).sum()}  |  "
          f"Rejected: {(df['grade_e']==2).sum()}")

    X = df[features]
    y = df['grade_e'].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                                random_state=42,
                                                stratify=y)

    model = DecisionTreeClassifier(max_depth=10, min_samples_leaf=8,
                                    random_state=42)
    model.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te))

    joblib.dump(model,        os.path.join(MODELS_DIR, 'quality_model.pkl'))
    joblib.dump(grade_labels, os.path.join(MODELS_DIR, 'grade_labels.pkl'))

    print(f"  ✅  Trained — Accuracy: {acc*100:.1f}%")
    print(f"  Saved: quality_model.pkl")

except FileNotFoundError:
    print("  ❌  quality_data.csv not found in ml_data/")
except Exception as e:
    print(f"  ❌  Error: {e}")


# ── Summary ──────────────────────────────────────────────────
print("\n" + "=" * 60)
saved = [f for f in os.listdir(MODELS_DIR) if f.endswith('.pkl')]
print(f"  ✅  {len(saved)} model files saved in ml_models/")
for f in sorted(saved):
    kb = os.path.getsize(os.path.join(MODELS_DIR, f)) / 1024
    print(f"      {f}  ({kb:.1f} KB)")
print("=" * 60)
print("  Run server:  python manage.py runserver")
print("=" * 60)
