import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from graph_service.main import app
from graph_service.models import UserNode, GraphRule, Link, Cluster # Import Cluster model
from graph_service.services import initialize_graph_db, graph, db # Import graph and db from services
from common.config import MONGODB_DB_NAME
import networkx as nx
from unittest.mock import patch, AsyncMock # Import AsyncMock
import random
import string
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

async def seed_data(db):
    # Seed normal users (30)
    normal_users = [generate_user_data(is_fraud=False) for _ in range(30)]
    await db.users.insert_many(normal_users)

    # Seed fraud users (10) in 4 clusters
    fraud_users = []
    for i in range(4): # 4 clusters
        cluster_size = 2 if i < 2 else 3 # Two clusters of 2, two of 3 (total 4 + 6 = 10)
        common_domain = f"fraudcluster{i}.com"
        common_zip = str(10000 + i)
        for j in range(cluster_size):
            user_data = generate_user_data(is_fraud=True)
            user_data["domain_email"] = common_domain
            user_data["address_zip"] = common_zip
            fraud_users.append(user_data)
    await db.users.insert_many(fraud_users)

    # Add some graph rules for link generation
    rules = [
        {"name": "email_domain_match", "description": "Matching email domains", "field1": "domain_email", "operator": "equal"},
        {"name": "zip_code_match_rule", "description": "Matching address_zip", "field1": "address_zip", "operator": "equal"},
    ]
    await db.graph_rules.insert_many(rules)

@pytest.fixture(scope="function")
async def setup_and_seed_db():
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    # Seed the database with sample data
    users = [generate_user_data(is_fraud=False) for _ in range(30)]
    await mock_db.users.insert_many(users)

    # Seed fraud users (10) in 4 clusters
    fraud_users = []
    for i in range(4): # 4 clusters
        cluster_size = 2 if i < 2 else 3 # Two clusters of 2, two of 3 (total 4 + 6 = 10)
        common_domain = f"fraudcluster{i}.com"
        common_zip = str(10000 + i)
        for j in range(cluster_size):
            user_data = generate_user_data(is_fraud=True)
            user_data["domain_email"] = common_domain
            user_data["address_zip"] = common_zip
            fraud_users.append(user_data)
    await mock_db.users.insert_many(fraud_users)

    # Add some graph rules for link generation
    rules = [
        {"name": "email_domain_match", "description": "Matching email domains", "field1": "domain_email", "operator": "equal"},
        {"name": "zip_code_match_rule", "description": "Matching address_zip", "field1": "address_zip", "operator": "equal"},
    ]
    await mock_db.graph_rules.insert_many(rules)
    yield mock_db

async def test_generate_links(setup_and_seed_db, test_client):
    # Use mock_db directly to ensure a clean state without seeded links
    #await seed_data(mock_db) # Seed users and rules, but not links in this test

    # Clear links collection to ensure a clean state for this test
    await setup_and_seed_db.links.delete_many({})

    # Ensure no links exist initially
    assert await setup_and_seed_db.links.count_documents({}) == 0

    # Call the generate_links endpoint
    response = test_client.post("/generate_links/")
    assert response.status_code == 200
    assert "Links generated successfully" in response.json()["message"]

    # Verify links are created in the mock database
    assert await setup_and_seed_db.links.count_documents({}) > 0

async def test_analyze_transaction_no_fraudsters(setup_and_seed_db):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    # Remove all fraud users for this test
    await mock_db.users.delete_many({"is_fraud": True})

    # Generate links to ensure some connections exist
    client.post("/generate_links/")

    # Get a non-fraudulent user ID
    normal_user = await mock_db.users.find_one({"is_fraud": False})
    assert normal_user is not None
    user_id = normal_user['id_user']

    transaction_data = {"id_user": user_id}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 200
    analysis_result = response.json()
    assert analysis_result['user_id'] == user_id
    assert analysis_result['proximity_score'] == 0.0
    assert analysis_result['shortest_path_length_to_fraudster'] == "No path"
    assert analysis_result['closest_fraudster'] is None
    # linked_fraud_count should be 0 as there are no fraud users
    assert analysis_result['linked_fraud_count'] == 0
    # total_linked_nodes should be greater than 0 if links were generated
    assert analysis_result['total_linked_nodes'] >= 0 # Can be 0 if no links were generated for this user

def test_analyze_transaction_linked_to_fraudster(setup_and_seed_db):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    # Ensure there are fraud users
    fraud_user = mock_db.users.find_one({"is_fraud": True})
    assert fraud_user is not None
    fraud_user_id = fraud_user['id_user']

    # Get a non-fraudulent user
    normal_user = mock_db.users.find_one({"is_fraud": False})
    assert normal_user is not None
    user_id = normal_user['id_user']

    # Create a direct link between the normal user and a fraudster
    link_data = {"source": user_id, "target": fraud_user_id, "type": "direct_fraud_link", "weight": 1.0}
    mock_db.links.insert_one(link_data)
    # The edge is added to the graph by the create_link_service, not directly in the test


    transaction_data = {"id_user": user_id}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 200
    analysis_result = response.json()
    assert analysis_result['user_id'] == user_id
    # Proximity score should be calculated based on shortest path (which is 1)
    assert abs(analysis_result['proximity_score'] - (1.0 / (1 + 1))) < 1e-6 # 1 / (path_length + 1)
    assert analysis_result['shortest_path_length_to_fraudster'] == 1
    assert analysis_result['closest_fraudster'] == fraud_user_id
    # linked_fraud_count should be at least 1
    assert analysis_result['linked_fraud_count'] >= 1
    assert analysis_result['total_linked_nodes'] >= 1
