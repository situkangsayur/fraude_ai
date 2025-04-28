from fastapi import HTTPException
from typing import Dict, Any, List, Optional
import networkx as nx
from pymongo import MongoClient
from bson.objectid import ObjectId
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from ..models import UserNode, GraphRule, Link # Import models from the same package

# Global graph and database objects
graph = nx.Graph()
db = None

import sys

async def initialize_graph_db(db_instance=None):
    """
    Initializes the graph and database connection on startup.
    Accepts an optional db_instance for testing.
    """
    global graph, db
    if db_instance:
        db = db_instance
    elif os.environ.get("TESTING") == "True":
        # Use mongomock for testing if no db_instance is provided
        from mongomock import MongoClient
        client = MongoClient()
        db = client['fraud_detection']
    else:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

    graph = nx.Graph()

    # Load nodes from MongoDB
    if db and 'users' in db.list_collection_names():
        for node_data in db.users.find():
            node_id = node_data['id_user']
            graph.add_node(node_id, **node_data)

    # Load edges from MongoDB
    if db and 'links' in db.list_collection_names():
        for link_data in db.links.find():
            source = link_data['source']
            target = link_data['target']
            weight = link_data['weight']
            graph.add_edge(source, target, weight=weight, type=link_data['type'], reasons=link_data.get('reasons', []), rule_ids=link_data.get('rule_ids', []))

    # Load cluster data from MongoDB
    if db and 'clusters' in db.list_collection_names():
        for cluster_data in db.clusters.find():
            cluster_id = str(cluster_data['_id'])
            members = cluster_data['members']
            # Store cluster information in graph nodes or a separate structure
            for member_id in members:
                if member_id in graph:
                    graph.nodes[member_id]['cluster_id'] = cluster_id