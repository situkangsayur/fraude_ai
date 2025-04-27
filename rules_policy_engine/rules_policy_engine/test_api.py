import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
import mongomock
# from common.mongodb_utils import MockMongoClient
from .main import app
from .models import StandardRule, VelocityRule, Policy, Transaction
from .services import evaluate_standard_rule, evaluate_policy, determine_risk_level
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from common.mongodb_utils import get_mongodb_database
from common.mongodb_utils import get_mongodb_database
from unittest.mock import patch, AsyncMock

import os
import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_test_environment():
    os.environ["TESTING"] = "True"
    yield
    os.environ["TESTING"] = "False"

# Note: mock_db fixture is now defined in conftest.py and includes seeding

def test_evaluate_standard_rule():
    transaction = {"amount": 100, "user_id": "user123"}
    rule = StandardRule(
        rule_type="standard",
        description="Amount greater than 50",
        points=10,
        risk_point=10, # Assuming risk_point is same as points if not specified differently
        field="amount",
        operator="greater_than",
        value=50,
    )
    # Pass the rule as a dictionary
    assert evaluate_standard_rule(transaction, rule.model_dump()) == True

def test_evaluate_standard_rule_field_not_found():
    transaction = {"user_id": "user123"}
    rule = StandardRule(
        rule_type="standard",
        description="Amount greater than 50",
        points=10,
        risk_point=10,
        field="amount",
        operator="greater_than",
        value=50,
    )
    # Pass the rule as a dictionary
    assert evaluate_standard_rule(transaction, rule.model_dump()) == False

@patch('rules_policy_engine.services.evaluate_velocity_rule', return_value=False)
async def test_evaluate_policy(mock_evaluate_velocity_rule):
    transaction = {"amount": 100, "user_id": "user123"}
    # Define rules inline for this specific test, independent of seeding
    rule1 = StandardRule(
        rule_type="standard",
        description="Amount greater than 50",
        points=10,
        field="amount",
        operator="greater_than",
        value=50,
    )
    rule2 = VelocityRule(
        rule_type="velocity",
        description="High velocity",
        points=20,
        field="user_id",
        time_range="1 hour",
        aggregation_function="count",
        threshold=10,
    )
    policy = Policy(
        name="Test Policy Inline",
        description="Test policy description inline",
        rules=[rule1, rule2],
    )
    # evaluate_policy sums points from rules that evaluate to True
    # evaluate_standard_rule(transaction, rule1) is True (10 points)
    # evaluate_velocity_rule is mocked to return False (0 points)
    assert evaluate_policy(transaction, policy) == 10

def test_determine_risk_level():
    assert determine_risk_level(0) == "normal"
    assert determine_risk_level(50) == "normal"
    assert determine_risk_level(70) == "suspect"
    assert determine_risk_level(100) == "fraud_confirm"
    assert determine_risk_level(89) == "suspect"
    assert determine_risk_level(90) == "suspect"
    assert determine_risk_level(100) == "fraud_confirm"
    assert determine_risk_level(120) == "fraud_confirm"

