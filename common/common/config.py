import os

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://root:root@localhost:27017/?authSource=admin")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "fraud_detection")

# LLM Configuration
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "google/flan-t5-base")
RULES_POLICY_ENGINE_URL = os.environ.get("RULES_POLICY_ENGINE_URL", "http://localhost:8000")

# Other Configurations
# Add any other configuration settings here
