"""
CropConnect — Model Evaluation Script
Generates F1, Recall, Precision, Accuracy for all 3 ML models
Run: python evaluate_models.py
"""

import os
import warnings
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, mean_absolute_error, r2_score,
    mean_squared_error, confusion_matrix
)

warnings.filterwarnings('ignore')

# ── Path Setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'ml_data')

print("=" * 70)
print("  CropConnect — ML Model Evaluation Report")
print("=" * 70)


# ─────────────────────────────────────────────────────────────
# HELPER: Print a clean metrics table
# ─────────────────────────────────────────────────────────────
def print_table(rows, headers):
    col_w = [max(len(str(r[i])) for r in rows + [headers]) + 2 for i in range(len(headers))]
    sep = "+" + "+".join("-" * w for w in col_w) + "+"
    def fmt_row(row):
        return "|" + "|".join(str(row[i]).center(col_w[i]) for i in range(len(headers))) + "|"
    print(sep)
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(sep)


# ─────────────────────────────────────────────────────────────
# MODEL 1 — FRAUD DETECTOR
# Dataset  : fraud_data.csv
# Algorithm: GradientBoostingClassifier
# Task     : Binary Classification (0=Genuine, 1=Fraud)
# ─────────────────────────────────────────────────────────────
print("\n[1/3]  FRAUD DETECTOR  —  GradientBoostingClassifier")
print("-" * 70)

df = pd.read_csv(os.path.join(DATA_DIR, 'fraud_data.csv'))

features = [
    'farmer_land_acres', 'booked_quantity_qtl', 'quantity_per_acre',
    'past_total_bookings', 'past_approved_bookings', 'past_rejected_bookings',
    'qty_vs_avg_ratio', 'farmer_verified', 'days_since_last_booking',
    'aadhaar_bank_linked', 'multiple_accounts_flag'
]
df = df.dropna(subset=features + ['is_fraudulent'])

X = df[features]
y = df['is_fraudulent']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = GradientBoostingClassifier(
    n_estimators=200, max_depth=4, learning_rate=0.08, random_state=42
)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# ── Overall metrics ──
fraud_rows = [
    ["Accuracy",  f"{accuracy_score(y_test, y_pred) * 100:.2f}%"],
    ["Precision", f"{precision_score(y_test, y_pred) * 100:.2f}%"],
    ["Recall",    f"{recall_score(y_test, y_pred) * 100:.2f}%"],
    ["F1 Score",  f"{f1_score(y_test, y_pred) * 100:.2f}%"],
]
print_table(fraud_rows, ["Metric", "Score"])

# ── Per-class metrics ──
print("\n  Per-class breakdown:")
class_rows = [
    ["Genuine (0)",
     f"{precision_score(y_test, y_pred, pos_label=0):.4f}",
     f"{recall_score(y_test, y_pred, pos_label=0):.4f}",
     f"{f1_score(y_test, y_pred, pos_label=0):.4f}",
     f"{(y_test == 0).sum()}"],
    ["Fraud (1)",
     f"{precision_score(y_test, y_pred, pos_label=1):.4f}",
     f"{recall_score(y_test, y_pred, pos_label=1):.4f}",
     f"{f1_score(y_test, y_pred, pos_label=1):.4f}",
     f"{(y_test == 1).sum()}"],
]
print_table(class_rows, ["Class", "Precision", "Recall", "F1", "Support"])

# ── Confusion matrix ──
cm = confusion_matrix(y_test, y_pred)
print(f"\n  Confusion Matrix:")
print(f"               Predicted Genuine  Predicted Fraud")
print(f"  Actual Genuine      {cm[0][0]:>4}               {cm[0][1]:>4}")
print(f"  Actual Fraud        {cm[1][0]:>4}               {cm[1][1]:>4}")

print(f"\n  Train size: {len(X_train)}   Test size: {len(X_test)}")
print(f"  Fraud ratio in test: {(y_test==1).sum()}/{len(y_test)} = {(y_test==1).mean()*100:.1f}%")


