import os

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://root:@localhost:27017/?authSource=admin")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "fraud_detection")

# LLM Configuration
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "google/flan-t5-base")

# Other Configurations
# Add any other configuration settings here