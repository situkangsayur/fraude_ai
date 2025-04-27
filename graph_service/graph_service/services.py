from fastapi import HTTPException
from typing import Dict, Any, List, Optional
import networkx as nx
from pymongo import MongoClient
from bson.objectid import ObjectId
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from .models import UserNode, GraphRule, Link # Import models from the same package

# Global graph and database objects
graph = nx.Graph()
db = None

async def initialize_graph_db():
    """
    Initializes the graph and database connection on startup.
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
        graph.add_edge(source, target, weight=weight, type=link_data['type'], reasons=link_data.get('reasons', []), rule_ids=link_data.get('rule_ids', []))

    # Load cluster data from MongoDB
    for cluster_data in db.clusters.find():
        cluster_id = cluster_data['cluster_id']
        members = cluster_data['members']
        # Store cluster information in graph nodes or a separate structure
        for member_id in members:
            if member_id in graph:
                graph.nodes[member_id]['cluster_id'] = cluster_id

def apply_graph_rule(user1, user2, rule):
    """
    Applies a graph rule to two users and returns True if the rule is satisfied, False otherwise.
    """
    field1_value = user1.get(rule['field1'])
    field2_value = user2.get(rule['field2']) if rule.get('field2') else rule.get('value')

    if field1_value is None or field2_value is None:
        return False

    operator = rule['operator']

    if operator == "equal":
        return str(field1_value) == str(field2_value) # Compare as strings for flexibility
    elif operator == "greater_than":
        try:
            return float(field1_value) > float(field2_value)
        except (ValueError, TypeError):
            return False # Cannot compare non-numeric values
    elif operator == "lower_than":
        try:
            return float(field1_value) < float(field2_value)
        except (ValueError, TypeError):
            return False # Cannot compare non-numeric values
    elif operator == "contains":
        return str(field2_value) in str(field1_value) # Check if value is a substring of field1

    return False

def apply_graph_rule_single(data, rule):
    """
    Applies a graph rule to a single data object (user or transaction) and returns True if the rule is satisfied.
    """
    field1_value = data.get(rule['field1'])
    value_to_compare = rule.get('value')

    if field1_value is None or value_to_compare is None:
        return False

    operator = rule['operator']

    if operator == "equal":
        return str(field1_value) == str(value_to_compare)
    elif operator == "greater_than":
        try:
            return float(field1_value) > float(value_to_compare)
        except (ValueError, TypeError):
            return False
    elif operator == "lower_than":
        try:
            return float(field1_value) < float(value_to_compare)
        except (ValueError, TypeError):
            return False
    elif operator == "contains":
        return str(value_to_compare) in str(field1_value)

    return False

async def create_user_service(user: UserNode) -> Dict[str, Any]:
    """
    Creates a new user node in the graph and MongoDB.
    """
    user_data = user.model_dump()
    # Ensure id_user is unique
    if db.users.find_one({"id_user": user_data["id_user"]}):
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    db.users.insert_one(user_data)
    node_id = user_data['id_user']
    graph.add_node(node_id, **user_data)
    # Trigger clustering after adding a new user
    await cluster_nodes_service()
    # Convert ObjectId to string for response
    user_data['_id'] = str(user_data['_id'])
    return user_data

async def read_user_service(user_id: str) -> Dict[str, Any]:
    """
    Reads a user node by ID from MongoDB.
    """
    user_data = db.users.find_one({"id_user": user_id})
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Convert ObjectId to string for response
    user_data['_id'] = str(user_data['_id'])
    return user_data

async def update_user_service(user_id: str, user: UserNode) -> Dict[str, Any]:
    """
    Updates a user node by ID in MongoDB.
    """
    user_data = user.model_dump()
    result = db.users.update_one({"id_user": user_id}, {"$set": user_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = db.users.find_one({"id_user": user_id})
    # Update the node in the graph
    if user_id in graph:
        # Ensure _id is not added to graph node attributes as ObjectId
        updated_user_for_graph = updated_user.copy()
        if '_id' in updated_user_for_graph:
            del updated_user_for_graph['_id']
        graph.nodes[user_id].update(updated_user_for_graph)

    # Convert ObjectId to string for response
    if updated_user:
        updated_user['_id'] = str(updated_user['_id'])
    return updated_user

async def delete_user_service(user_id: str) -> Dict[str, Any]:
    """
    Deletes a user node by ID from MongoDB and the graph.
    """
    result = db.users.delete_one({"id_user": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    # Remove the node from the graph
    if user_id in graph:
        graph.remove_node(user_id)
    # Also remove any links associated with this user
    db.links.delete_many({"$or": [{"source": user_id}, {"target": user_id}]})
    # Remove edges from the graph
    edges_to_remove = list(graph.edges(user_id))
    graph.remove_edges_from(edges_to_remove)

    return {"message": "User deleted successfully"}

async def create_link_service(link: Link) -> Dict[str, Any]:
    """
    Creates a new link in the graph and MongoDB.
    """
    link_data = link.model_dump()
    # Ensure link doesn't already exist (simple check based on source and target)
    if db.links.find_one({"source": link_data["source"], "target": link_data["target"]}) or db.links.find_one({"source": link_data["target"], "target": link_data["source"]}):
         raise HTTPException(status_code=400, detail="Link between these users already exists")

    result = db.links.insert_one(link_data)
    # Fetch the inserted document to get the ObjectId
    new_link = db.links.find_one({"_id": result.inserted_id})

    graph.add_edge(new_link['source'], new_link['target'], weight=new_link['weight'], type=new_link['type'], reasons=new_link.get('reasons', []), rule_ids=new_link.get('rule_ids', []))
    # Convert ObjectId to string for response
    if new_link:
        new_link['_id'] = str(new_link['_id'])
    return new_link

async def read_link_service(source_id: str, target_id: str) -> Dict[str, Any]:
    """
    Reads a link by source and target ID from MongoDB.
    """
    link_data = db.links.find_one({"source": source_id, "target": target_id})
    if link_data is None:
        raise HTTPException(status_code=404, detail="Link not found")
    # Convert ObjectId to string for response
    link_data['_id'] = str(link_data['_id'])
    return link_data

async def delete_link_service(source_id: str, target_id: str) -> Dict[str, Any]:
    """
    Deletes a link by source and target ID from MongoDB and the graph.
    """
    result = db.links.delete_one({"source": source_id, "target": target_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    # Remove the edge from the graph
    if graph.has_edge(source_id, target_id):
        graph.remove_edge(source_id, target_id)
    return {"message": "Link deleted successfully"}

async def generate_links_service() -> Dict[str, Any]:
    """
    Generates links between users based on predefined rules and distance metrics.
    """
    # Load graph rules from MongoDB
    graph_rules = list(db.graph_rules.find()) # Convert cursor to list

    users = list(db.users.find()) # Convert cursor to list

    # Iterate through all users and apply graph rules and distance metrics
    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            user1 = users[i]
            user2 = users[j]

            user1_id = user1['id_user']
            user2_id = user2['id_user']

            # Check for existing link to avoid duplicates
            if db.links.find_one({"source": user1_id, "target": user2_id}) or db.links.find_one({"source": user2_id, "target": user1_id}):
                continue

            triggered_rules_details = []
            # Apply rules
            for rule in graph_rules:
                if apply_graph_rule(user1, user2, rule):
                    triggered_rules_details.append({
                        "name": rule['name'],
                        "description": rule['description'],
                        "rule_id": str(rule['_id'])
                    })

            # Apply distance metrics (example using address_zip)
            # Distance metrics can also be considered as rules or contribute to link strength/reason
            if user1.get('address_zip') and user2.get('address_zip') and user1['address_zip'] == user2['address_zip']:
                triggered_rules_details.append({
                    "name": "zip_code_match",
                    "description": "Matching address zip codes",
                    "rule_id": "zip_code_match" # Using a placeholder ID for distance metric
                })

            # Add more distance metrics here (e.g., Euclidean/Manhattan on numerical features)
            # This would require identifying numerical features and potentially normalizing them.
            # For simplicity, this example only includes zip code matching.

            if triggered_rules_details:
                # Create a single link with all triggered rule details
                link_data = {
                    "source": user1_id,
                    "target": user2_id,
                    "type": "multiple_rules", # Or a more specific type if needed
                    "weight": 0.5,  # Consider adjusting weight based on number/type of rules
                    "reasons": [detail['description'] for detail in triggered_rules_details],
                    "rule_ids": [detail['rule_id'] for detail in triggered_rules_details]
                }
                db.links.insert_one(link_data)
                graph.add_edge(user1_id, user2_id, weight=0.5, type="multiple_rules", reasons=link_data['reasons'], rule_ids=link_data['rule_ids'])

    return {"message": "Links generated successfully"}

async def create_graph_rule_service(rule: GraphRule) -> Dict[str, Any]:
    """
    Creates a new graph rule in MongoDB.
    """
    rule_data = rule.model_dump()
    result = db.graph_rules.insert_one(rule_data)
    new_rule = db.graph_rules.find_one({"_id": result.inserted_id})
    # Convert ObjectId to string for response
    if new_rule:
        new_rule['_id'] = str(new_rule['_id'])
    return new_rule

async def read_graph_rule_service(rule_id: str) -> Dict[str, Any]:
    """
    Reads a graph rule by ID from MongoDB.
    """
    try:
        # Convert rule_id string to ObjectId
        rule_object_id = ObjectId(rule_id)
        rule = db.graph_rules.find_one({"_id": rule_object_id})
        if rule is None:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        # Convert ObjectId to string for response
        rule['_id'] = str(rule['_id'])
        return rule
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")


async def update_graph_rule_service(rule_id: str, rule: GraphRule) -> Dict[str, Any]:
    """
    Updates a graph rule by ID in MongoDB.
    """
    try:
        # Convert rule_id string to ObjectId
        rule_object_id = ObjectId(rule_id)
        rule_data = rule.model_dump()
        result = db.graph_rules.update_one({"_id": rule_object_id}, {"$set": rule_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        updated_rule = db.graph_rules.find_one({"_id": rule_object_id})
         # Convert ObjectId to string for response
        if updated_rule:
            updated_rule['_id'] = str(updated_rule['_id'])
        return updated_rule
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")

async def delete_graph_rule_service(rule_id: str) -> Dict[str, Any]:
    """
    Deletes a graph rule by ID from MongoDB.
    """
    try:
        # Convert rule_id string to ObjectId
        rule_object_id = ObjectId(rule_id)
        result = db.graph_rules.delete_one({"_id": rule_object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        # Also remove any links created by this rule
        db.links.delete_many({"rule_ids": rule_id}) # Assuming rule_ids is a list
        # Need to rebuild the graph or remove edges from the graph based on the deleted rule
        # For simplicity, we'll just return success here. Rebuilding the graph on rule deletion might be complex.
        return {"message": "Graph rule deleted successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")

async def analyze_transaction_service(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the transaction data using graph theory.
    """
    user_id = transaction_data.get('id_user')

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing 'id_user' in transaction data")

    # Get the list of fraudulent user IDs from the database
    fraud_users = list(db.users.find({"is_fraud": True}))
    fraud_user_ids = [user['id_user'] for user in fraud_users]

    if user_id not in graph:
         raise HTTPException(status_code=404, detail=f"User ID {user_id} not found in the graph.")

    # Calculate the shortest path to any fraudster
    shortest_path_length = float('inf')
    closest_fraudster = None

    for fraud_user_id in fraud_user_ids:
        if fraud_user_id in graph:
            try:
                path_length = nx.shortest_path_length(graph, source=user_id, target=fraud_user_id)
                if path_length < shortest_path_length:
                    shortest_path_length = path_length
                    closest_fraudster = fraud_user_id
            except nx.NetworkXNoPath:
                # No path to this fraudulent user
                pass

    # Calculate a proximity score based on the shortest path length
    # A smaller path length means higher risk/proximity
    proximity_score = 1.0 / (shortest_path_length + 1) if shortest_path_length != float('inf') else 0.0 # Add 1 to avoid division by zero

    # You could also consider the number of linked nodes and their fraud status
    linked_nodes = list(graph.neighbors(user_id))
    linked_fraud_count = sum(1 for node_id in linked_nodes if node_id in fraud_user_ids)

    # Apply graph rules to the transaction and user
    triggered_rules = []
    graph_rules = list(db.graph_rules.find())
    user_data = db.users.find_one({"id_user": user_id}) # Fetch user data for rule application

    if user_data:
        # Apply rules that check transaction data or user data
        for rule in graph_rules:
            # Simple rule application logic - needs refinement based on actual rule structure
            # Assuming rules can check fields in transaction_data or user_data
            rule_satisfied = False
            if rule.get('field1') in transaction_data and rule.get('value') is not None:
                 if apply_graph_rule_single(transaction_data, rule):
                     rule_satisfied = True
            elif rule.get('field1') in user_data and rule.get('value') is not None:
                 if apply_graph_rule_single(user_data, rule):
                     rule_satisfied = True
            # Add logic for rules comparing two fields within transaction_data or user_data, or between them

            if rule_satisfied:
                triggered_rules.append(rule['name'])


    return {
        "user_id": user_id,
        "proximity_score": proximity_score,
        "shortest_path_length_to_fraudster": shortest_path_length if shortest_path_length != float('inf') else "No path",
        "closest_fraudster": closest_fraudster,
        "linked_fraud_count": linked_fraud_count,
        "total_linked_nodes": len(linked_nodes),
        "triggered_rules": triggered_rules # Add triggered rules to the response
    }

