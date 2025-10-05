#!/usr/bin/env python3
"""Train a random-forest model that predicts crop profitability for the next season.

The script reads the enriched historical dataset (`alap_kiegeszitve_costs_full.csv`),
trains a RandomForestRegressor on the last 24 years of EU crop data, persists the
pipeline, and exposes a helper for generating ranked crop suggestions given a
country/category selection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "alap_kiegeszitve_costs_full.csv"
MODEL_DIR = REPO_ROOT / "server" / "models"
MODEL_PATH = MODEL_DIR / "random_forest_profit.pkl"

CATEGORICAL_FEATURES = ["country", "category_key", "product", "Soil Type"]
NUMERIC_FEATURES = [
    "year",
    "Humidity(%)",
    "Moisture(%)",
    "Nitrogen(mg/Kg)",
    "Potassium(mg/Kg)",
    "Phosphorous(mg/Kg)",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMN = "profit_margin_pct"


def load_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path, sep=";")

    float_columns = [
        "price_eur_tonne",
        "Humidity(%)",
        "Moisture(%)",
        "Nitrogen(mg/Kg)",
        "Potassium(mg/Kg)",
        "Phosphorous(mg/Kg)",
        "cost_eur_tonne",
    ]
    for col in float_columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .replace({"nan": np.nan})
            .astype(float)
        )

    df["profit_eur_tonne"] = df["price_eur_tonne"] - df["cost_eur_tonne"]
    df[TARGET_COLUMN] = np.where(
        df["cost_eur_tonne"] > 0,
        df["profit_eur_tonne"] / df["cost_eur_tonne"],
        np.nan,
    )

    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])

    return df


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "num",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=None,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    return pipeline


def time_split(df: pd.DataFrame, year_threshold: int = 2018) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = df[df["year"] <= year_threshold].copy()
    test_df = df[df["year"] > year_threshold].copy()
    if train_df.empty or test_df.empty:
        raise ValueError("Temporal split yielded empty train/test sets. Check the threshold.")
    return train_df, test_df


def train_model(df: pd.DataFrame) -> dict:
    train_df, test_df = time_split(df)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN]

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds)),
        "test_samples": int(len(y_test)),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)

    return metrics


def load_model(path: Path = MODEL_PATH) -> Pipeline:
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run train_profit_model.py to train it first."
        )
    payload = joblib.load(path)
    return payload["pipeline"]


def prepare_candidate_matrix(
    df: pd.DataFrame,
    *,
    country: str,
    categories: Iterable[str],
    target_year: int,
    lookback_years: int = 10,
) -> pd.DataFrame:
    categories = set(categories)
    start_year = target_year - lookback_years

    subset = df[
        (df["country"].str.lower() == country.lower())
        & (df["year"] >= start_year)
        & (df["year"] < target_year)
        & (df["category_key"].isin(categories) if categories else True)
    ].copy()

    if subset.empty:
        raise ValueError("No historical records match the provided filters.")

    aggregated = (
        subset
        .groupby(["product", "category_key", "Soil Type"], as_index=False)
        .agg({
            "year": "max",
            "country": "first",
            "Humidity(%)": "mean",
            "Moisture(%)": "mean",
            "Nitrogen(mg/Kg)": "mean",
            "Potassium(mg/Kg)": "mean",
            "Phosphorous(mg/Kg)": "mean",
        })
    )

    aggregated["year"] = target_year
    return aggregated


def suggest_crops(
    model: Pipeline,
    df: pd.DataFrame,
    *,
    country: str,
    categories: Iterable[str],
    target_year: int,
    top_k: int = 5,
) -> pd.DataFrame:
    candidates = prepare_candidate_matrix(
        df,
        country=country,
        categories=categories,
        target_year=target_year,
    )
    preds = model.predict(candidates[FEATURE_COLUMNS])
    candidates = candidates.assign(predicted_profit_margin=preds)
    return candidates.sort_values("predicted_profit_margin", ascending=False).head(top_k)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Load the saved model and print crop suggestions.",
    )
    parser.add_argument("--country", type=str, help="ISO country name (e.g., Hungary)")
    parser.add_argument(
        "--categories",
        type=str,
        nargs="*",
        default=None,
        help="Optional list of category keys (arable vegetables etc.)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Target year for suggestion inference (default: 2025).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of suggestions to display (default: 5).",
    )
    args = parser.parse_args()

    df = load_dataset()

    if args.suggest:
        if not args.country:
            raise SystemExit("--country is required when using --suggest")
        model = load_model()
        categories = args.categories or []
        suggestions = suggest_crops(
            model,
            df,
            country=args.country,
            categories=categories,
            target_year=args.year,
            top_k=args.top,
        )
        print(suggestions.to_json(orient="records", indent=2))
        return

    metrics = train_model(df)
    print("Model trained and saved to", MODEL_PATH)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