async def test_cluster_nodes(setup_and_seed_db):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    # Ensure no clusters exist initially
    assert await mock_db.clusters.count_documents({}) == 0

    response = client.post("/cluster_nodes/")
    assert response.status_code == 200
    assert "Nodes clustered successfully" in response.json()["message"]

    # Verify clusters are created in the mock database
    assert await mock_db.clusters.count_documents({}) > 0

    # Optional: Verify the number of clusters or members
    # Based on the seeding logic (4 fraud clusters + individual normal users)
    # The number of clusters should be around 4 + 30 = 34, but this can vary
    # depending on how the clustering algorithm handles the normal users.
    # A simpler check is to ensure some clusters were created and that fraud users
    # within the same seeded cluster are in the same database cluster.

    # Get fraud users from the mock DB
    fraud_users_from_db = [user async for user in await mock_db.users.find({"is_fraud": True})] # Use to_list for async find

    # Group fraud users by their seeded cluster properties (domain_email, address_zip)
    seeded_fraud_clusters = {}
    for user in fraud_users_from_db:
        cluster_key = (user.get("domain_email"), user.get("address_zip"))
        if cluster_key not in seeded_fraud_clusters:
            seeded_fraud_clusters[cluster_key] = []
        seeded_fraud_clusters[cluster_key].append(user['id_user'])

    # Verify that users from the same seeded fraud cluster are in the same database cluster
    db_clusters = [cluster async for cluster in await mock_db.clusters.find()] # Use to_list for async find
    for seeded_cluster_members in seeded_fraud_clusters.values():
        if not seeded_cluster_members:
            continue # Skip empty clusters

        first_member_id = seeded_cluster_members[0]
        # Find the database cluster containing the first member
        containing_db_cluster = None
        for db_cluster in db_clusters:
            if first_member_id in db_cluster.get("members", []):
                containing_db_cluster = db_cluster
                break

        assert containing_db_cluster is not None, f"User {first_member_id} not found in any database cluster"

        # Check if all members of the seeded cluster are in this database cluster
        for member_id in seeded_cluster_members:
            assert member_id in containing_db_cluster.get("members", []), f"User {member_id} from seeded cluster not found in the same database cluster as {first_member_id}"

async def test_analyze_transaction_indirectly_linked_to_fraudster(setup_and_seed_db):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    # Ensure there are fraud users
    fraud_users = [user async for user in await mock_db.users.find({"is_fraud": True})] # Use to_list for async find
    assert len(fraud_users) > 0
    fraud_user_id = fraud_users[0]['id_user']

    # Get two non-fraudulent users
    normal_users = [user async for user in setup_and_seed_db.users.find({"is_fraud": False}).limit(2)]
    assert len(normal_users) >= 2
    user1_id = normal_users[0]['id_user']
    user2_id = normal_users[1]['id_user']

    # Create indirect links: user1 -> user2 -> fraudster
    link1_data = {"source": user1_id, "target": user2_id, "type": "indirect_link1", "weight": 0.5}
    link2_data = {"source": user2_id, "target": fraud_user_id, "type": "indirect_link2", "weight": 0.5}
    await setup_and_seed_db.links.insert_one(link1_data)
    await setup_and_seed_db.links.insert_one(link2_data)


    transaction_data = {"id_user": user1_id}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 200
    analysis_result = response.json()
    assert analysis_result['user_id'] == user1_id
    # Shortest path should be 2 (user1 -> user2 -> fraudster)
    assert analysis_result['shortest_path_length_to_fraudster'] == 2
    assert analysis_result['proximity_score'] == 1.0 / (2 + 1) # 1 / (path_length + 1)
    assert analysis_result['closest_fraudster'] == fraud_user_id
    assert analysis_result['linked_fraud_count'] == 0 # user1 is not directly linked to a fraudster
    assert analysis_result['total_linked_nodes'] >= 1 # user1 is linked to user2
def test_analyze_transaction_user_not_in_graph(test_client):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    transaction_data = {"id_user": "non_existent_user"}
    transaction_data = {"id_user": "non_existent_user"}
    # Change to POST request with json body
    response = test_client.post("/analyze", json=transaction_data)
    assert response.status_code == 404
    assert "User ID non_existent_user not found in the graph." in response.json()["detail"]

def test_analyze_transaction_missing_user_id(test_client):
    mock_client = MockMongoClient()
    mock_db = mock_client["test_db"]
    transaction_data = {"some_other_field": "value"}
    transaction_data = {"some_other_field": "value"}
    # Change to POST request with json body
    response = test_client.post("/analyze", json=transaction_data)
    assert response.status_code == 400 # Expect 400 for missing user ID