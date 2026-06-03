import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

def generate_fraud_dataset(n_samples: int = 50000) -> pd.DataFrame:
    n_fraud = int(n_samples * 0.03)       # 3% fraud rate
    n_legit = n_samples - n_fraud

    legit = pd.DataFrame({
        "amount": np.random.lognormal(mean=3.5, sigma=1.2, size=n_legit).clip(1, 10000),
        "hour_of_day": np.random.choice(range(24), size=n_legit, p=_hour_weights()),
        "day_of_week": np.random.randint(0, 7, size=n_legit),
        "merchant_category": np.random.choice(
            ["grocery", "restaurant", "gas", "retail", "travel", "entertainment", "healthcare"],
            size=n_legit, p=[0.25, 0.20, 0.15, 0.18, 0.08, 0.09, 0.05]
        ),
        "country_code": np.random.choice(["IN", "US", "GB", "DE", "SG"], size=n_legit,
                                          p=[0.50, 0.20, 0.12, 0.10, 0.08]),
        "card_present": np.random.choice([0, 1], size=n_legit, p=[0.25, 0.75]),
        "transactions_last_1h": np.random.poisson(1.2, size=n_legit).clip(0, 15),
        "transactions_last_24h": np.random.poisson(4.5, size=n_legit).clip(0, 50),
        "avg_amount_last_7d": np.random.lognormal(3.4, 1.1, size=n_legit).clip(1, 5000),
        "distance_from_home_km": np.abs(np.random.normal(15, 20, size=n_legit)).clip(0, 200),
        "account_age_days": np.random.exponential(500, size=n_legit).clip(1, 3650),
        "failed_attempts_last_24h": np.random.choice([0, 1, 2], size=n_legit, p=[0.85, 0.12, 0.03]),
        "is_international": np.random.choice([0, 1], size=n_legit, p=[0.90, 0.10]),
        "device_change": np.random.choice([0, 1], size=n_legit, p=[0.95, 0.05]),
        "is_fraud": 0,
    })

    fraud = pd.DataFrame({
        "amount": np.random.lognormal(mean=5.2, sigma=1.5, size=n_fraud).clip(50, 25000),
        "hour_of_day": np.random.choice(range(24), size=n_fraud, p=_fraud_hour_weights()),
        "day_of_week": np.random.randint(0, 7, size=n_fraud),
        "merchant_category": np.random.choice(
            ["grocery", "restaurant", "gas", "retail", "travel", "entertainment", "healthcare"],
            size=n_fraud, p=[0.08, 0.07, 0.10, 0.20, 0.30, 0.18, 0.07]
        ),
        "country_code": np.random.choice(["IN", "US", "GB", "DE", "SG"], size=n_fraud,
                                          p=[0.20, 0.25, 0.20, 0.20, 0.15]),
        "card_present": np.random.choice([0, 1], size=n_fraud, p=[0.70, 0.30]),
        "transactions_last_1h": np.random.poisson(4.5, size=n_fraud).clip(0, 20),
        "transactions_last_24h": np.random.poisson(12, size=n_fraud).clip(0, 80),
        "avg_amount_last_7d": np.random.lognormal(3.0, 1.2, size=n_fraud).clip(1, 3000),
        "distance_from_home_km": np.abs(np.random.normal(120, 80, size=n_fraud)).clip(0, 800),
        "account_age_days": np.random.exponential(120, size=n_fraud).clip(1, 1000),
        "failed_attempts_last_24h": np.random.choice([0, 1, 2, 3, 4], size=n_fraud,
                                                      p=[0.30, 0.25, 0.20, 0.15, 0.10]),
        "is_international": np.random.choice([0, 1], size=n_fraud, p=[0.45, 0.55]),
        "device_change": np.random.choice([0, 1], size=n_fraud, p=[0.50, 0.50]),
        "is_fraud": 1,
    })

    df = pd.concat([legit, fraud], ignore_index=True).sample(frac=1, random_state=42)
    df["transaction_id"] = [f"TXN{str(i).zfill(8)}" for i in range(len(df))]
    df["timestamp"] = pd.date_range("2024-01-01", periods=len(df), freq="1min")

    return df


def _hour_weights():
    w = np.array([0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 4.0,
                  5.0, 5.5, 6.0, 5.5, 5.0, 5.0, 5.5, 6.0, 5.5, 5.0,
                  4.5, 4.0, 3.0, 1.5])
    return w / w.sum()


def _fraud_hour_weights():
    w = np.array([3.0, 4.0, 4.5, 4.0, 3.0, 2.0, 1.5, 1.5, 2.0, 2.5,
                  3.0, 3.5, 3.5, 3.5, 3.0, 2.5, 2.5, 2.5, 3.0, 3.5,
                  4.0, 4.5, 4.5, 4.0])
    return w / w.sum()


if __name__ == "__main__":
    output_path = Path(__file__).parent.parent.parent / "data" / "transactions.csv"
    output_path.parent.mkdir(exist_ok=True)
    df = generate_fraud_dataset(50000)
    df.to_csv(output_path, index=False)
    print(f"✅ Dataset saved: {output_path}")
    print(f"   Total records : {len(df):,}")
    print(f"   Fraud records : {df['is_fraud'].sum():,} ({df['is_fraud'].mean()*100:.1f}%)")
    print(f"   Features      : {df.columns.tolist()}")