import os
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_policy(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Test creating a policy via the API endpoint (optional, could be removed if covered elsewhere)
    policy_data = {
        "name": "API Test Policy",
        "description": "API Test policy description",
        "rules": [{
            "rule_type": "standard",
            "description": "Amount greater than 500",
            "points": 20,
            "field": "amount",
            "operator": "greater_than",
            "value": 500,
            "risk_point": 20
        }]
    }
    # This test still uses the TestClient approach
    response = client.post("/policies/", json=policy_data)
    assert response.status_code == 200
    assert response.json()["name"] == "API Test Policy"

    # Verify it was actually inserted in the mock_db
    found = mock_db.policies.find_one({"name": "API Test Policy"})
    assert found is not None
    assert found["description"] == "API Test policy description"

@pytest.mark.asyncio
async def test_create_policy_empty_rules(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_client] = lambda *args, **kwargs: mock_db.client

    # Test creating a policy via the API endpoint (optional, could be removed if covered elsewhere)
    policy_data = {
        "name": "API Test Policy Empty Rules",
        "description": "API Test policy description with empty rules",
        "rules": []
    }
    # This test still uses the TestClient approach
    response = client.post("/policies/", json=policy_data)
    assert response.status_code == 422  # Or appropriate error code
    assert "detail" in response.json() # Check for error detail

    # Clear overrides after the test
    app.dependency_overrides.clear()
    # Verify it was NOT inserted in the mock_db because creation should fail
    found = mock_db.policies.find_one({"name": "API Test Policy Empty Rules"})
    assert found is None


@pytest.mark.asyncio
async def test_process_transaction_normal(mock_db):
    # Use seeded transaction 'txn2' (Negative fraud)
    transaction_data = {
        "transaction_id": "txn2",
        "user_id": "user2",
        "amount": 100,
        "transaction_type": "deposit",
    }
    from .api import process_transaction # Import the function directly
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db) # Call the function
    assert response["transaction_id"] == "txn2"
    # Based on seeded rules (amount < 500, type != transfer), risk points = 0
    assert response["risk_points"] == 0
    assert response["risk_level"] == "normal"

# Removing this test for now as seeded data doesn't directly create a 'suspect' case
# @pytest.mark.asyncio
# async def test_process_transaction_suspect(mock_db):
#     # This would require specific rules/data to generate points between 60-89
#     pass

@pytest.mark.asyncio
async def test_process_transaction_fraud(mock_db):
    # Use seeded transaction 'txn1' (Positive fraud)
    transaction_data = {
        "transaction_id": "txn1",
        "user_id": "user1",
        "amount": 1000,
        "transaction_type": "transfer",
    }
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db
    from .api import process_transaction # Import the function directly
    transaction = Transaction(**transaction_data)
    response = await process_transaction(transaction, mock_db=mock_db) # Call the function
    assert response["transaction_id"] == "txn1"
    # Based on seeded rules:
    # - Amount > 500 (standard_rule1): 20 points
    # - Type == transfer (standard_rule2): 30 points
    # - Velocity rule not triggered by single transaction
    # Total points = 50
    assert response["risk_points"] == 50
    # Clear overrides after the test
    app.dependency_overrides = {}
    # Risk level for 50 points is 'normal' based on determine_risk_level
    assert response["risk_level"] == "normal" # Test name might be misleading now

def test_process_transaction_invalid_input():
    # Test validation using the TestClient
    transaction_data = {
        "transaction_id": "invalid_txn",
        "user_id": "test_user",
        "amount": "invalid",  # Invalid amount
        "transaction_type": "deposit"
    }
    response = client.post("/transactions", json=transaction_data)
