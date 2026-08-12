import pandas as pd
from cloud_accounts.models import CostRecord


def build_feature_dataframe(organization):
    """
    Pulls daily total cost per day for an organization and engineers
    features for time-series forecasting:
      - rolling_avg_7: 7-day rolling average (smooths daily noise)
      - day_of_week: captures weekly seasonality (e.g., weekend dips)
      - day_index: captures overall trend over time (0, 1, 2, ...)

    Returns a pandas DataFrame sorted by date, ready for train/test split.
    """
    records = (
        CostRecord.objects.filter(cloud_account__organization=organization)
        .values("date")
        .order_by("date")
    )

    df = pd.DataFrame(list(records))
    if df.empty:
        return df

    # aggregate total cost per day (in case of multiple services per day)
    from django.db.models import Sum
    daily = (
        CostRecord.objects.filter(cloud_account__organization=organization)
        .values("date")
        .annotate(total_amount=Sum("amount"))
        .order_by("date")
    )
    df = pd.DataFrame(list(daily))
    df["date"] = pd.to_datetime(df["date"])
    df["total_amount"] = df["total_amount"].astype(float)

    # feature engineering
    df["day_of_week"] = df["date"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["rolling_avg_7"] = df["total_amount"].rolling(window=7, min_periods=1).mean()
    df["day_index"] = range(len(df))

    return df.reset_index(drop=True)


from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


def train_forecast_model(organization, test_size=15):
    """
    Trains a Linear Regression model to predict daily cost based on
    engineered features (day_of_week, rolling_avg_7, day_index).

    Uses a CHRONOLOGICAL split (not random) - trains on the earliest
    days, tests on the most recent days - to avoid data leakage that
    would happen if we let the model "see the future" during training.

    Returns the trained model, feature column names, and validation metrics.
    """
    df = build_feature_dataframe(organization)

    if len(df) < test_size + 10:
        raise ValueError(
            f"Not enough data to train a reliable model. "
            f"Have {len(df)} days, need at least {test_size + 10}."
        )

    feature_cols = ["day_of_week", "rolling_avg_7", "day_index"]
    target_col = "total_amount"

    split_index = len(df) - test_size
    train_df = df.iloc[:split_index]
    test_df = df.iloc[split_index:]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    model = LinearRegression()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    return {
        "model": model,
        "feature_cols": feature_cols,
        "mae": float(mae),
        "trained_on_days": len(train_df),
        "tested_on_days": len(test_df),
        "last_day_index": int(df["day_index"].iloc[-1]),
        "last_date": df["date"].iloc[-1],
    }


import pandas as pd


def generate_forecast(organization, days_ahead=30):
    """
    Trains on ALL available historical data (since we already validated
    accuracy separately via train_forecast_model), then predicts costs
    for the next days_ahead days into the future.

    Returns predicted daily amounts plus the validation MAE for context.
    """
    validation = train_forecast_model(organization)
    mae = validation["mae"]

    df = build_feature_dataframe(organization)
    feature_cols = ["day_of_week", "rolling_avg_7", "day_index"]
    target_col = "total_amount"

    # retrain on ALL data for the actual forecast (not just the train split)
    final_model = LinearRegression()
    final_model.fit(df[feature_cols], df[target_col])

    last_date = df["date"].iloc[-1]
    last_day_index = df["day_index"].iloc[-1]
    last_rolling_avg = df["rolling_avg_7"].iloc[-1]

    future_rows = []
    for i in range(1, days_ahead + 1):
        future_date = last_date + pd.Timedelta(days=i)
        future_rows.append({
            "date": future_date,
            "day_of_week": future_date.dayofweek,
            "rolling_avg_7": last_rolling_avg,  # simplification: hold recent avg steady
            "day_index": last_day_index + i,
        })

    future_df = pd.DataFrame(future_rows)
    predictions = final_model.predict(future_df[feature_cols])
    predictions = predictions.clip(min=0)  # cost can't be negative

    daily_predictions = [
        {"date": str(row["date"].date()), "predicted_amount": round(float(pred), 2)}
        for row, pred in zip(future_df.to_dict("records"), predictions)
    ]

    return {
        "forecast_period": f"next_{days_ahead}_days",
        "predicted_total": round(float(predictions.sum()), 2),
        "daily_predictions": daily_predictions,
        "model_confidence": {
            "mae": round(mae, 2),
            "based_on_days": len(df),
        },
    }


import pandas as pd


def generate_forecast(organization, days_ahead=30):
    """
    Trains on ALL available historical data (since we already validated
    accuracy separately via train_forecast_model), then predicts costs
    for the next days_ahead days into the future.

    Returns predicted daily amounts plus the validation MAE for context.
    """
    validation = train_forecast_model(organization)
    mae = validation["mae"]

    df = build_feature_dataframe(organization)
    feature_cols = ["day_of_week", "rolling_avg_7", "day_index"]
    target_col = "total_amount"

    # retrain on ALL data for the actual forecast (not just the train split)
    final_model = LinearRegression()
    final_model.fit(df[feature_cols], df[target_col])

    last_date = df["date"].iloc[-1]
    last_day_index = df["day_index"].iloc[-1]
    last_rolling_avg = df["rolling_avg_7"].iloc[-1]

    future_rows = []
    for i in range(1, days_ahead + 1):
        future_date = last_date + pd.Timedelta(days=i)
        future_rows.append({
            "date": future_date,
            "day_of_week": future_date.dayofweek,
            "rolling_avg_7": last_rolling_avg,  # simplification: hold recent avg steady
            "day_index": last_day_index + i,
        })

    future_df = pd.DataFrame(future_rows)
    predictions = final_model.predict(future_df[feature_cols])
    predictions = predictions.clip(min=0)  # cost can't be negative

    daily_predictions = [
        {"date": str(row["date"].date()), "predicted_amount": round(float(pred), 2)}
        for row, pred in zip(future_df.to_dict("records"), predictions)
    ]

    return {
        "forecast_period": f"next_{days_ahead}_days",
        "predicted_total": round(float(predictions.sum()), 2),
        "daily_predictions": daily_predictions,
        "model_confidence": {
            "mae": round(mae, 2),
            "based_on_days": len(df),
        },
    }
