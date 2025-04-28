from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from common.models import Transaction, FraudData # Import Transaction and FraudData models
from bson import ObjectId # Import ObjectId for MongoDB
from datetime import datetime
import pickle
import os
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

app = FastAPI()

# Initialize MongoDB client and database
mongo_client = get_mongodb_client(MONGODB_URI)
if not mongo_client:
    raise ConnectionError("Failed to connect to MongoDB")
db = get_mongodb_database(mongo_client, MONGODB_DB_NAME)
if db is None:
    raise ConnectionError(f"Failed to connect to database {MONGODB_DB_NAME}")

# Define collections
transactions_collection = db.transactions
fraud_data_collection = db.fraud_data

class FraudScoreResponse(BaseModel):
    fraud_score: float
    fraud_tag: str # Add fraud tag

class FraudConfirmation(BaseModel):
    confirmed_fraud: str # "fraud" or "normal"
    confirmed_institution: Optional[str] = None

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

# Define the path for the saved model
MODEL_PATH = "neural_net_model.pkl"

# Load the trained model or create a new one
input_size = 2  # Example: amount and number of items (needs to be dynamic based on features)
model = SimpleNN(input_size)

if os.path.exists(MODEL_PATH):
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        print(f"Model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model from {MODEL_PATH}: {e}")
        # If loading fails, a new model instance will be used
else:
    print(f"No model found at {MODEL_PATH}, creating a new model.")

model.eval()  # Set the model to evaluation mode

@app.post("/predict", response_model=FraudScoreResponse) # Renamed endpoint to /predict
async def predict_fraud(transaction: Transaction): # Accept Transaction model
    """
    Predicts fraud score and tag for a transaction using a deep learning model.
    """
    try:
        # Prepare the input data for the model
        # NOTE: Feature engineering from the full Transaction model would be needed here
        amount = transaction.amount
        num_items = len(transaction.list_of_items)
        input_data = torch.tensor([amount, num_items], dtype=torch.float32)

        # Make a prediction using the model
        with torch.no_grad():  # Disable gradient calculation for inference
            fraud_score = model(input_data).item()

        # Determine fraud tag based on a threshold (example threshold)
        fraud_threshold = 0.5
        fraud_tag = "fraud" if fraud_score >= fraud_threshold else "normal"

        return {"fraud_score": fraud_score, "fraud_tag": fraud_tag}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str):
    """
    Retrieves transaction information by ID.
    """
    try:
        # Find the transaction in MongoDB
        # Assuming transaction_id in the database is stored as a string
        transaction_data = transactions_collection.find_one({"id_transaction": transaction_id})

        if transaction_data:
            # Convert MongoDB ObjectId to string and use it as 'id' for Pydantic model
            transaction_data['id'] = str(transaction_data['_id'])
            del transaction_data['_id'] # Remove the original _id field
            return Transaction(**transaction_data)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/transactions/{transaction_id}/confirm_fraud")
async def confirm_fraud_status(transaction_id: str, confirmation: FraudConfirmation):
    """
    Updates the fraud confirmation status for a transaction.
    """
    try:
        # Find the transaction in MongoDB
        transaction_data = transactions_collection.find_one({"id_transaction": transaction_id})

        if not transaction_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        # Update the transaction with confirmation details
        update_result = transactions_collection.update_one(
            {"id_transaction": transaction_id},
            {
                "$set": {
                    "confirmed_fraud": confirmation.confirmed_fraud,
                    "confirmed_date": datetime.now().isoformat(), # Generate confirmed_date here
                    "confirmed_institution": confirmation.confirmed_institution
                }
            }
        )

        if update_result.modified_count == 1:
            return {"message": "Fraud confirmation updated successfully"}
        else:
            # This case might happen if the document was found but no changes were made
            # (e.g., confirmed_fraud was already the same)
            return {"message": "Transaction found, but no changes were made"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Define a simple dataset for training (replace with actual data loading)
class FraudDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Assuming data is a list of tuples/lists: ([features], label)
        features = torch.tensor(self.data[idx][0], dtype=torch.float32)
        label = torch.tensor(self.data[idx][1], dtype=torch.float32).unsqueeze(0) # Ensure label is float and has shape [1]
        return features, label

# Training function
def train_model(model: nn.Module, data: List[Dict[str, Any]], epochs: int = 10, learning_rate: float = 0.001):
    """
    Trains the neural network model.
    """
    # Prepare data for training (This is a simplified example)
    # In a real scenario, you would load and preprocess your actual fraud data
    training_data = []
    for entry in data:
        # Example: using 'amount' and 'num_items' as features, 'confirmed_fraud' as label
        # You would need to adapt this based on your actual data and feature engineering
        features = [entry.get("amount", 0), len(entry.get("list_of_items", []))]
        # Convert 'confirmed_fraud' to a numerical label (e.g., "fraud" -> 1, "normal" -> 0)
        label = 1.0 if entry.get("confirmed_fraud") == "fraud" else 0.0
        training_data.append((features, label))

    if not training_data:
        print("No training data available.")
        return

    dataset = FraudDataset(training_data)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

    criterion = nn.BCELoss() # Binary Cross-Entropy Loss for binary classification
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    model.train() # Set the model to training mode
    for epoch in range(epochs):
        running_loss = 0.0
        for inputs, labels in dataloader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(dataloader)}")

    model.eval() # Set the model back to evaluation mode

    # Save the trained model
    try:
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)
        print(f"Model saved successfully to {MODEL_PATH}")
    except Exception as e:
        print(f"Error saving model to {MODEL_PATH}: {e}")


class TrainingParams(BaseModel):
    epochs: int = 10
    learning_rate: float = 0.001

@app.post("/train")
async def train_neural_network(params: TrainingParams):
    """
    Triggers the training of the neural network model.
    """
    try:
        # Fetch data for training (e.g., confirmed fraud data)
        # In a real application, you would filter and preprocess data appropriately
        training_data_cursor = transactions_collection.find({"confirmed_fraud": {"$exists": True}})
        training_data = list(training_data_cursor)

        if not training_data:
            return {"message": "No confirmed fraud data available for training."}

        # Train the model
        train_model(model, training_data, epochs=params.epochs, learning_rate=params.learning_rate)

        return {"message": "Model training initiated. Check logs for progress."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
