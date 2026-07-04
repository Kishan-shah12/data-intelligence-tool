import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import random
import os

def generate_mock_data():
    NUM_ROWS = 1_000_000
    NUM_FRAUD_RINGS = 500

    print("Generating entities (users, devices, IPs, Zips)...")
    users = [f"user_{i}" for i in range(200_000)]
    devices = [f"dev_{i}" for i in range(100_000)]
    ips = [f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(50_000)]
    zips = [f"{random.randint(10000, 99999)}" for _ in range(10_000)]

    start_time = datetime(2023, 1, 1)
    end_time = datetime(2023, 1, 31)
    time_diff = int((end_time - start_time).total_seconds())

    transactions = []

    print(f"Generating {NUM_FRAUD_RINGS} fraud rings...")
    for _ in range(NUM_FRAUD_RINGS):
        ring_device = random.choice(devices)
        ring_ip = random.choice(ips)
        ring_size = random.randint(10, 50)
        base_time = start_time + timedelta(seconds=random.randint(0, time_diff))
        
        # Pick distinct users for the ring
        ring_users = random.sample(users, ring_size)
        
        for user in ring_users:
            # Transactions within a 5-minute (300 seconds) window
            txn_time = base_time + timedelta(seconds=random.randint(0, 300))
            transactions.append({
                "transaction_id": str(uuid.uuid4()),
                "timestamp": txn_time,
                "user_id": user,
                "device_id": ring_device,
                "ip_address": ring_ip,
                "shipping_zip": random.choice(zips),
                "cart_value": round(random.uniform(10.0, 5000.0), 2),
                "is_fraud_flag": 1
            })

    num_normal_txns = NUM_ROWS - len(transactions)
    print(f"Generating {num_normal_txns} normal transactions (this might take a few moments)...")

    # Vectorized generation for normal transactions for speed
    normal_txns = pd.DataFrame({
        "transaction_id": [str(uuid.uuid4()) for _ in range(num_normal_txns)],
        "timestamp": [start_time + timedelta(seconds=random.randint(0, time_diff)) for _ in range(num_normal_txns)],
        "user_id": np.random.choice(users, num_normal_txns),
        "device_id": np.random.choice(devices, num_normal_txns),
        "ip_address": np.random.choice(ips, num_normal_txns),
        "shipping_zip": np.random.choice(zips, num_normal_txns),
        "cart_value": np.round(np.random.uniform(5.0, 1000.0, num_normal_txns), 2),
        "is_fraud_flag": 0
    })

    print("Combining and sorting datasets...")
    fraud_df = pd.DataFrame(transactions)
    df = pd.concat([fraud_df, normal_txns], ignore_index=True)
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # Add a date column for Hive-style partitioning
    df['date'] = df['timestamp'].dt.date

    output_dir = "data/raw_transactions"
    print(f"Saving data to {output_dir} as partitioned Parquet files...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save partitioned by date
    df.to_parquet(output_dir, partition_cols=['date'], engine='pyarrow', index=False)
    print("Done! Data successfully generated and saved.")

if __name__ == "__main__":
    generate_mock_data()