async def cluster_nodes_service() -> Dict[str, Any]:
    """
    Clusters nodes based on graph rules and distance metrics.
    """
    # Clear existing clusters
    db.clusters.delete_many({})

    # Load graph rules from MongoDB
    graph_rules = list(db.graph_rules.find())

    users = list(db.users.find())
    user_ids = [user['id_user'] for user in users]

    # Initialize clusters - each user is initially in their own cluster
    clusters = {user_id: {user_id} for user_id in user_ids}
    cluster_id_counter = len(user_ids)

    # Apply rules to group users
    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            user1 = users[i]
            user2 = users[j]

            user1_id = user1['id_user']
            user2_id = user2['id_user']

            # Check if they are already in the same cluster
            if any(user1_id in cluster and user2_id in cluster for cluster in clusters.values()):
                continue

            rule_triggered = False
            for rule in graph_rules:
                if apply_graph_rule(user1, user2, rule):
                    # Merge clusters
                    cluster1_id = None
                    cluster2_id = None
                    for c_id, members in clusters.items():
                        if user1_id in members:
                            cluster1_id = c_id
                        if user2_id in members:
                            cluster2_id = c_id
                        if cluster1_id and cluster2_id:
                            break

                    if cluster1_id and cluster2_id and cluster1_id != cluster2_id:
                        clusters[cluster1_id].update(clusters[cluster2_id])
                        del clusters[cluster2_id]
                    elif cluster1_id and not cluster2_id:
                         clusters[cluster1_id].add(user2_id)
                    elif cluster2_id and not cluster1_id:
                         clusters[cluster2_id].add(user1_id)
                    elif not cluster1_id and not cluster2_id:
                        # Should not happen if all users are initially in clusters
                        pass

                    rule_triggered = True
                    break # Move to the next pair if a rule is triggered

            # Apply distance metrics for clustering if no rule was triggered
            if not rule_triggered:
                # Example: Cluster users with the same address_zip
                if user1.get('address_zip') and user2.get('address_zip') and user1['address_zip'] == user2['address_zip']:
                     cluster1_id = None
                     cluster2_id = None
                     for c_id, members in clusters.items():
                         if user1_id in members:
                             cluster1_id = c_id
                         if user2_id in members:
                             cluster2_id = c_id
                         if cluster1_id and cluster2_id:
                             break

                     if cluster1_id and cluster2_id and cluster1_id != cluster2_id:
                         clusters[cluster1_id].update(clusters[cluster2_id])
                         del clusters[cluster2_id]
                     elif cluster1_id and not cluster2_id:
                          clusters[cluster1_id].add(user2_id)
                     elif cluster2_id and not cluster1_id:
                          clusters[cluster2_id].add(user1_id)
                     elif not cluster1_id and not cluster2_id:
                         # Should not happen if all users are initially in clusters
                         pass


    # Save clusters to MongoDB
    for cluster_id, members in clusters.items():
        # Use a more stable cluster ID, e.g., based on a hash of sorted members or the first member's ID
        # For simplicity, let's use the first member's ID if available, otherwise generate one
        stable_cluster_id = list(members)[0] if members else f"cluster_{cluster_id_counter}"
        cluster_doc = {
            "cluster_id": stable_cluster_id,
            "members": list(members)
        }
        db.clusters.insert_one(cluster_doc)
        cluster_id_counter += 1 # Still increment for unique fallback IDs if needed

    return {"message": "Nodes clustered successfully"}