# ─────────────────────────────────────────────────────────────
# MODEL 2 — QUALITY GRADE PREDICTOR
# Dataset  : quality_data.csv
# Algorithm: DecisionTreeClassifier
# Task     : Multi-class Classification (FAQ / Below_FAQ / Rejected)
# ─────────────────────────────────────────────────────────────
print("\n\n[2/3]  QUALITY GRADE PREDICTOR  —  DecisionTreeClassifier")
print("-" * 70)

dq = pd.read_csv(os.path.join(DATA_DIR, 'quality_data.csv'))

grade_map    = {'FAQ': 0, 'Below_FAQ': 1, 'Rejected': 2}
grade_labels = {0: 'FAQ', 1: 'Below_FAQ', 2: 'Rejected'}

dq['crop_e']  = dq['crop'].map({'Paddy': 0, 'Groundnut': 1}).fillna(0)
dq['grade_e'] = dq['quality_grade'].map(grade_map)

q_features = [
    'crop_e', 'moisture_percent', 'foreign_matter_percent',
    'damaged_grains_percent', 'immature_grains_percent',
    'chalky_grains_percent', 'shelling_outturn_percent',
    'oil_content_percent', 'aflatoxin_detected'
]
dq = dq.dropna(subset=q_features + ['grade_e'])

Xq = dq[q_features]
yq = dq['grade_e'].astype(int)

Xq_train, Xq_test, yq_train, yq_test = train_test_split(
    Xq, yq, test_size=0.2, random_state=42, stratify=yq
)

quality_model = DecisionTreeClassifier(
    max_depth=10, min_samples_leaf=8, random_state=42
)
quality_model.fit(Xq_train, yq_train)
yq_pred = quality_model.predict(Xq_test)

# ── Overall metrics (macro avg) ──
quality_rows = [
    ["Accuracy",         f"{accuracy_score(yq_test, yq_pred) * 100:.2f}%"],
    ["Precision (macro)", f"{precision_score(yq_test, yq_pred, average='macro') * 100:.2f}%"],
    ["Recall (macro)",   f"{recall_score(yq_test, yq_pred, average='macro') * 100:.2f}%"],
    ["F1 Score (macro)", f"{f1_score(yq_test, yq_pred, average='macro') * 100:.2f}%"],
]
print_table(quality_rows, ["Metric", "Score (macro avg)"])

# ── Per-class metrics ──
print("\n  Per-class breakdown:")
class_q_rows = []
for grade_id, grade_name in grade_labels.items():
    p = precision_score(yq_test, yq_pred, labels=[grade_id], average='macro')
    r = recall_score(yq_test, yq_pred, labels=[grade_id], average='macro')
    f = f1_score(yq_test, yq_pred, labels=[grade_id], average='macro')
    support = (yq_test == grade_id).sum()
    class_q_rows.append([grade_name, f"{p:.4f}", f"{r:.4f}", f"{f:.4f}", str(support)])
print_table(class_q_rows, ["Grade Class", "Precision", "Recall", "F1", "Support"])

print(f"\n  Tree depth used: {quality_model.get_depth()}")
print(f"  Tree leaves    : {quality_model.get_n_leaves()}")
print(f"  Train size: {len(Xq_train)}   Test size: {len(Xq_test)}")


# ─────────────────────────────────────────────────────────────
# MODEL 3 — CROP YIELD PREDICTOR
# Dataset  : yield_data.csv
# Algorithm: RandomForestRegressor
# Task     : Regression (predicts total_yield_qtl)
# Note     : No F1/Precision/Recall for regression — use MAE/RMSE/R²
# ─────────────────────────────────────────────────────────────
print("\n\n[3/3]  CROP YIELD PREDICTOR  —  RandomForestRegressor")
print("-" * 70)
print("  (Regression task — uses MAE, RMSE, R², MAPE instead of F1/Precision/Recall)")

dy = pd.read_csv(os.path.join(DATA_DIR, 'yield_data.csv'))

crops     = sorted(dy['crop'].unique())
districts = sorted(dy['district'].unique())
seasons   = sorted(dy['season'].unique())
soils     = sorted(dy['soil_type'].unique())

