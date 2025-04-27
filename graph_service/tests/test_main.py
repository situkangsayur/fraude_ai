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

# Mock MongoDB client and database
@pytest.fixture(scope="function")
async def mock_db():
    client = MockMongoClient()
    db = client[MONGODB_DB_NAME]

    # Mock async methods
    db.users.delete_many = AsyncMock(return_value=None)
    db.links.delete_many = AsyncMock(return_value=None)
    db.graph_rules.delete_many = AsyncMock(return_value=None)
    db.clusters.delete_many = AsyncMock(return_value=None)

    # Mock find methods to return iterables
    db.users.find = AsyncMock()
    db.users.find.return_value.to_list = AsyncMock(return_value=[])
    db.links.find = AsyncMock()
    db.links.find.return_value.to_list = AsyncMock(return_value=[])
    db.graph_rules.find = AsyncMock()
    db.graph_rules.find.return_value.to_list = AsyncMock(return_value=[])
    db.clusters.find = AsyncMock()
    db.clusters.find.return_value.to_list = AsyncMock(return_value=[])

    db.users.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="fake_id"))
    db.links.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="fake_id"))
    db.graph_rules.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="fake_id"))
    db.clusters.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="fake_id"))

    db.users.insert_many = AsyncMock(return_value=None)
    db.links.insert_many = AsyncMock(return_value=None)
    db.graph_rules.insert_many = AsyncMock(return_value=None)
    db.clusters.insert_many = AsyncMock(return_value=None)

    db.users.count_documents = AsyncMock(return_value=0)
    db.links.count_documents = AsyncMock(return_value=0)
    db.graph_rules.count_documents = AsyncMock(return_value=0)
    db.clusters.count_documents = AsyncMock(return_value=0)

    return db

# Override the dependency to use the mock database
# Override the dependency to use the mock database
# We need to mock the functions that the service layer uses to get the client and database
# Since initialize_graph_db is now responsible for setting the global db, we can mock that.
# However, the tests directly use mock_db fixture, so we need to ensure the service functions
# use this mock_db. This requires modifying the service functions or mocking them.
# A simpler approach for testing the API layer is to mock the service functions themselves.

# We will mock the service functions that interact with the database and graph
# and ensure they use the mock_db provided by the fixture.

client = TestClient(app)

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
        {"name": "zip_code_match_rule", "description": "Matching address zip codes", "field1": "address_zip", "operator": "equal"},
    ]
    await db.graph_rules.insert_many(rules)

    # Generate links based on seeded data and rules
    # This logic should ideally be in the service, but for testing, we can simulate it here
    # Find users with matching email domains or zip codes and create links
    all_users = list(await db.users.find().to_list(length=None)) # Await find and use to_list
    links_to_create = []
    for i in range(len(all_users)):
        for j in range(i + 1, len(all_users)):
            user1 = all_users[i]
            user2 = all_users[j]

            # Check email domain match rule
            if user1.get("domain_email") and user1["domain_email"] == user2.get("domain_email"):
                 # Avoid creating duplicate links
                 if not await db.links.find_one({"source": user1['id_user'], "target": user2['id_user'], "type": "email_domain_match"}) and \
                   not await db.links.find_one({"source": user2['id_user'], "target": user1['id_user'], "type": "email_domain_match"}):
                    links_to_create.append({
                        "source": user1['id_user'],
                        "target": user2['id_user'],
                        "type": "email_domain_match",
                        "weight": 0.5, # Example weight
                        "reason": "Matching email domains"
                    })

            # Check zip code match rule
            if user1.get("address_zip") and user1["address_zip"] == user2.get("address_zip"):
                 # Avoid creating duplicate links
                 if not await db.links.find_one({"source": user1['id_user'], "target": user2['id_user'], "type": "zip_code_match_rule"}) and \
                   not await db.links.find_one({"source": user2['id_user'], "target": user1['id_user'], "type": "zip_code_match_rule"}):
                    links_to_create.append({
                        "source": user1['id_user'],
                        "target": user2['id_user'],
                        "type": "zip_code_match_rule",
                        "weight": 0.7, # Example weight
                        "reason": "Matching address zip codes"
                    })

    if links_to_create:
        await db.links.insert_many(links_to_create)


