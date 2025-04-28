import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from graph_service.main import app
from graph_service.models import Link
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
    user_id = f"user_{generate_random_string(5)}"
    return {
        "id_user": user_id,
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

async def test_create_link(mock_db, test_client):
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    test_client.post("/users/", json=user1_data)
    test_client.post("/users/", json=user2_data)
    
    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    response = test_client.post("/links/", json=link_data)
    assert response.status_code == 200
    created_link = response.json()
    assert created_link['source'] == link_data['source']
    assert created_link['target'] == link_data['target']
    assert await mock_db.links.find_one({"source": link_data['source'], "target": link_data['target']}) is not None

async def test_create_link_duplicate(mock_db, test_client):
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    test_client.post("/users/", json=user1_data)
    test_client.post("/users/", json=user2_data)
    
    user1_data_id = str(user1_data['id_user'])
    user2_data_id = str(user2_data['id_user'])
    
    link_data = {"source": user1_data_id, "target": user2_data_id, "type": "test_link", "weight": 0.8}
    # Before inserting, ensure that the _id field is converted to string
    link_data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in link_data.items()}
    # Before inserting, ensure that the _id field is converted to string
    #link_data = {k: str(v) if isinstance(v, ObjectId) else v for k, v in link_data.items()}
    await mock_db.links.insert_one(link_data) # Create the link first
    
    # Convert ObjectId to string before calling test_client.post
    #link_data['_id'] = str(link_data['_id']) if '_id' in link_data else None
    
    response = None
    try:
        response = test_client.post("/links/", json=link_data) # Attempt to create again
        assert response.status_code == 400
        detail = response.json()["detail"]
    
        assert "Link between these users already exists" in detail
    except TypeError as e:
        print(f"Error decoding JSON: {e}")
        if response:
            print(f"Response content: {response.content}")
        raise

async def test_read_link(mock_db, test_client):
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    await mock_db.users.insert_one(user1_data)
    await mock_db.users.insert_one(user2_data)
    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    await mock_db.links.insert_one(link_data)
    
    response = test_client.get(f"/links/{link_data['source']}/{link_data['target']}")
    assert response.status_code == 200
    read_link = response.json()
    assert read_link['source'] == link_data['source']
    assert read_link['target'] == link_data['target']

async def test_read_link_not_found(mock_db, test_client):
    response = test_client.get("/links/user1/user2")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]

async def test_delete_link(mock_db, test_client):
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    test_client.post("/users/", json=user1_data)
    test_client.post("/users/", json=user2_data)
    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    await mock_db.links.insert_one(link_data)
    # Nodes and edges are added to the graph by the respective service functions, not directly in the test
    
    response = test_client.delete(f"/links/{link_data['source']}/{link_data['target']}")
    assert response.status_code == 200
    assert "Link deleted successfully" in response.json()["message"]
    assert await mock_db.links.find_one({"source": link_data['source'], "target": link_data['target']}) is None

async def test_delete_link_not_found(mock_db, test_client):
    response = test_client.delete("/links/user1/user2")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]