import pandas as pd
import numpy as np
import random
import hashlib
import secrets
from datetime import datetime, timedelta
import os

def generate_blockchain_transactions(num_transactions=1000):
    """Generate realistic blockchain transaction dataset"""
    
    # Generate addresses
    num_addresses = num_transactions // 5
    addresses = [
        hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:40]
        for _ in range(num_addresses)
    ]
    
    transactions = []
    start_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_transactions):
        tx = {
            'tx_id': hashlib.sha256(f"tx_{i}_{secrets.token_hex(8)}".encode()).hexdigest(),
            'timestamp': (start_time + timedelta(minutes=random.randint(0, 43200))).isoformat(),
            'sender_address': random.choice(addresses),
            'receiver_address': random.choice(addresses),
            'amount': round(random.uniform(0.001, 100.0), 8),
            'fee': round(random.uniform(0.0001, 0.01), 8),
            'block_number': random.randint(1000000, 1500000),
            'gas_used': random.randint(21000, 100000),
            'transaction_type': random.choice(['transfer', 'contract_call', 'contract_creation']),
            'status': random.choice(['success', 'success', 'success', 'failed']),
        }
        transactions.append(tx)
    
    df = pd.DataFrame(transactions)
    return df

def generate_network_data(num_records=1000):
    """Generate blockchain network data"""
    
    records = []
    nodes = [f"node_{i:04d}" for i in range(50)]
    
    for i in range(num_records):
        record = {
            'node_id': random.choice(nodes),
            'peer_count': random.randint(1, 25),
            'latency_ms': round(random.uniform(10, 500), 2),
            'bandwidth_mbps': round(random.uniform(1, 100), 2),
            'block_propagation_time': round(random.uniform(0.5, 10.0), 2),
            'transactions_per_second': round(random.uniform(10, 1000), 2),
            'mempool_size': random.randint(0, 5000),
            'sync_status': random.choice(['synced', 'syncing', 'synced']),
            'uptime_hours': random.randint(1, 720),
            'geographic_region': random.choice(['US-East', 'US-West', 'EU', 'Asia', 'Oceania']),
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    return df

def generate_user_behavior_data(num_users=500):
    """Generate user behavior dataset"""
    
    users = []
    
    for i in range(num_users):
        user = {
            'user_id': f"user_{hashlib.sha256(str(i).encode()).hexdigest()[:16]}",
            'transaction_count': random.randint(1, 200),
            'total_volume': round(random.uniform(0.1, 10000), 2),
            'avg_transaction_size': round(random.uniform(0.01, 100), 2),
            'active_days': random.randint(1, 365),
            'peak_hour': random.randint(0, 23),
            'preferred_gas_price': round(random.uniform(1, 50), 2),
            'contract_interactions': random.randint(0, 100),
            'token_types_used': random.randint(1, 20),
            'privacy_score': round(random.uniform(0, 1), 3),
            'risk_score': round(random.uniform(0, 1), 3),
            'account_age_days': random.randint(1, 1000),
        }
        users.append(user)
    
    df = pd.DataFrame(users)
    return df

def generate_privacy_metrics_data(num_samples=500):
    """Generate privacy evaluation metrics dataset"""
    
    techniques = ['ring_signature', 'zkp', 'smpc', 'tee', 'mixer']
    metrics = []
    
    for i in range(num_samples):
        technique = random.choice(techniques)
        
        # Different characteristics for each technique
        if technique == 'ring_signature':
            privacy_score = random.uniform(60, 95)
            execution_time = random.uniform(0.1, 2.0)
            anonymity_set = random.randint(5, 50)
        elif technique == 'zkp':
            privacy_score = random.uniform(90, 100)
            execution_time = random.uniform(0.5, 5.0)
            anonymity_set = 1
        elif technique == 'smpc':
            privacy_score = random.uniform(70, 95)
            execution_time = random.uniform(1.0, 10.0)
            anonymity_set = random.randint(3, 20)
        elif technique == 'tee':
            privacy_score = random.uniform(85, 98)
            execution_time = random.uniform(0.2, 1.5)
            anonymity_set = 1
        else:  # mixer
            privacy_score = random.uniform(50, 90)
            execution_time = random.uniform(5.0, 30.0)
            anonymity_set = random.randint(10, 100)
        
        metric = {
            'experiment_id': f"exp_{i:05d}",
            'technique': technique,
            'privacy_score': round(privacy_score, 2),
            'execution_time_seconds': round(execution_time, 3),
            'anonymity_set_size': anonymity_set,
            'throughput_tps': round(random.uniform(10, 1000), 2),
            'storage_overhead_mb': round(random.uniform(0.1, 100), 2),
            'computation_cost': round(random.uniform(0.01, 10.0), 4),
            'accuracy': round(random.uniform(0.95, 1.0), 4),
        }
        metrics.append(metric)
    
    df = pd.DataFrame(metrics)
    return df

# Generate all datasets
if __name__ == "__main__":
    # Create media/datasets directory if not exists
    os.makedirs('media/datasets', exist_ok=True)
    
    # Generate and save datasets
    print("Generating blockchain transactions dataset...")
    tx_df = generate_blockchain_transactions(1000)
    tx_df.to_csv('media/datasets/blockchain_transactions.csv', index=False)
    print(f"✓ Generated: blockchain_transactions.csv ({len(tx_df)} records)")
    
    print("\nGenerating network data...")
    network_df = generate_network_data(1000)
    network_df.to_csv('media/datasets/network_data.csv', index=False)
    print(f"✓ Generated: network_data.csv ({len(network_df)} records)")
    
    print("\nGenerating user behavior data...")
    user_df = generate_user_behavior_data(500)
    user_df.to_csv('media/datasets/user_behavior.csv', index=False)
    print(f"✓ Generated: user_behavior.csv ({len(user_df)} records)")
    
    print("\nGenerating privacy metrics data...")
    metrics_df = generate_privacy_metrics_data(500)
    metrics_df.to_csv('media/datasets/privacy_metrics.csv', index=False)
    print(f"✓ Generated: privacy_metrics.csv ({len(metrics_df)} records)")
    
    print("\n✓ All datasets generated successfully!")
    print("\nDataset Summaries:")
    print(f"\n1. Blockchain Transactions: {tx_df.shape}")
    print(tx_df.head(2))
    print(f"\n2. Network Data: {network_df.shape}")
    print(network_df.head(2))
    print(f"\n3. User Behavior: {user_df.shape}")
    print(user_df.head(2))
    print(f"\n4. Privacy Metrics: {metrics_df.shape}")
    print(metrics_df.head(2))
