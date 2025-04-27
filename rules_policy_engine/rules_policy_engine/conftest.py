import pytest
import mongomock
from .models import StandardRule, VelocityRule, Policy

@pytest.fixture
def mock_db():
    client = mongomock.MongoClient()
    db = mongomock.Database(client, "test_db", _store={})

    # Seed the database with standard rules
    db.standard_rule = db["standard_rule"]
    standard_rule1 = StandardRule(
        rule_type="standard",
        description="Amount greater than 500",
        points=20,
        risk_point=20,
        field="amount",
        operator="greater_than",
        value=500,
    )
    standard_rule2 = StandardRule(
        rule_type="standard",
        description="Transaction type is transfer",
        points=30,
        risk_point=30,
        field="transaction_type",
        operator="equal",
        value="transfer",
    )
    db.standard_rule.insert_many([standard_rule1.model_dump(), standard_rule2.model_dump()])

    # Seed the database with velocity rules
    db.velocity_rule = db["velocity_rule"]
    velocity_rule1 = VelocityRule(
        rule_type="velocity",
        description="High transaction velocity",
        points=40,
        risk_point=40,
        field="user_id",
        time_range="1 hour",
        aggregation_function="count",
        threshold=5,
    )
    db.velocity_rule.insert_many([velocity_rule1.model_dump()])

    # Seed the database with policies
    db.policies = db["policies"]
    policy1 = Policy(
        name="High Risk Policy",
        description="Policy to detect high risk transactions",
        rules=[standard_rule1, standard_rule2, velocity_rule1],
    )
    db.policies.insert_many([policy1.model_dump()])

    # Seed the database with sample users
    db.users = db["users"]
    user1 = {"user_id": "user1", "risk_score": 50}
    user2 = {"user_id": "user2", "risk_score": 20}
    db.users.insert_many([user1, user2])

    # Seed the database with sample transactions
    db.transactions = db["transactions"]
    transaction1 = {
        "transaction_id": "txn1",
        "user_id": "user1",
        "amount": 1000,
        "transaction_type": "transfer",
    }  # Positive fraud
    transaction2 = {
        "transaction_id": "txn2",
        "user_id": "user2",
        "amount": 100,
        "transaction_type": "deposit",
    }  # Negative fraud
    db.transactions.insert_many([transaction1, transaction2])

    yield db