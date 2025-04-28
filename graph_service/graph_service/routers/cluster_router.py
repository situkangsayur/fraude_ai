from fastapi import APIRouter, HTTPException
from typing import List
from ..services.cluster_service import get_all_clusters_service, get_cluster_by_id_service
from ..models import Cluster

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