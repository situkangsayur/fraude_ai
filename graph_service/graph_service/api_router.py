from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from . import services
from .models import Cluster, Link # Assuming Cluster model exists or needs to be created

router = APIRouter()

@router.get("/clusters", response_model=List[Cluster])
async def get_all_clusters():
    """
    Retrieve all clusters.
    """
    return await services.get_all_clusters_service()

@router.get("/clusters/{cluster_id}", response_model=Cluster)
async def get_cluster_by_id(cluster_id: str):
    """
    Retrieve a specific cluster by ID.
    """
    cluster = await services.get_cluster_by_id_service(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.get("/links", response_model=List[Link])
async def get_all_links():
    """
    Retrieve all links.
    """
    return await services.get_all_links_service()

@router.get("/clusters/{cluster_id}/links", response_model=List[Link])
async def get_links_by_cluster(cluster_id: str):
    """
    Retrieve all links within a specific cluster.
    """
    return await services.get_links_by_cluster_service(cluster_id)