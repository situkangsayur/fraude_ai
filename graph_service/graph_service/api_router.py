from fastapi import APIRouter
from .routers import cluster_router, link_router

router = APIRouter()

router.include_router(cluster_router.router)
router.include_router(link_router.router)