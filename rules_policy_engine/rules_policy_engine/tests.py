import pytest
from fastapi.testclient import TestClient
from .main import app
from .models import StandardRule, VelocityRule, Policy, Transaction
from .services import evaluate_standard_rule, evaluate_policy, determine_risk_level

client = TestClient(app)

def test_evaluate_standard_rule():
    transaction = {"amount": 100, "user_id": "user123"}
    rule = StandardRule(
        rule_type="standard",
        description="Amount greater than 50",
        points=10,
        field="amount",
        operator="greater_than",
        value=50,
    )
    assert evaluate_standard_rule(transaction, rule) == True

def test_evaluate_standard_rule_field_not_found():
    transaction = {"user_id": "user123"}
    rule = StandardRule(
        rule_type="standard",
        description="Amount greater than 50",
        points=10,
        field="amount",
        operator="greater_than",
        value=50,
    )
    assert evaluate_standard_rule(transaction, rule) == False

def test_evaluate_policy():
    transaction = {"amount": 100, "user_id": "user123"}
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
        name="Test Policy",
        description="Test policy description",
        rules=[rule1, rule2],
    )
    assert evaluate_policy(transaction, policy) == 10

def test_determine_risk_level():
    assert determine_risk_level(50) == "normal"
    assert determine_risk_level(70) == "suspect"
    assert determine_risk_level(100) == "fraud_confirm"
    assert determine_risk_level(120) == "fraud_confirm"

def test_create_policy():
    response = client.post(
        "/policies/",
        json={
            "name": "Test Policy",
            "description": "Test policy description",
            "rules": []
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Test Policy"

# Add more tests for API endpoints and other functions