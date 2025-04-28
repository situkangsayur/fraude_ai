from fastapi import APIRouter
from typing import List
from ..services.link_service import get_all_links_service, get_links_by_cluster_service
from ..models import Link

router = APIRouter()

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