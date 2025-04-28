from fastapi import HTTPException
from typing import Dict, Any
from ..models import UserNode
from bson.objectid import ObjectId
from ..services import db, graph
from .cluster_service import cluster_nodes_service

async def create_user_service(user: UserNode, db) -> Dict[str, Any]:
    """
    Creates a new user node in the graph and MongoDB.
    """
    user_data = user.model_dump(by_alias=True)  # Use by_alias=True to get the dictionary with the alias name
    # Ensure id_user is unique
    if db.users.find_one({"id_user": user_data["id_user"]}):
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    result = db.users.insert_one(user_data)
    # Fetch the inserted document to get the ObjectId
    new_user = db.users.find_one({"_id": result.inserted_id})
    if new_user and '_id' in new_user:
        new_user['_id'] = str(new_user['_id'])

    node_id = new_user['id_user']
    graph.add_node(node_id, **new_user)
    # Trigger clustering after adding a new user
    await cluster_nodes_service()
    # Convert ObjectId to string for response and rename _id to id
    if new_user and '_id' in new_user:
        new_user['id'] = str(new_user.pop('_id'))
    return new_user

async def read_user_service(user_id: str, db) -> Dict[str, Any]:
    """
    Reads a user node by ID from MongoDB.
    """
    user_data = db.users.find_one({"id_user": user_id})
    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Convert ObjectId to string for response
    if user_data and '_id' in user_data:
        user_data['id'] = str(user_data.pop('_id'))
    return user_data

async def update_user_service(user_id: str, user: UserNode, db) -> Dict[str, Any]:
    """
    Updates a user node by ID in MongoDB.
    """
    user_data = user.model_dump(by_alias=True, exclude_unset=True) # Use by_alias=True and exclude_unset=True
    user_data.pop("id", None) # Remove id from user_data to prevent updating _id
    result = db.users.update_one({"id_user": user_id}, {"$set": user_data})
    if result.modified_count == 0:
        # Check if the user exists with the given ID but no changes were made
        user_exists = db.users.find_one({"id_user": user_id})
        if user_exists is None:
            raise HTTPException(status_code=404, detail="User not found")
        # If user exists but no changes, return the existing user
        updated_user = db.users.find_one({"id_user": user_id})
    else:
        updated_user = db.users.find_one({"id_user": user_id}) # Fetch the updated document

    # Update the node in the graph
    if user_id in graph and updated_user:
        # Ensure _id is not added to graph node attributes as ObjectId
        updated_user_for_graph = updated_user.copy()
        if '_id' in updated_user_for_graph:
            del updated_user_for_graph['_id']
        graph.nodes[user_id].update(updated_user_for_graph)

    # Convert ObjectId to string for response and rename _id to id
    if updated_user and '_id' in updated_user:
        updated_user['id'] = str(updated_user.pop('_id'))
    return updated_user

async def delete_user_service(user_id: str, db) -> Dict[str, Any]:
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