async def get_all_clusters_service() -> List[Dict[str, Any]]:
    """
    Retrieves all clusters with their members from MongoDB.
    """
    clusters = list(db.clusters.find())
    # Convert ObjectId to string for response
    for cluster in clusters:
        cluster['_id'] = str(cluster['_id'])
    return clusters

async def get_cluster_by_id_service(cluster_id: str) -> Dict[str, Any]:
    """
    Retrieves a specific cluster by ID with its members from MongoDB.
    """
    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    # Convert ObjectId to string for response
    cluster['_id'] = str(cluster['_id'])
    return cluster

async def get_all_links_service() -> List[Dict[str, Any]]:
    """
    Retrieves all links from MongoDB, including reasons.
    """
    links = list(db.links.find())
    # Convert ObjectId to string for response
    for link in links:
        link['_id'] = str(link['_id'])
    return links

async def get_links_by_cluster_service(cluster_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves links within a specific cluster from MongoDB, including reasons.
    """
    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    member_ids = cluster.get('members', [])

    # Find links where both source and target are members of the cluster
    links = list(db.links.find({
        "$and": [
            {"source": {"$in": member_ids}},
            {"target": {"$in": member_ids}}
        ]
    }))

    # Convert ObjectId to string for response
    for link in links:
        link['_id'] = str(link['_id'])
    return links