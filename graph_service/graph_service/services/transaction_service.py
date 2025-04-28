from fastapi import HTTPException
from typing import Dict, Any

from ..services import db, graph
from .graph_rule_service import apply_graph_rule_single
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