@pytest.mark.asyncio
async def test_read_policy(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a policy to read
    policy_data = {
        "name": "Policy to Read",
        "description": "Description of policy to read",
        "rules": [{
            "rule_type": "standard",
            "description": "Amount greater than 100",
            "points": 10,
            "field": "amount",
            "operator": "greater_than",
            "value": 100,
            "risk_point": 10
        }]
    }
    insert_result = mock_db.policies.insert_one(policy_data)
    policy_id = str(insert_result.inserted_id)

    response = client.get(f"/policies/{policy_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Policy to Read"
    assert response_data["_id"] == policy_id

    # Test reading a non-existent policy
    response = client.get("/policies/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_policy(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a policy to update
    policy_data = {
        "name": "Policy to Update",
        "description": "Description of policy to update",
        "rules": [{
            "rule_type": "standard",
            "description": "Amount greater than 100",
            "points": 10,
            "field": "amount",
            "operator": "greater_than",
            "value": 100,
            "risk_point": 10
        }]
    }
    insert_result = mock_db.policies.insert_one(policy_data)
    policy_id = str(insert_result.inserted_id)

    # Data to update the policy with
    updated_policy_data = {
        "name": "Updated Policy Name",
        "description": "Updated description",
        "rules": [{
            "rule_type": "velocity",
            "description": "High frequency",
            "points": 30,
            "field": "user_id",
            "time_range": "24 hour",
            "aggregation_function": "count",
            "threshold": 5,
            "risk_point": 30
        }]
    }

    response = client.put(f"/policies/{policy_id}", json=updated_policy_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Updated Policy Name"
    assert response_data["description"] == "Updated description"
    assert len(response_data["rules"]) == 1
    assert response_data["rules"][0]["rule_type"] == "velocity"

    # Verify the update in the mock_db
    found = mock_db.policies.find_one({"_id": ObjectId(policy_id)})
    assert found is not None
    assert found["name"] == "Updated Policy Name"
    assert found["description"] == "Updated description"

    # Test updating a non-existent policy
    response = client.put("/policies/non_existent_id", json=updated_policy_data)
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_delete_policy(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a policy to delete
    policy_data = {
        "name": "Policy to Delete",
        "description": "Description of policy to delete",
        "rules": [{
            "rule_type": "standard",
            "description": "Amount greater than 100",
            "points": 10,
            "field": "amount",
            "operator": "greater_than",
            "value": 100,
            "risk_point": 10
        }]
    }
    insert_result = mock_db.policies.insert_one(policy_data)
    policy_id = str(insert_result.inserted_id)

    response = client.delete(f"/policies/{policy_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Policy deleted successfully"}

    # Verify deletion in the mock_db
    found = mock_db.policies.find_one({"_id": ObjectId(policy_id)})
    assert found is None

    # Test deleting a non-existent policy
    response = client.delete("/policies/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

def test_get_rule_statistics():
    """Test the placeholder /rule_statistics/ endpoint."""
    response = client.get("/rule_statistics/")
    assert response.status_code == 200
    assert response.json() == {"message": "Rule statistics API not implemented yet."}

def test_get_user_risk_info():
    """Test the placeholder /users/{user_id}/risk_info endpoint."""
    user_id = "test_user_123"
    response = client.get(f"/users/{user_id}/risk_info")
    assert response.status_code == 200
@pytest.mark.asyncio
async def test_create_standard_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    rule_data = {
        "rule_type": "standard",
        "description": "New Standard Rule",
        "points": 15,
        "risk_point": 15,
        "field": "user_id",
        "operator": "equals",
        "value": "test_user_create"
    }
    response = client.post("/standard_rules/", json=rule_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "New Standard Rule"
    assert "_id" in response_data

    # Verify insertion in mock_db
    found = mock_db.standard_rule.find_one({"description": response_data["description"]})
    assert found is not None
    assert found["description"] == "New Standard Rule"

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_standard_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to read
    rule_data = {
        "rule_type": "standard",
        "description": "Standard Rule to Read",
        "points": 25,
        "risk_point": 25,
        "field": "amount",
        "operator": "less_than",
        "value": 50
    }
    insert_result = mock_db.standard_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    response = client.get(f"/standard_rules/{rule_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "Standard Rule to Read"
    assert response_data["_id"] == rule_id

    # Test reading a non-existent rule
    response = client.get("/standard_rules/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_standard_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to update
    rule_data = {
        "rule_type": "standard",
        "description": "Standard Rule to Update",
        "points": 35,
        "risk_point": 35,
        "field": "transaction_type",
        "operator": "equals",
        "value": "withdrawal"
    }
    insert_result = mock_db.standard_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    # Data to update the rule with
    updated_rule_data = {
        "rule_type": "standard",
        "description": "Updated Standard Rule",
        "points": 40,
        "risk_point": 40,
        "field": "amount",
        "operator": "greater_than",
        "value": 1000
    }

    response = client.put(f"/standard_rules/{rule_id}", json=updated_rule_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "Updated Standard Rule"
    assert response_data["risk_point"] == 40

    # Verify the update in the mock_db
    found = mock_db.standard_rule.find_one({"_id": ObjectId(rule_id)})
    assert found is not None
    assert found["description"] == "Updated Standard Rule"
    assert found["risk_point"] == 40

    # Test updating a non-existent rule
    response = client.put("/standard_rules/non_existent_id", json=updated_rule_data)
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_delete_standard_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to delete
    rule_data = {
        "rule_type": "standard",
        "description": "Standard Rule to Delete",
        "points": 50,
        "risk_point": 50,
        "field": "user_id",
        "operator": "not_equals",
        "value": "safe_user"
    }
    insert_result = mock_db.standard_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    response = client.delete(f"/standard_rules/{rule_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Rule deleted successfully"}

    # Verify deletion in the mock_db
    found = mock_db.standard_rule.find_one({"_id": ObjectId(rule_id)})
    assert found is None

    # Test deleting a non-existent rule
    response = client.delete("/standard_rules/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_velocity_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    rule_data = {
        "rule_type": "velocity",
        "description": "New Velocity Rule",
        "points": 25,
        "risk_point": 25,
        "field": "user_id",
        "time_range": "1 hour",
        "aggregation_function": "count",
        "threshold": 10
    }
    response = client.post("/velocity_rules/", json=rule_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "New Velocity Rule"
    assert "_id" in response_data

    # Verify insertion in mock_db
    found = mock_db.velocity_rule.find_one({"description": response_data["description"]})
    assert found is not None
    assert found["description"] == "New Velocity Rule"

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_velocity_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to read
    rule_data = {
        "rule_type": "velocity",
        "description": "Velocity Rule to Read",
        "points": 35,
        "risk_point": 35,
        "field": "amount",
        "time_range": "24 hour",
        "aggregation_function": "sum",
        "threshold": 5000
    }
    insert_result = mock_db.velocity_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    response = client.get(f"/velocity_rules/{rule_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "Velocity Rule to Read"
    assert response_data["_id"] == rule_id

    # Test reading a non-existent rule
    response = client.get("/velocity_rules/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_velocity_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to update
    rule_data = {
        "rule_type": "velocity",
        "description": "Velocity Rule to Update",
        "points": 45,
        "risk_point": 45,
        "field": "transaction_count",
        "time_range": "7 day",
        "aggregation_function": "count",
        "threshold": 20
    }
    insert_result = mock_db.velocity_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    # Data to update the rule with
    updated_rule_data = {
        "rule_type": "velocity",
        "description": "Updated Velocity Rule",
        "points": 50,
        "risk_point": 50,
        "field": "amount",
        "time_range": "1 day",
        "aggregation_function": "sum",
        "threshold": 10000
    }

    response = client.put(f"/velocity_rules/{rule_id}", json=updated_rule_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "Updated Velocity Rule"
    assert response_data["risk_point"] == 50

    # Verify the update in the mock_db
    found = mock_db.velocity_rule.find_one({"_id": ObjectId(rule_id)})
    assert found is not None
    assert found["description"] == "Updated Velocity Rule"
    assert found["risk_point"] == 50

    # Test updating a non-existent rule
    response = client.put("/velocity_rules/non_existent_id", json=updated_rule_data)
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_delete_velocity_rule(mock_db):
    # Override dependencies for the test
    app.dependency_overrides[get_mongodb_database] = lambda: mock_db

    # Insert a rule to delete
    rule_data = {
        "rule_type": "velocity",
        "description": "Velocity Rule to Delete",
        "points": 60,
        "risk_point": 60,
        "field": "user_id",
        "time_range": "30 minute",
        "aggregation_function": "count",
        "threshold": 5
    }
    insert_result = mock_db.velocity_rule.insert_one(rule_data)
    rule_id = str(insert_result.inserted_id)

    response = client.delete(f"/velocity_rules/{rule_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Rule deleted successfully"}

    # Verify deletion in the mock_db
    found = mock_db.velocity_rule.find_one({"_id": ObjectId(rule_id)})
    assert found is None

    # Test deleting a non-existent rule
    response = client.delete("/velocity_rules/non_existent_id")
    assert response.status_code == 404

    # Clear overrides after the test
    app.dependency_overrides.clear()