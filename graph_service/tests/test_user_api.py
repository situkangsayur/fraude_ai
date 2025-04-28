import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from graph_service.main import app
from graph_service.models import UserNode
from common.config import MONGODB_DB_NAME
import string
import random
import pytest
import json
from bson.objectid import ObjectId

@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from graph_service.main import app
    return TestClient(app)

def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_user_data(is_fraud=False):
    return {
        "id_user": f"user_{generate_random_string(5)}",
        "nama_lengkap": f"Nama {generate_random_string(7)}",
        "email": f"{generate_random_string(5)}@{generate_random_string(5)}.com",
        "domain_email": f"{generate_random_string(5)}.com",
        "address": f"Address {generate_random_string(10)}",
        "address_zip": str(random.randint(10000, 99999)),
        "address_city": f"City {generate_random_string(5)}",
        "address_province": f"Province {generate_random_string(5)}",
        "address_kecamatan": f"Kecamatan {generate_random_string(5)}",
        "phone_number": f"08{random.randint(100000000, 999999999)}",
        "is_fraud": is_fraud
    }

async def test_create_user(mock_db, test_client):
    user_data = generate_user_data()
    response = test_client.post("/users/", json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user['id_user'] == user_data['id_user']
    assert await mock_db.users.find_one({"id_user": user_data['id_user']}) is not None

async def test_create_user_duplicate_id(mock_db, test_client):
    user_data = generate_user_data()
    response1 = test_client.post("/users/", json=user_data) # Create the user first
    assert response1.status_code == 200
    
    # Serialize ObjectId to string
    #user_data['id_user'] = str(user_data['id_user'])
    
    response = test_client.post("/users/", json=user_data) # Attempt to create again
    assert response.status_code == 400
    assert "User with this ID already exists" in response.json()["detail"]

async def test_create_user_missing_data(mock_db, test_client):
    user_data = generate_user_data()
    del user_data["nama_lengkap"]
    response = test_client.post("/users/", json=user_data)
    assert response.status_code == 422  # Unprocessable Entity
    assert "field required" in response.json()["detail"][0]["msg"]


async def test_read_user(mock_db, test_client):
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    response = test_client.get(f"/users/{user_data['id_user']}")
    assert response.status_code == 200
    read_user = response.json()
    assert read_user['id_user'] == user_data['id_user']

async def test_read_user_not_found(mock_db, test_client):
    response = test_client.get("/users/non_existent_user")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

async def test_update_user_invalid_data(mock_db, test_client):
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    updated_data = user_data.copy()
    updated_data['email'] = "invalid-email"
    
    # Serialize ObjectId to string
    for key, value in updated_data.items():
        if isinstance(value, ObjectId):
            updated_data[key] = str(value)
    
    response = test_client.put(f"/users/{user_data['id_user']}", json=updated_data)
    assert response.status_code == 422
    assert "value is not a valid email address" in response.json()["detail"][0]["msg"]


async def test_read_user_invalid_id(mock_db, test_client):
    response = test_client.get("/users/invalid_user_id")
    assert response.status_code == 422
    assert "value is not a valid ObjectId" in response.json()["detail"][0]["msg"]


async def test_update_user(mock_db, test_client):
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    updated_data = user_data.copy()
    updated_data['nama_lengkap'] = "Updated Name"
    
    # Serialize ObjectId to string
    for key, value in updated_data.items():
        if isinstance(value, ObjectId):
            updated_data[key] = str(value)
    
    response = test_client.put(f"/users/{user_data['id_user']}", json=updated_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user['nama_lengkap'] == "Updated Name"
    db_user = await mock_db.users.find_one({"id_user": user_data['id_user']})
    assert db_user['nama_lengkap'] == "Updated Name"

async def test_update_user_not_found(mock_db, test_client):
    user_data = generate_user_data()
    response = test_client.put("/users/non_existent_user", json=user_data)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

async def test_delete_user(mock_db, test_client):
    user_data = generate_user_data()
    mock_db.users.insert_one(user_data)
    # Add a link to the user to test link deletion
    link_data = {"source": user_data['id_user'], "target": "another_user", "type": "test_link"}
    mock_db.links.insert_one(link_data)
    # Nodes and edges are added to the graph by the respective service functions, not directly in the test
    
    response = test_client.delete(f"/users/{user_data['id_user']}")
    assert response.status_code == 200
    assert "User deleted successfully" in response.json()["message"]
    assert mock_db.users.find_one({"id_user": user_data['id_user']}) is None
    assert mock_db.links.find_one({"source": user_data['id_user']}) is None
    assert mock_db.links.find_one({"target": user_data['id_user']}) is None

async def test_delete_user_not_found(mock_db, test_client):
    response = test_client.delete("/users/non_existent_user")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]