@pytest.fixture(scope="function")
async def setup_and_seed_db(mock_db):
    # Patch the global db and graph objects and the mongodb utils in the services module
    with patch('graph_service.services.db', mock_db), \
         patch('graph_service.services.graph', nx.Graph()) as mock_graph, \
         patch('common.mongodb_utils.get_mongodb_client', return_value=mock_db.client), \
         patch('common.mongodb_utils.get_mongodb_database', return_value=mock_db):
        # Initialize the graph with data from the mocked database
        await initialize_graph_db()
        await seed_data(mock_db)
        yield mock_db

@pytest.mark.asyncio
async def test_create_user(mock_db):
    mock_db = await mock_db
    user_data = generate_user_data()
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user['id_user'] == user_data['id_user']
    assert await mock_db.users.find_one({"id_user": user_data['id_user']}) is not None

@pytest.mark.asyncio
async def test_create_user_duplicate_id(mock_db):
    mock_db = await mock_db
    user_data = generate_user_data()
    client.post("/users/", json=user_data) # Create the user first
    response = client.post("/users/", json=user_data) # Attempt to create again
    assert response.status_code == 400
    assert "User with this ID already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_user(mock_db):
    mock_db = await mock_db
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    response = client.get(f"/users/{user_data['id_user']}")
    assert response.status_code == 200
    read_user = response.json()
    assert read_user['id_user'] == user_data['id_user']

