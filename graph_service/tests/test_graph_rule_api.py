import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from graph_service.main import app
from graph_service.models import GraphRule
from common.config import MONGODB_DB_NAME
import pytest
from bson.objectid import ObjectId

@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from graph_service.main import app
    return TestClient(app)

async def test_create_graph_rule(mock_db, test_client):
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    response = test_client.post("/graph_rules/", json=rule_data)
    assert response.status_code == 200
    created_rule = response.json()
    assert created_rule['name'] == rule_data['name']
    assert await mock_db.graph_rules.find_one({"name": rule_data['name']}) is not None

async def test_read_graph_rule(mock_db, test_client):
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    response = test_client.get(f"/graph_rules/{rule_id}")
    assert response.status_code == 200
    read_rule = response.json()
    assert read_rule['name'] == rule_data['name']
    assert read_rule['id'] == rule_id

async def test_read_graph_rule_not_found(mock_db, test_client):
    response = test_client.get("/graph_rules/000000000000000000000000")
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]

async def test_update_graph_rule(mock_db, test_client):
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    updated_data = rule_data.copy()
    updated_data['description'] = "Updated description"
    # Convert ObjectId to string for JSON serialization
    for key, value in updated_data.items():
        if isinstance(value, ObjectId):
            updated_data[key] = str(value)
    response = test_client.put(f"/graph_rules/{rule_id}", json=updated_data)
    assert response.status_code == 200
    updated_rule = response.json()
    assert updated_rule['description'] == "Updated description"
    db_rule = await mock_db.graph_rules.find_one({"_id": ObjectId(rule_id)})
    assert db_rule['description'] == "Updated description"

async def test_update_graph_rule_not_found(mock_db, test_client):
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    response = test_client.put("/graph_rules/000000000000000000000000", json=rule_data)
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]

async def test_delete_graph_rule(mock_db, test_client):
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    response = test_client.delete(f"/graph_rules/{rule_id}")
    assert response.status_code == 200
    assert "Graph rule deleted successfully" in response.json()["message"]
    assert await mock_db.graph_rules.find_one({"_id": ObjectId(rule_id)}) is None

async def test_delete_graph_rule_not_found(mock_db, test_client):
    response = test_client.delete("/graph_rules/000000000000000000000000")
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]