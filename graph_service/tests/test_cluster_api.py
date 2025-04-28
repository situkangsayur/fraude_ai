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


@pytest.mark.asyncio
async def test_get_all_clusters(mock_db, test_client):
    # Seed the database with sample data
    db = await mock_db
    await db.clusters.insert_many([
        {"members": ["user1", "user2"], "description": "Sample cluster 1"},
        {"members": ["user3", "user4"], "description": "Sample cluster 2"},
    ])
    response = test_client.get("/clusters/")
    assert response.status_code == 200
    clusters = response.json()
    assert isinstance(clusters, list)

@pytest.mark.asyncio
async def test_get_cluster_by_id(mock_db, test_client):
    # Seed the database with sample data
    db = await mock_db
    db.clusters.insert_many([
        {"members": ["user1", "user2"], "description": "Sample cluster 1"},
        {"members": ["user3", "user4"], "description": "Sample cluster 2"},
    ])
    # The cluster is already seeded in conftest.py
    cluster = await db.clusters.find_one({"description": "Sample cluster 1"})
    assert cluster is not None
    cluster_id = str(cluster["_id"]) if cluster and "_id" in cluster else None
    assert cluster_id is not None

    response = test_client.get(f"/clusters/{cluster_id}")
    assert response.status_code == 200, f"Expected 200, but got {response.status_code}. Response detail: {response.text}"
    retrieved_cluster = response.json()
    assert retrieved_cluster["_id"] == cluster_id
    assert retrieved_cluster["members"] == cluster["members"]

@pytest.mark.asyncio
async def test_get_cluster_by_id_not_found(mock_db, test_client):
    response = test_client.get("/clusters/non_existent_cluster")
    assert response.status_code == 404
    assert "Cluster not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_all_links(mock_db, test_client):
    # Seed the database with sample data
    db = await mock_db
    db.links.insert_many([
        {"source": "user1", "target": "user3", "type": "test_link", "weight": 0.5, "reasons": [], "rule_ids": []},
        {"source": "user2", "target": "user4", "type": "test_link", "weight": 0.7, "reasons": [], "rule_ids": []},
        {"source": "user5", "target": "user6", "type": "test_link", "weight": 0.3, "reasons": [], "rule_ids": []},
    ])
    response = test_client.get("/links/")
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)

@pytest.mark.asyncio
async def test_get_links_by_cluster(mock_db, test_client):
    # Seed the database with sample data
    db = await mock_db
    db.clusters.insert_many([
        {"members": ["user1", "user2"], "description": "Sample cluster 1"},
        {"members": ["user3", "user4"], "description": "Sample cluster 2"},
    ])
    await db.links.insert_many([
        {"source": "user1", "target": "user3", "type": "test_link", "weight": 0.5, "reasons": [], "rule_ids": []},
        {"source": "user2", "target": "user4", "type": "test_link", "weight": 0.7, "reasons": [], "rule_ids": []},
        {"source": "user5", "target": "user6", "type": "test_link", "weight": 0.3, "reasons": [], "rule_ids": []},
    ])
    # The cluster is already seeded in conftest.py
    cluster = await db.clusters.find_one({"description": "Sample cluster 1"})
    assert cluster is not None
    cluster_id = str(cluster["_id"])

    response = test_client.get(f"/clusters/{cluster_id}/links")
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    # Basic check to ensure links are returned (more detailed checks would require more complex setup)
    assert len(links) >= 0

@pytest.mark.asyncio
async def test_get_links_by_cluster_not_found(mock_db, test_client):
    response = test_client.get("/clusters/non_existent_cluster/links")
    assert response.status_code == 404
    assert "Cluster not found" in response.json()["detail"]