def test_read_user_not_found():
    response = client.get("/users/non_existent_user")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_user(mock_db):
    mock_db = await mock_db
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    updated_data = user_data.copy()
    updated_data['nama_lengkap'] = "Updated Name"
    # Convert ObjectId to string for JSON serialization
    for key, value in updated_data.items():
        if isinstance(value, ObjectId):
            updated_data[key] = str(value)
    response = client.put(f"/users/{user_data['id_user']}", json=updated_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user['nama_lengkap'] == "Updated Name"
    db_user = await mock_db.users.find_one({"id_user": user_data['id_user']})
    assert db_user['nama_lengkap'] == "Updated Name"

def test_update_user_not_found():
    user_data = generate_user_data()
    response = client.put("/users/non_existent_user", json=user_data)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user(mock_db):
    mock_db = await mock_db
    user_data = generate_user_data()
    await mock_db.users.insert_one(user_data)
    # Add a link to the user to test link deletion
    link_data = {"source": user_data['id_user'], "target": "another_user", "type": "test_link"}
    await mock_db.links.insert_one(link_data)
    # Nodes and edges are added to the graph by the respective service functions, not directly in the test

    response = client.delete(f"/users/{user_data['id_user']}")
    assert response.status_code == 200
    assert "User deleted successfully" in response.json()["message"]
    assert await mock_db.users.find_one({"id_user": user_data['id_user']}) is None
    assert await mock_db.links.find_one({"source": user_data['id_user']}) is None
    assert await mock_db.links.find_one({"target": user_data['id_user']}) is None

def test_delete_user_not_found():
    response = client.delete("/users/non_existent_user")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_link(mock_db):
    mock_db = await mock_db
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    client.post("/users/", json=user1_data)
    client.post("/users/", json=user2_data)

    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    response = client.post("/links/", json=link_data)
    assert response.status_code == 200
    created_link = response.json()
    assert created_link['source'] == link_data['source']
    assert created_link['target'] == link_data['target']
    assert await mock_db.links.find_one({"source": link_data['source'], "target": link_data['target']}) is not None

@pytest.mark.asyncio
async def test_create_link_duplicate(mock_db):
    mock_db = await mock_db
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    client.post("/users/", json=user1_data)
    client.post("/users/", json=user2_data)

    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    await mock_db.links.insert_one(link_data) # Create the link first
    response = client.post("/links/", json=link_data) # Attempt to create again
    assert response.status_code == 400
    assert "Link between these users already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_link(mock_db):
    mock_db = await mock_db
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    await mock_db.users.insert_one(user1_data)
    await mock_db.users.insert_one(user2_data)
    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    await mock_db.links.insert_one(link_data)

    response = client.get(f"/links/{link_data['source']}/{link_data['target']}")
    assert response.status_code == 200
    read_link = response.json()
    assert read_link['source'] == link_data['source']
    assert read_link['target'] == link_data['target']

def test_read_link_not_found():
    response = client.get("/links/user1/user2")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_link(mock_db):
    mock_db = await mock_db
    user1_data = generate_user_data()
    user2_data = generate_user_data()
    # Create users via the endpoint to ensure they are added to the graph by the service
    client.post("/users/", json=user1_data)
    client.post("/users/", json=user2_data)
    link_data = {"source": user1_data['id_user'], "target": user2_data['id_user'], "type": "test_link", "weight": 0.8}
    await mock_db.links.insert_one(link_data)
    # Nodes and edges are added to the graph by the respective service functions, not directly in the test

    response = client.delete(f"/links/{link_data['source']}/{link_data['target']}")
    assert response.status_code == 200
    assert "Link deleted successfully" in response.json()["message"]
    assert await mock_db.links.find_one({"source": link_data['source'], "target": link_data['target']}) is None

def test_delete_link_not_found():
    response = client.delete("/links/user1/user2")
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_graph_rule(mock_db):
    mock_db = await mock_db
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    response = client.post("/graph_rules/", json=rule_data)
    assert response.status_code == 200
    created_rule = response.json()
    assert created_rule['name'] == rule_data['name']
    assert await mock_db.graph_rules.find_one({"name": rule_data['name']}) is not None

@pytest.mark.asyncio
async def test_read_graph_rule(mock_db):
    mock_db = await mock_db
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    response = client.get(f"/graph_rules/{rule_id}")
    assert response.status_code == 200
    read_rule = response.json()
    assert read_rule['name'] == rule_data['name']
    assert read_rule['id'] == rule_id

def test_read_graph_rule_not_found():
    response = client.get("/graph_rules/000000000000000000000000")
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_graph_rule(mock_db):
    mock_db = await mock_db
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    updated_data = rule_data.copy()
    updated_data['description'] = "Updated description"
    # Convert ObjectId to string for JSON serialization
    for key, value in updated_data.items():
        if isinstance(value, ObjectId):
            updated_data[key] = str(value)
    response = client.put(f"/graph_rules/{rule_id}", json=updated_data)
    assert response.status_code == 200
    updated_rule = response.json()
    assert updated_rule['description'] == "Updated description"
    db_rule = await mock_db.graph_rules.find_one({"_id": result.inserted_id})
    assert db_rule['description'] == "Updated description"

def test_update_graph_rule_not_found():
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    response = client.put("/graph_rules/000000000000000000000000", json=rule_data)
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_graph_rule(mock_db):
    mock_db = await mock_db
    rule_data = {"name": "test_rule", "description": "A test rule", "field1": "email", "operator": "contains", "value": "@example.com"}
    result = await mock_db.graph_rules.insert_one(rule_data)
    rule_id = str(result.inserted_id)
    response = client.delete(f"/graph_rules/{rule_id}")
    assert response.status_code == 200
    assert "Graph rule deleted successfully" in response.json()["message"]
    assert await mock_db.graph_rules.find_one({"_id": result.inserted_id}) is None

def test_delete_graph_rule_not_found():
    response = client.delete("/graph_rules/000000000000000000000000")
    assert response.status_code == 404
    assert "Graph rule not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_links(mock_db):
    mock_db = await mock_db
    # Use mock_db directly to ensure a clean state without seeded links
    await seed_data(mock_db) # Seed users and rules, but not links in this test

    # Clear links collection to ensure a clean state for this test
    await mock_db.links.delete_many({})

    # Ensure no links exist initially
    assert await mock_db.links.count_documents({}) == 0

    # Call the generate_links endpoint
    response = client.post("/generate_links/")
    assert response.status_code == 200
    assert "Links generated successfully" in response.json()["message"]

    # Verify links are created in the mock database
    assert await mock_db.links.count_documents({}) > 0

@pytest.mark.asyncio
async def test_analyze_transaction_no_fraudsters(mock_db, setup_and_seed_db):
    mock_db = await mock_db
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

@pytest.mark.asyncio
async def test_analyze_transaction_linked_to_fraudster(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # Ensure there are fraud users
    fraud_users = list(await mock_db.users.find({"is_fraud": True}).to_list(length=None)) # Use to_list for async find
    assert len(fraud_users) > 0
    fraud_user_id = fraud_users[0]['id_user']

    # Get a non-fraudulent user
    normal_user = await mock_db.users.find_one({"is_fraud": False})
    assert normal_user is not None
    user_id = normal_user['id_user']

    # Create a direct link between the normal user and a fraudster
    link_data = {"source": user_id, "target": fraud_user_id, "type": "direct_fraud_link", "weight": 1.0}
    await mock_db.links.insert_one(link_data)
    # The edge is added to the graph by the create_link_service, not directly in the test


    transaction_data = {"id_user": user_id}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 200
    analysis_result = response.json()
    assert analysis_result['user_id'] == user_id
    # Proximity score should be calculated based on shortest path (which is 1)
    assert analysis_result['proximity_score'] == 1.0 / (1 + 1) # 1 / (path_length + 1)
    assert analysis_result['shortest_path_length_to_fraudster'] == 1
    assert analysis_result['closest_fraudster'] == fraud_user_id
    # linked_fraud_count should be at least 1
    assert analysis_result['linked_fraud_count'] >= 1
    assert analysis_result['total_linked_nodes'] >= 1
@pytest.mark.asyncio
async def test_cluster_nodes(mock_db, setup_and_seed_db):
    mock_db = await mock_db
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
    fraud_users_from_db = list(await mock_db.users.find({"is_fraud": True}).to_list(length=None)) # Use to_list for async find

    # Group fraud users by their seeded cluster properties (domain_email, address_zip)
    seeded_fraud_clusters = {}
    for user in fraud_users_from_db:
        cluster_key = (user.get("domain_email"), user.get("address_zip"))
        if cluster_key not in seeded_fraud_clusters:
            seeded_fraud_clusters[cluster_key] = []
        seeded_fraud_clusters[cluster_key].append(user['id_user'])

    # Verify that users from the same seeded fraud cluster are in the same database cluster
    db_clusters = list(await mock_db.clusters.find().to_list(length=None)) # Use to_list for async find
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

@pytest.mark.asyncio
async def test_analyze_transaction_indirectly_linked_to_fraudster(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # Ensure there are fraud users
    fraud_users = list(await mock_db.users.find({"is_fraud": True}).to_list(length=None)) # Use to_list for async find
    assert len(fraud_users) > 0
    fraud_user_id = fraud_users[0]['id_user']

    # Get two non-fraudulent users
    normal_users = list(await setup_and_seed_db.users.find({"is_fraud": False}).limit(2))
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
def test_analyze_transaction_user_not_in_graph():
    transaction_data = {"id_user": "non_existent_user"}
    transaction_data = {"id_user": "non_existent_user"}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 404
    assert "User ID non_existent_user not found in the graph." in response.json()["detail"]

def test_analyze_transaction_missing_user_id():
    transaction_data = {"some_other_field": "value"}
    transaction_data = {"some_other_field": "value"}
    # Change to POST request with json body
    response = client.post("/analyze", json=transaction_data)
    assert response.status_code == 400 # Expect 400 for missing user ID
    # The error detail might change with Pydantic validation on the body,
    # so we'll check for the specific Pydantic error message.
    assert "Field required" in response.json()["detail"][0]["msg"]
    assert "id_user" in response.json()["detail"][0]["loc"]

# New tests for cluster and link retrieval endpoints

@pytest.mark.asyncio
async def test_get_all_clusters(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # First, run clustering to populate the clusters collection
    client.post("/cluster_nodes/")
    
    response = client.get("/clusters/")
    assert response.status_code == 200
    clusters = response.json()
    assert isinstance(clusters, list)
    assert len(clusters) > 0
    # Verify the structure of a cluster object
    if clusters:
        cluster = clusters[0]
        assert "cluster_id" in cluster
        assert "members" in cluster
        assert isinstance(cluster["members"], list)

@pytest.mark.asyncio
async def test_get_cluster_by_id(mock_db, setup_and_seed_db):
    # First, run clustering to populate the clusters collection
    client.post("/cluster_nodes/")

    # Get a cluster ID from the created clusters
    cluster_doc = await mock_db.clusters.find_one() # Await find_one
    assert cluster_doc is not None
    cluster_id = cluster_doc['cluster_id']

    response = client.get(f"/clusters/{cluster_id}")
    assert response.status_code == 200
    cluster = response.json()
    assert cluster["cluster_id"] == cluster_id
    assert isinstance(cluster["members"], list)

@pytest.mark.asyncio
async def test_get_cluster_by_id_not_found(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # Ensure no clusters exist or get a non-existent ID
    await mock_db.clusters.delete_many({}) # Clear clusters
    
    response = client.get("/clusters/non_existent_cluster_id")
    assert response.status_code == 404
    assert "Cluster not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_all_links(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # Links are seeded by setup_and_seed_db fixture
    
    response = client.get("/links/")
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    assert len(links) > 0
    # Verify the structure of a link object, including reasons
    if links:
        link = links[0]
        assert "source" in link
        assert "target" in link
        assert "type" in link
        assert "weight" in link
        assert "reasons" in link # Check for the reasons field
        assert isinstance(link["reasons"], list)
        assert "rule_ids" in link # Check for the rule_ids field
        assert isinstance(link["rule_ids"], list)


@pytest.mark.asyncio
async def test_get_links_by_cluster(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # First, run clustering to populate the clusters collection
    client.post("/cluster_nodes/")
    
    # Get a cluster ID that has members and links
    # Find a cluster with at least two members to ensure potential links exist within it
    cluster_with_links = None
    for cluster_doc in await mock_db.clusters.find().to_list(length=None): # Await find and use to_list
        if len(cluster_doc.get("members", [])) >= 2:
            # Check if there are links between members of this cluster
            members = cluster_doc["members"]
            has_links = False
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    if await mock_db.links.find_one({"source": members[i], "target": members[j]}) or \
                       await mock_db.links.find_one({"source": members[j], "target": members[i]}):
                        has_links = True
                        break
                if has_links:
                    break
            if has_links:
                cluster_with_links = cluster_doc
                break
    
    assert cluster_with_links is not None, "Could not find a cluster with links between its members in the seeded data."
    cluster_id = cluster_with_links['cluster_id']

    response = client.get("/links/", params={"cluster_id": cluster_id})
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    # Assert that the returned links are indeed between members of the specified cluster
    cluster_members = set(cluster_with_links.get("members", []))
    for link in links:
        assert link["source"] in cluster_members and link["target"] in cluster_members
        assert "reasons" in link # Check for the reasons field
        assert isinstance(link["reasons"], list)
        assert "rule_ids" in link # Check for the rule_ids field
        assert isinstance(link["rule_ids"], list)


@pytest.mark.asyncio
async def test_get_links_by_cluster_not_found(mock_db, setup_and_seed_db):
    mock_db = await mock_db
    # Ensure no clusters exist or get a non-existent ID
    await mock_db.clusters.delete_many({}) # Clear clusters
    
    response = client.get("/links/", params={"cluster_id": "non_existent_cluster_id"})
    # The service returns an empty list if the cluster is not found or has no links
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    assert len(links) == 0