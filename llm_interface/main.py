from fastapi import FastAPI
from llm_interface import api

app = FastAPI()

app.include_router(api.app, prefix="/api")