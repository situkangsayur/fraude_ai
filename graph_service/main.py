from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any, List, Optional
import networkx as nx
from pymongo import MongoClient
from pydantic import BaseModel
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database

app = FastAPI()

class UserNode(BaseModel):
    id_user: str
    nama_lengkap: str
    email: str
    domain_email: str
    address: str
    address_zip: str
    address_city: str
    address_province: str
    address_kecamatan: str
    phone_number: str
    is_fraud: bool = False

class GraphRule(BaseModel):
    name: str
    description: str
    field1: str
    operator: str  # e.g., "equal", "greater_than", "contains"
    field2: Optional[str] = None  # Optional, for comparing two fields
    value: Optional[str] = None  # Optional, for comparing with a fixed value

@app.on_event("startup")
async def startup_event():
    """
    Loads the graph from MongoDB on startup.
    """
    global graph, db
    client = get_mongodb_client(MONGODB_URI)
    if client is None:
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
    db = get_mongodb_database(client, MONGODB_DB_NAME)
    if db is None:
        raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

    graph = nx.Graph()

    # Load nodes from MongoDB
    for node_data in db.users.find():
        node_id = node_data['id_user']
        graph.add_node(node_id, **node_data)

    # Load edges from MongoDB
    for link_data in db.links.find():
        source = link_data['source']
        target = link_data['target']
        weight = link_data['weight']
        graph.add_edge(source, target, weight=weight, type=link_data['type'], reason=link_data['reason'])

@app.post("/nodes/", response_model=Dict[str, Any])
async def create_node(user: UserNode):
    """
    Creates a new user node in the graph and MongoDB.
    """
    try:
        user_data = user.dict()
        db.users.insert_one(user_data)
        node_id = user_data['id_user']
        graph.add_node(node_id, **user_data)
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/links/", response_model=Dict[str, Any])
async def create_links():
    """
    Creates links between users based on predefined rules.
    """
    try:
        # Load graph rules from MongoDB
        graph_rules = await db.graph_rules.find().to_list(length=None)

        # Iterate through all users and apply graph rules
        for user1 in db.users.find():
            for user2 in db.users.find():
                if user1['id_user'] == user2['id_user']:
                    continue

                for rule in graph_rules:
                    if apply_graph_rule(user1, user2, rule):
                        # Create a link between the users
                        link_data = {
                            "source": user1['id_user'],
                            "target": user2['id_user'],
                            "type": rule['name'],
                            "weight": 0.5,  # Adjust weight as needed
                            "reason": rule['description'],
                            "rule_id": rule['_id']
                        }
                        db.links.insert_one(link_data)
                        graph.add_edge(user1['id_user'], user2['id_user'], weight=0.5, type=rule['name'], reason=rule['description'])
                        break  # Only create one link per pair of users
        return {"message": "Links created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def apply_graph_rule(user1, user2, rule):
    """
    Applies a graph rule to two users and returns True if the rule is satisfied, False otherwise.
    """
    field1 = user1.get(rule['field1'])
    field2 = user2.get(rule['field2']) if rule.get('field2') else rule.get('value')

    if field1 is None or field2 is None:
        return False

    operator = rule['operator']

    if operator == "equal":
        return field1 == field2
    elif operator == "greater_than":
        return field1 > field2
    elif operator == "lower_than":
        return field1 < field2
    # Add more operators as needed

    return False

@app.post("/graph_rules/", response_model=Dict[str, Any])
async def create_graph_rule(rule: GraphRule):
    """
    Creates a new graph rule in MongoDB.
    """
    try:
        rule_data = rule.dict()
        result = await db.graph_rules.insert_one(rule_data)
        new_rule = await db.graph_rules.find_one({"_id": result.inserted_id})
        return new_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def read_graph_rule(rule_id: str):
    """
    Reads a graph rule by ID from MongoDB.
    """
    try:
        rule = await db.graph_rules.find_one({"_id": rule_id})
        if rule is None:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        return rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def update_graph_rule(rule_id: str, rule: GraphRule):
    """
    Updates a graph rule by ID in MongoDB.
    """
    try:
        rule_data = rule.dict()
        result = await db.graph_rules.update_one({"_id": rule_id}, {"$set": rule_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        updated_rule = await db.graph_rules.find_one({"_id": rule_id})
        return updated_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_graph_rule(rule_id: str):
    """
    Deletes a graph rule by ID from MongoDB.
    """
    try:
        result = await db.graph_rules.delete_one({"_id": rule_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        return {"message": "Graph rule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_transaction(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the transaction data using graph theory.
    """
    user_id = transaction_data['id_user']

    # Get the list of fraudulent user IDs (replace with actual data retrieval logic)
    fraud_user_ids = ["user123", "user456"]

    try:
        # Calculate the shortest path to a fraudster
        shortest_path_length = float('inf')
        for fraud_user in fraud_user_ids:
            try:
                path_length = nx.shortest_path_length(graph, source=user_id, target=fraud_user)
                proximity = 1.0 / path_length  # Closer is higher proximity
            except nx.NetworkXNoPath:
                # No path to fraudulent user
                pass

        # Calculate a proximity score based on the shortest path length
        proximity_score = 1.0 / shortest_path_length if shortest_path_length != float('inf') else 0.0

        return {
            "proximity_score": proximity_score,
            "shortest_path_length": shortest_path_length,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))