dy['crop_e'] = dy['crop'].map({c: i for i, c in enumerate(crops)})
dy['dist_e'] = dy['district'].map({d: i for i, d in enumerate(districts)})
dy['seas_e'] = dy['season'].map({s: i for i, s in enumerate(seasons)})
dy['soil_e'] = dy['soil_type'].map({s: i for i, s in enumerate(soils)})

y_features = ['crop_e', 'dist_e', 'seas_e', 'soil_e',
              'land_area_acres', 'annual_rainfall_mm', 'avg_temperature_c']
dy = dy.dropna(subset=y_features + ['total_yield_qtl'])

Xy = dy[y_features]
yy = dy['total_yield_qtl']

Xy_train, Xy_test, yy_train, yy_test = train_test_split(
    Xy, yy, test_size=0.2, random_state=42
)

yield_model = RandomForestRegressor(
    n_estimators=150, max_depth=12, random_state=42, n_jobs=-1
)
yield_model.fit(Xy_train, yy_train)
yy_pred = yield_model.predict(Xy_test)

mae  = mean_absolute_error(yy_test, yy_pred)
rmse = np.sqrt(mean_squared_error(yy_test, yy_pred))
r2   = r2_score(yy_test, yy_pred)
mape = np.mean(np.abs((yy_test - yy_pred) / yy_test)) * 100

yield_rows = [
    ["MAE  (Mean Absolute Error)",        f"{mae:.2f} qtl"],
    ["RMSE (Root Mean Squared Error)",    f"{rmse:.2f} qtl"],
    ["R²   (R-squared / Accuracy)",       f"{r2:.4f}  ({r2*100:.2f}%)"],
    ["MAPE (Mean Abs Percentage Error)",  f"{mape:.2f}%"],
]
print_table(yield_rows, ["Metric", "Score"])

# ── Feature importance ──
print("\n  Feature Importance (what drives yield prediction):")
importances = sorted(
    zip(y_features, yield_model.feature_importances_),
    key=lambda x: x[1], reverse=True
)
imp_rows = [[f, f"{v*100:.2f}%", "█" * int(v * 40)] for f, v in importances]
print_table(imp_rows, ["Feature", "Importance %", "Bar"])

print(f"\n  Train size: {len(Xy_train)}   Test size: {len(Xy_test)}")


# ─────────────────────────────────────────────────────────────
# MASTER SUMMARY TABLE
# ─────────────────────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("  MASTER SUMMARY — All 3 Models")
print("=" * 70)

fraud_acc  = accuracy_score(y_test, y_pred) * 100
fraud_prec = precision_score(y_test, y_pred) * 100
fraud_rec  = recall_score(y_test, y_pred) * 100
fraud_f1   = f1_score(y_test, y_pred) * 100

qual_acc   = accuracy_score(yq_test, yq_pred) * 100
qual_prec  = precision_score(yq_test, yq_pred, average='macro') * 100
qual_rec   = recall_score(yq_test, yq_pred, average='macro') * 100
qual_f1    = f1_score(yq_test, yq_pred, average='macro') * 100

summary_rows = [
    ["Fraud Detector",
     "GradientBoosting", "Binary Classif.",
     f"{fraud_acc:.2f}%", f"{fraud_prec:.2f}%",
     f"{fraud_rec:.2f}%", f"{fraud_f1:.2f}%"],
    ["Quality Grader",
     "DecisionTree", "Multi-class Classif.",
     f"{qual_acc:.2f}%", f"{qual_prec:.2f}%",
     f"{qual_rec:.2f}%", f"{qual_f1:.2f}%"],
    ["Yield Predictor",
     "RandomForest", "Regression",
     f"R²={r2*100:.2f}%", "N/A", "N/A",
     f"MAE={mae:.1f}qtl"],
]
print_table(summary_rows, [
    "Model", "Algorithm", "Task Type",
    "Accuracy", "Precision", "Recall", "F1 Score"
])

print("\n  Notes:")
print("  • F1 / Precision / Recall are not applicable to regression tasks.")
print("  • Quality model uses macro-averaging across 3 classes.")
print("  • Fraud model uses binary averaging (positive class = Fraud).")
print("  • Yield R² of 0.90+ means the model explains 90% of yield variance.")
print("=" * 70)