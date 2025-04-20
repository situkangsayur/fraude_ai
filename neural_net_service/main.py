from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import torch
import torch.nn as nn
import torch.nn.functional as F
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database

app = FastAPI()

class TransactionData(BaseModel):
    amount: float
    list_of_items: list

class FraudScoreResponse(BaseModel):
    fraud_score: float

class SimpleNN(nn.Module):
    def __init__(self, input_size):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)  # Output a single fraud score

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))  # Use sigmoid to get a score between 0 and 1
        return x

# Load the trained model (replace with your actual model loading logic)
# For simplicity, I'm creating a dummy model here
input_size = 2  # Example: amount and number of items
model = SimpleNN(input_size)
model.eval()  # Set the model to evaluation mode

@app.post("/score", response_model=FraudScoreResponse)
async def score_transaction(transaction_data: TransactionData):
    """
    Scores a transaction using a deep learning model.
    """
    try:
        # Prepare the input data for the model
        amount = transaction_data.amount
        num_items = len(transaction_data.list_of_items)
        input_data = torch.tensor([amount, num_items], dtype=torch.float32)

        # Make a prediction using the model
        with torch.no_grad():  # Disable gradient calculation for inference
            fraud_score = model(input_data).item()

        return {"fraud_score": fraud_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))