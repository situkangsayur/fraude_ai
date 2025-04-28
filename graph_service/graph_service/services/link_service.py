from fastapi import HTTPException
from typing import Dict, Any

from ..models import Link
from ..services import db, graph

async def create_link_service(link: Link, db) -> Dict[str, Any]:
    """
    Creates a new link in the graph and MongoDB.
    """
    link_data = link.model_dump(by_alias=True) # Use by_alias=True
    # Ensure link doesn't already exist (simple check based on source and target)
    if db.links.find_one({"source": link_data["source"], "target": link_data["target"]}) or db.links.find_one({"source": link_data["target"], "target": link_data["source"]}):
         raise HTTPException(status_code=400, detail="Link between these users already exists")

    result = db.links.insert_one(link_data)
    # Fetch the inserted document to get the ObjectId
    new_link = db.links.find_one({"_id": result.inserted_id})

    graph.add_edge(new_link['source'], new_link['target'], weight=new_link['weight'], type=new_link['type'], reasons=new_link.get('reasons', []), rule_ids=new_link.get('rule_ids', []))
    # Convert ObjectId to string for response and rename _id to id
    if new_link and '_id' in new_link:
        new_link['id'] = str(new_link.pop('_id'))
    return new_link

async def read_link_service(source_id: str, target_id: str, db) -> Dict[str, Any]:
    """
    Reads a link by source and target ID from MongoDB.
    """
    link_data = db.links.find_one({"source": source_id, "target": target_id})
    if link_data is None:
        raise HTTPException(status_code=404, detail="Link not found")
    # Convert ObjectId to string for response and rename _id to id
    if link_data and '_id' in link_data:
        link_data['id'] = str(link_data.pop('_id'))
    return link_data

async def delete_link_service(source_id: str, target_id: str, db) -> Dict[str, Any]:
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