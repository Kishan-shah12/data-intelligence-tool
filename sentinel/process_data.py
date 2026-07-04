import pandas as pd
import os

def process():
    print("Reading raw transactions...")
    raw_df = pd.read_parquet("data/raw_transactions")

    print("Processing threat networks...")
    threats = raw_df.groupby("device_id").agg(
        unique_users_count=("user_id", "nunique"),
        total_value_at_risk=("cart_value", "sum"),
        connected_ips=("ip_address", lambda x: list(set(x))),
        is_fraud_flag=("is_fraud_flag", "max")
    ).reset_index()

    threats["risk_score"] = threats.apply(lambda row: 85 if row["unique_users_count"] > 10 else 45, axis=1)

    print("Saving processed threat networks...")
    threats.to_parquet("data/processed_threat_networks.parquet", engine="pyarrow", index=False)
    
    print("Done! Here are a few high-risk device IDs you can test:")
    print(threats[threats['risk_score'] > 80]['device_id'].head().tolist())

if __name__ == "__main__":
    process()
