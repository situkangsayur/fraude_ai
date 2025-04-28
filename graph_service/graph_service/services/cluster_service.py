from typing import List, Dict, Any

from ..services import db, graph
from .graph_rule_service import apply_graph_rule

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

    # Save clusters to MongoDB
    final_clusters = []
    for members in clusters.values():
        if len(members) > 1:
            cluster_doc = {
                "members": list(members)
            }
            final_clusters.append(cluster_doc)

    db.clusters.insert_many(final_clusters)

    return {"message": "Nodes clustered successfully"}

async def get_all_clusters_service() -> List[Dict[str, Any]]:
    """
    Retrieve all clusters from MongoDB.
    """
    clusters = list(db.clusters.find())
    for cluster in clusters:
        cluster['_id'] = str(cluster['_id'])  # Convert ObjectId to string
    return clusters

async def get_cluster_by_id_service(cluster_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific cluster by ID from MongoDB.
    """
    cluster = db.clusters.find_one({"_id": cluster_id})
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    cluster['_id'] = str(cluster['_id'])  # Convert ObjectId to string
    return cluster