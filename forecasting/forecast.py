import pandas as pd
import numpy as np
import os

# ==============================
# 📂 Load Data (robust path)
# ==============================
BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "..", "data", "sales.csv")

df = pd.read_csv(file_path)
df['date'] = pd.to_datetime(df['date'])

# Normalize column names
df.columns = df.columns.str.lower().str.strip()

# ==============================
# 📊 Sort Data
# ==============================
df = df.sort_values(['sku', 'date'])

FORECAST_HORIZON = 4
results = []

# ==============================
# 📏 Metrics
# ==============================

# Safe MAPE (avoids division by zero)
def mape(actual, pred):
    actual, pred = np.array(actual), np.array(pred)
    mask = actual != 0

    if np.sum(mask) == 0:
        return np.nan

    return np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100

# MAE (primary stable metric)
def mae(actual, pred):
    actual, pred = np.array(actual), np.array(pred)
    return np.mean(np.abs(actual - pred))

# ==============================
# 🔁 Forecast per SKU
# ==============================
for sku in df['sku'].unique():
    sku_df = df[df['sku'] == sku]

    if len(sku_df) <= FORECAST_HORIZON:
        continue

    train = sku_df.iloc[:-FORECAST_HORIZON]
    test = sku_df.iloc[-FORECAST_HORIZON:]

    # ==============================
    # 🥇 Baseline (Last Value)
    # ==============================
    last_value = train['units_sold'].iloc[-1]
    baseline_pred = [last_value] * FORECAST_HORIZON

    # ==============================
    # 🥈 Model (Moving Average)
    # ==============================
    moving_avg = train['units_sold'].rolling(3).mean().iloc[-1]

    # fallback if NaN (small data)
    if np.isnan(moving_avg):
        moving_avg = last_value

    model_pred = [moving_avg] * FORECAST_HORIZON

    # ==============================
    # 📊 Evaluate
    # ==============================
    baseline_mape = mape(test['units_sold'], baseline_pred)
    model_mape = mape(test['units_sold'], model_pred)

    baseline_mae = mae(test['units_sold'], baseline_pred)
    model_mae = mae(test['units_sold'], model_pred)

    results.append({
        "sku": sku,
        "baseline_mape": baseline_mape,
        "model_mape": model_mape,
        "baseline_mae": baseline_mae,
        "model_mae": model_mae,
        "improvement_mae": baseline_mae - model_mae
    })

# ==============================
# 📊 Final Results
# ==============================
results_df = pd.DataFrame(results)

print("\n📊 Per SKU Results:\n")
print(results_df)

print("\n🎯 Overall Performance:\n")
print("Baseline MAPE:", results_df['baseline_mape'].mean(skipna=True))
print("Model MAPE:", results_df['model_mape'].mean(skipna=True))

print("Baseline MAE:", results_df['baseline_mae'].mean())
print("Model MAE:", results_df['model_mae'].mean())