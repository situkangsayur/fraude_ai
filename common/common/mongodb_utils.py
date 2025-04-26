import os
from pymongo import MongoClient
import mongomock # Keep mongomock import for type hinting if needed, or remove if not

def get_mongodb_client(mongo_uri, mock_db=None):
    """
    Returns a MongoDB client.
    If mock_db is provided (during testing), returns the client from the mock_db fixture.
    Otherwise, connects to the real MongoDB.
    """
    try:
        if os.environ.get("TESTING") == "True":
            client = mongomock.MongoClient()
            return client
        elif mock_db:
            return mock_db.client if hasattr(mock_db, 'client') else mock_db
        else:
            # Normal operation: connect to the real MongoDB
            client = MongoClient(mongo_uri)
        return client
    except Exception as e:
        print(f"Error getting MongoDB client: {e}")
        return None

def get_mongodb_database(client, db_name):
    """
    Returns a MongoDB database object from a client.
    """
    try:
        db = client[db_name]
        return db
    except Exception as e:
        print(f"Error getting MongoDB database: {e}")
        return None

# Removed unused custom Mock classes (MockMongoClient, MockMongoDatabase, etc.)
# Removed unused get_mock_mongodb_client function