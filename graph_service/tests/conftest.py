import pytest
import mongomock
from graph_service.models import UserNode, GraphRule, Link, Cluster
from unittest.mock import patch
import asyncio
from graph_service.services import initialize_graph_db

import os

client = mongomock.MongoClient()
db = client['fraud_detection']

@pytest.fixture
async def mock_db():
    # Create collections
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    if 'links' not in db.list_collection_names():
        db.create_collection('links')
    if 'clusters' not in db.list_collection_names():
        db.create_collection('clusters')
    # Seed the database with a fraud user
    if db.users.count_documents({"id_user": "fraud_user"}) == 0:
        db.users.insert_one({
            "id_user": "fraud_user",
            "nama_lengkap": "Fraud User",
            "email": "fraud@example.com",
            "domain_email": "example.com",
            "address": "Fraud Address",
            "address_zip": "12345",
            "address_city": "Fraud City",
            "address_province": "Fraud Province",
            "address_kecamatan": "Fraud Kecamatan",
            "phone_number": "081234567890",
            "is_fraud": True
        })
    if os.environ.get("TESTING") != "True":
        await initialize_graph_db(db)
    os.environ["TESTING"] = "True"
    return db