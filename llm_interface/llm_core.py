from langchain.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from common.config import LLM_MODEL_NAME, RULES_POLICY_ENGINE_URL
from common.mongodb_utils import get_mongodb_client, get_documents
import requests

def load_llm():
    """
    Loads the LLM model.
    """
    try:
        model_name = LLM_MODEL_NAME
    except Exception as e:
        print(f"Error loading LLM model name from config: {e}")
        raise
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
    llm = HuggingFacePipeline(pipeline=pipe)
    return llm

def analyze_transaction_data(transaction_data: Dict[str, Any], llm) -> str:
    """
    Analyzes the transaction data using an LLM and RAG.
    """
    try:
        # 1. Retrieve relevant compliance documents using RAG
        compliance_docs = get_relevant_compliance_documents(transaction_data)

        # 2. Get policy rules from rules_policy_engine
        policy_rules = get_policy_rules(transaction_data)

        # 3. Prepare the prompt for the LLM
        prompt = f"Analyze the following transaction data for fraud:\n{transaction_data}\n\nConsider the following compliance documents:\n{compliance_docs}\n\nConsider the following policy rules:\n{policy_rules}\n\nProvide a fraud score and a justification."

        # 4. Run the LLM and get the response
        llm_response = llm(prompt)
        return llm_response
    except Exception as e:
        print(f"Error analyzing transaction data: {e}")
        raise

def get_relevant_compliance_documents(transaction_data: Dict[str, Any]) -> str:
    """
    Retrieves relevant compliance documents from MongoDB using RAG.
    """
    try:
        client = get_mongodb_client()
        db = client["fraud_db"]  # Replace with your actual database name
        compliance_docs = get_documents(db, "compliance_docs", {})  # Replace with your actual collection name and query

        # Basic concatenation for now, replace with actual RAG logic
        return "\n".join([doc["content"] for doc in compliance_docs])
    except Exception as e:
        print(f"Error retrieving compliance documents: {e}")
        return "No compliance documents found."

def get_policy_rules(transaction_data: Dict[str, Any]) -> str:
    """
    Retrieves relevant policy rules from the rules_policy_engine.
    """
    try:
        response = requests.post(f"{RULES_POLICY_ENGINE_URL}/get_rules", json=transaction_data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text  # Assuming the response is a string representation of the rules
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving policy rules: {e}")
        return "No policy rules found."