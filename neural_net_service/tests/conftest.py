import pytest
from unittest.mock import patch, MagicMock
import mongomock
from datetime import datetime

# Mock MongoDB client and database for testing at a session scope
@pytest.fixture(scope="session")
def mock_db_session():
    # Use mongomock for a in-memory MongoDB instance
    mock_client = mongomock.MongoClient()
    mock_db = mock_client.get_database("test_db")

    yield mock_db


# Fixture to seed the database with sample data for each test function
@pytest.fixture(scope="function")
def seeded_db(mock_db_session):
    # Access the mocked database instance provided by the session fixture
    transactions_collection = mock_db_session.transactions
    fraud_data_collection = mock_db_session.fraud_data

    # Clear collections before seeding for each test function
    transactions_collection.delete_many({})
    fraud_data_collection.delete_many({})

    # Sample Transaction Data (30 transactions)
    sample_transactions = []
    for i in range(1, 31):
        transaction_data = {
            "id_transaction": f"transaction_{i}",
            "id_user": f"user_{(i % 10) + 1}", # Assign to 10 users
            "shipzip": f"zip_{i:05d}",
            "shipping_address": f"{i} Test St",
            "shipping_city": "Testville",
            "shipping_province": "TV",
            "shipping_kecamatan": "Test District",
            "payment_type": "credit_card" if i % 2 == 0 else "debit_card",
            "number": f"1111-2222-3333-{i:04d}",
            "bank_name": f"Bank_{i % 5 + 1}",
            "amount": 10.0 * i,
            "status": "completed",
            "billing_address": f"{i} Test St",
            "billing_city": "Testville",
            "billing_province": "TV",
            "billing_kecamatan": "Test District",
            "list_of_items": [{"item_id": f"item_{j}", "price": 5.0} for j in range(i % 3 + 1)] # 1 to 3 items
        }
        sample_transactions.append(transaction_data)

    transactions_collection.insert_many(sample_transactions)

    # Sample Fraud Data (10 fraud, 20 normal)
    sample_fraud_data = []
    for i in range(1, 31):
        fraud_status = "fraud" if i <= 10 else "normal"
        fraud_data = {
            "fraud_id": f"fraud_data_{i}",
            "id_user": f"user_{(i % 10) + 1}",
            "id_transactions": [f"transaction_{i}"],
            "status": "processed",
            "probability_ml": 0.9 if i <= 10 else 0.1,
            "policy_list": [f"policy_{i % 3 + 1}"],
            "jarak_fraud": 5 if i <= 10 else None,
            "probability_contact_with_fraud": 0.8 if i <= 10 else None,
            "confirmed_fraud": fraud_status,
            "confirmed_date": datetime.now().isoformat() if i <= 10 else None,
            "confirmed_institution": f"Institution_{i % 2 + 1}" if i <= 10 else None
        }
        sample_fraud_data.append(fraud_data)

    fraud_data_collection.insert_many(sample_fraud_data)

    yield mock_db_session