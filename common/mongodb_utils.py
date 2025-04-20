from pymongo import MongoClient

def get_mongodb_client(mongo_uri):
    """
    Returns a MongoDB client.
    """
    try:
        client = MongoClient(mongo_uri)
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_mongodb_database(client, db_name):
    """
    Returns a MongoDB database.
    """
    try:
        db = client[db_name]
        return db
    except Exception as e:
        print(f"Error getting MongoDB database: {e}")
        return None