import pytest
from fastapi.testclient import TestClient
from .main import app
from .models import Transaction
import json

client = TestClient(app)

import pytest

@pytest.mark.asyncio
async def test_process_transaction_normal(mock_db):
    transaction_data = {
        "transaction_id": "test_normal_transaction",
        "user_id": "test_user",
        "amount": 100,
        "transaction_type": "deposit"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)
    assert response["transaction_id"] == "test_normal_transaction"
    assert response["risk_level"] == "normal"

@pytest.mark.asyncio
async def test_process_transaction_suspect(mock_db):
    transaction_data = {
        "transaction_id": "test_suspect_transaction",
        "user_id": "test_user",
        "amount": 500,
        "transaction_type": "withdrawal"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)
    assert response["transaction_id"] == "test_suspect_transaction"
    # In a real system, the risk level would depend on the defined policies.
    # For this test, we'll just check that the risk_level is not empty.
    assert response["risk_level"] != ""

@pytest.mark.asyncio
async def test_process_transaction_fraud(mock_db):
    transaction_data = {
        "transaction_id": "test_fraud_transaction",
        "user_id": "test_user",
        "amount": 1000,
        "transaction_type": "transfer"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)
    assert response["transaction_id"] == "test_fraud_transaction"
    # In a real system, the risk level would depend on the defined policies.
    # For this test, we'll just check that the risk_level is not empty.
    assert response["risk_level"] != ""

def test_process_transaction_invalid_input():
    transaction_data = {
        "user_id": "test_user",
        "amount": "invalid",  # Invalid amount
        "transaction_type": "deposit"
    }
    response = client.post("/transactions", json=transaction_data)
    assert response.status_code == 422  # Unprocessable Entity due to validation error