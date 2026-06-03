import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


CATEGORY_MAP = {
    "grocery": 0, "restaurant": 1, "gas": 2,
    "retail": 3, "travel": 4, "entertainment": 5, "healthcare": 6,
}

COUNTRY_RISK = {
    "IN": 0.3, "US": 0.4, "GB": 0.35, "DE": 0.3, "SG": 0.45,
}

HIGH_RISK_CATEGORIES = {"travel", "entertainment"}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["merchant_cat_code"] = df["merchant_category"].map(CATEGORY_MAP).fillna(3).astype(int)
    df["country_risk_score"] = df["country_code"].map(COUNTRY_RISK).fillna(0.4)
    df["is_high_risk_category"] = df["merchant_category"].isin(HIGH_RISK_CATEGORIES).astype(int)

    df["is_night"] = ((df["hour_of_day"] >= 22) | (df["hour_of_day"] <= 5)).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)

    df["log_amount"] = np.log1p(df["amount"])
    df["amount_vs_avg"] = df["amount"] / (df["avg_amount_last_7d"] + 1e-9)
    df["is_large_amount"] = (df["amount"] > 1000).astype(int)
    df["amount_zscore"] = (
        (df["amount"] - df["avg_amount_last_7d"]) /
        (df["avg_amount_last_7d"].std() + 1e-9)
    ).clip(-5, 5)

    df["velocity_ratio"] = df["transactions_last_1h"] / (df["transactions_last_24h"] + 1e-9)
    df["high_velocity"] = (df["transactions_last_1h"] >= 5).astype(int)

    df["risk_score_raw"] = (
        df["is_international"] * 0.3 +
        df["device_change"] * 0.25 +
        df["is_night"] * 0.15 +
        df["is_high_risk_category"] * 0.15 +
        (df["failed_attempts_last_24h"] > 0).astype(int) * 0.15
    )
    df["distance_log"] = np.log1p(df["distance_from_home_km"])
    df["account_age_log"] = np.log1p(df["account_age_days"])
    df["new_account"] = (df["account_age_days"] < 30).astype(int)

    return df


FEATURE_COLUMNS = [
    "log_amount", "amount_vs_avg", "amount_zscore", "is_large_amount",
    "hour_sin", "hour_cos", "is_night", "is_weekend",
    "merchant_cat_code", "is_high_risk_category",
    "country_risk_score", "is_international",
    "card_present", "device_change",
    "transactions_last_1h", "transactions_last_24h", "velocity_ratio", "high_velocity",
    "distance_log", "account_age_log", "new_account",
    "failed_attempts_last_24h", "risk_score_raw",
]


class FraudFeatureTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer for the feature pipeline."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = engineer_features(X)
        return df[FEATURE_COLUMNS].values
