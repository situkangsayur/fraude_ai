from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any, List, Optional
from .models import UserNode, GraphRule, Link
from .services import (
    initialize_graph_db,
    create_user_service,
    read_user_service,
    update_user_service,
    delete_user_service,
    create_link_service,
    read_link_service,
    delete_link_service,
    generate_links_service,
    create_graph_rule_service,
    read_graph_rule_service,
    update_graph_rule_service,
    delete_graph_rule_service,
    analyze_transaction_service,
    cluster_nodes_service
)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Initializes the graph and database connection on startup.
    """
    await initialize_graph_db()

# CRUD operations for User Nodes
@app.post("/users/", response_model=Dict[str, Any])
async def create_user(user: UserNode):
    """
    Creates a new user node in the graph and MongoDB.
    """
    try:
        return await create_user_service(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=Dict[str, Any])
async def read_user(user_id: str):
    """
    Reads a user node by ID from MongoDB.
    """
    try:
        return await read_user_service(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(user_id: str, user: UserNode):
    """
    Updates a user node by ID in MongoDB.
    """
    try:
        return await update_user_service(user_id, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(user_id: str):
    """
    Deletes a user node by ID from MongoDB and the graph.
    """
    try:
        return await delete_user_service(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CRUD operations for Links
@app.post("/links/", response_model=Dict[str, Any])
async def create_link(link: Link):
    """
    Creates a new link in the graph and MongoDB.
    """
    try:
        return await create_link_service(link)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/links/{source_id}/{target_id}", response_model=Dict[str, Any])
async def read_link(source_id: str, target_id: str):
    """
    Reads a link by source and target ID from MongoDB.
    """
    try:
        return await read_link_service(source_id, target_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/links/{source_id}/{target_id}", response_model=Dict[str, Any])
async def delete_link(source_id: str, target_id: str):
    """
    Deletes a link by source and target ID from MongoDB and the graph.
    """
    try:
        return await delete_link_service(source_id, target_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_links/", response_model=Dict[str, Any])
async def generate_links():
    """
    Generates links between users based on predefined rules and distance metrics.
    """
    try:
        return await generate_links_service()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CRUD operations for Graph Rules
@app.post("/graph_rules/", response_model=Dict[str, Any])
async def create_graph_rule(rule: GraphRule):
    """
    Creates a new graph rule in MongoDB.
    """
    try:
        return await create_graph_rule_service(rule)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def read_graph_rule(rule_id: str):
    """
    Reads a graph rule by ID from MongoDB.
    """
    try:
        return await read_graph_rule_service(rule_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def update_graph_rule(rule_id: str, rule: GraphRule):
    """
    Updates a graph rule by ID in MongoDB.
    """
    try:
        return await update_graph_rule_service(rule_id, rule)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/graph_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_graph_rule(rule_id: str):
    """
    Deletes a graph rule by ID from MongoDB.
    """
    try:
        return await delete_graph_rule_service(rule_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_transaction(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the transaction data using graph theory.
    """
    try:
        return await analyze_transaction_service(transaction_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cluster_nodes/", response_model=Dict[str, Any])
async def cluster_nodes():
    """
    Clusters nodes based on graph rules and distance metrics.
    """
    try:
        return await cluster_nodes_service()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
