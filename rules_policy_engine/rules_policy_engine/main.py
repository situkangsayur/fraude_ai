from fastapi import FastAPI
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from .api import policy_router, rule_router

app = FastAPI()

app.include_router(policy_router)
app.include_router(rule_router)

@app.on_event("startup")
async def startup_event():
    client = get_mongodb_client(MONGODB_URI)
    if not client:
        print("Failed to connect to MongoDB")
        return

    db = get_mongodb_database(client, MONGODB_DB_NAME)
    if not db:
        print("Failed to get MongoDB database")
        return

    print("Connected to MongoDB")