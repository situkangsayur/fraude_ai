import pytest
from fastapi.testclient import TestClient
from .main import app
from .models import Transaction
from .services import determine_risk_level # Import determine_risk_level
import json
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.asyncio
async def test_process_transaction_below_thresholds(mock_db):
    """
    Test a transaction that should not trigger any rules based on seeded data.
    Amount <= 500, type != 'transfer', velocity count <= 5.
    """
    transaction_data = {
        "transaction_id": "txn_below_thresholds",
        "user_id": "user_low_risk",
        "amount": 100,
        "transaction_type": "deposit"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)

    assert response["transaction_id"] == "txn_below_thresholds"
    assert response["risk_points"] == 0
    assert response["risk_level"] == determine_risk_level(0) # Should be 'normal'

@pytest.mark.asyncio
async def test_process_transaction_standard_rule_amount(mock_db):
    """
    Test a transaction that triggers only the 'Amount greater than 500' standard rule.
    Amount > 500, type != 'transfer', velocity count <= 5.
    """
    transaction_data = {
        "transaction_id": "txn_amount_rule",
        "user_id": "user_standard_amount",
        "amount": 600,
        "transaction_type": "withdrawal"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)

    # Expected points: 20 (from standard_rule1)
    expected_points = 20
    assert response["transaction_id"] == "txn_amount_rule"
    assert response["risk_points"] == expected_points
    assert response["risk_level"] == determine_risk_level(expected_points)

@pytest.mark.asyncio
async def test_process_transaction_standard_rule_type(mock_db):
    """
    Test a transaction that triggers only the 'Transaction type is transfer' standard rule.
    Amount <= 500, type == 'transfer', velocity count <= 5.
    """
    transaction_data = {
        "transaction_id": "txn_type_rule",
        "user_id": "user_standard_type",
        "amount": 200,
        "transaction_type": "transfer"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)

    # Expected points: 30 (from standard_rule2)
    expected_points = 30
    assert response["transaction_id"] == "txn_type_rule"
    assert response["risk_points"] == expected_points
    assert response["risk_level"] == determine_risk_level(expected_points)

@pytest.mark.asyncio
async def test_process_transaction_both_standard_rules(mock_db):
    """
    Test a transaction that triggers both standard rules.
    Amount > 500, type == 'transfer', velocity count <= 5.
    """
    transaction_data = {
        "transaction_id": "txn_both_standard_rules",
        "user_id": "user_both_standard",
        "amount": 700,
        "transaction_type": "transfer"
    }
    from .api import process_transaction
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db)

    # Expected points: 20 (standard_rule1) + 30 (standard_rule2) = 50
    expected_points = 50
    assert response["transaction_id"] == "txn_both_standard_rules"
    assert response["risk_points"] == expected_points
    assert response["risk_level"] == determine_risk_level(expected_points)

@pytest.mark.asyncio
async def test_process_transaction_velocity_rule(mock_db):
    """
    Test a transaction that triggers the velocity rule.
    This requires inserting multiple transactions for the same user within the time window.
    For simplicity in this unit test, we will mock the evaluate_velocity_rule function
    to return True for a specific user.
    """
    transaction_data = {
        "transaction_id": "txn_velocity_rule",
        "user_id": "user_velocity",
        "amount": 100,
        "transaction_type": "deposit"
    }
    from .services import evaluate_velocity_rule
    with patch('rules_policy_engine.services.evaluate_velocity_rule', return_value=True) as mock_eval_velocity:
        from .api import process_transaction
        transaction = Transaction(**transaction_data)
        response = await process_transaction(transaction, mock_db=mock_db)

        # Expected points: 40 (from velocity_rule1)
        expected_points = 40
        assert response["transaction_id"] == "txn_velocity_rule"
        assert response["risk_points"] == expected_points
        assert response["risk_level"] == determine_risk_level(expected_points)
        mock_eval_velocity.assert_called_once() # Ensure the mock was called

@pytest.mark.asyncio
async def test_process_transaction_all_rules(mock_db):
    """
    Test a transaction that triggers all three rules.
    Amount > 500, type == 'transfer', velocity count > 5 (mocked).
    """
    transaction_data = {
        "transaction_id": "txn_all_rules",
        "user_id": "user_all_rules",
        "amount": 800,
        "transaction_type": "transfer"
    }
    from .services import evaluate_velocity_rule
    with patch('rules_policy_engine.services.evaluate_velocity_rule', return_value=True) as mock_eval_velocity:
        from .api import process_transaction
        transaction = Transaction(**transaction_data)
        response = await process_transaction(transaction, mock_db=mock_db)

        # Expected points: 20 (standard_rule1) + 30 (standard_rule2) + 40 (velocity_rule1) = 90
        expected_points = 90
        assert response["transaction_id"] == "txn_all_rules"
        assert response["risk_points"] == expected_points
        assert response["risk_level"] == determine_risk_level(expected_points)
        mock_eval_velocity.assert_called_once() # Ensure the mock was called

@pytest.mark.asyncio
async def test_process_transaction_invalid_input_api(mock_db):
    """
    Test the API endpoint /transactions with invalid input data.
    This test uses the TestClient to simulate an API call.
    """
    transaction_data = {
        "transaction_id": "invalid_txn_api",
        "user_id": "test_user",
        "amount": "invalid",  # Invalid amount
        "transaction_type": "deposit"
    }
    # No need to override dependencies here as TestClient uses the app's configured dependencies
    response = client.post("/transactions", json=transaction_data)
    assert response.status_code == 422  # Unprocessable Entity due to validation error
    assert "detail" in response.json() # Check for error detail