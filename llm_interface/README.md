# LLM Interface

## Fraud Analysis & Recommendation Engine (FARE)

---

## 📌 Project Description
**FARE** is a **Python**, **LLM (LangGraph)**, and **MongoDB** based application for:
- Analyzing **fraudulent** and **non-fraudulent** transaction data.
- Integrating **compliance documents** (PDF) via RAG (Retrieval Augmented Generation).
- Providing **recommendations** for new rules, graph detection methods, and distance metrics.
- Generating **reports** on fraud detection performance statistics.

The application combines approaches:
- **Rule-based Policy Engine**
- **Graph Network Service**
- **Neural Network Machine Learning**
  
All recommendations must align with active compliance policies.

---

## ✨ Main Features
- **Upload Compliance PDF**: Extract and store compliance documents for RAG reference.
- **Data Management API**: REST API for managing transactions, rules, graphs, and ML models.
- **Rule & Model Analysis API**: Check the relevance of rules and ML models.
- **Recommendation Engine**: Suggest new rules, distance metrics, and graph analysis methods.
- **Report Generator**: Generate fraud detection performance statistics.
- **Compliance Alignment**: Validate all recommendations against compliance regulations.

---

## 🏛 System Architecture

- **Frontend (Optional)**: Swagger UI / Admin Panel (FastAPI + Jinja2)
- **Backend**:
  - **Python 3.10+**
  - **FastAPI** (REST API Server)
  - **LangGraph** + **LangChain** + **Open-source LLM**
  - **MongoDB Atlas / Local** (database)
  - **PyMuPDF / pdfminer** (PDF extraction)
  - **NetworkX** (graph analysis)
  - **Scikit-learn / PyTorch** (distance metrics & ML validation)

---

## 📚 Database Structure (MongoDB)

### transactions
```json
{
  "transaction_id": "string",
  "user_id": "string",
  "amount": "float",
  "timestamp": "datetime",
  "features": {...},
  "label": "fraud / non-fraud"
}
```

### policy_rules
```json
{
  "rule_id": "string",
  "name": "string",
  "condition": {...},
  "risk_score": "int"
}
```

### graph_network
```json
{
  "user_id": "string",
  "connections": [
    {"target_user": "string", "fields_matched": [...], "distance_score": "float"}
  ],
  "cluster_id": "string (optional)"
}
```

### ml_models
```json
{
  "model_id": "string",
  "description": "string",
  "version": "string",
  "accuracy": "float",
  "last_trained": "datetime"
}
```

### compliance_docs
```json
{
  "doc_id": "string",
  "title": "string",
  "content": "text",
  "uploaded_at": "datetime"
}
```

### recommendations
```json
{
  "rec_id": "string",
  "type": "rule / graph_method / ml_model",
  "content": {...},
  "compliance_checked": true/false
}
```

---

## 🚀 API Contract

### Authentication
Currently open endpoints (optionally add OAuth2/token auth in the future).

### API List

| Method | URL | Body | Response | Description |
|:--|:--|:--|:--|:--|
| POST | `/upload-compliance-pdf` | PDF File | Success/Failure | Upload a compliance PDF |
| POST | `/analyze-transactions` | JSON (transaction batch) | JSON (analysis results) | Analyze transactions |
| GET | `/get-recommendations` | None | JSON (recommendations) | Fetch rule/model recommendations |
| GET | `/get-report` | None | JSON (fraud statistics) | Retrieve fraud statistics report |
| POST | `/add-policy-rule` | JSON (new rule) | Success/Failure | Add new policy rule |
| POST | `/add-graph-rule` | JSON (graph rule) | Success/Failure | Add new graph rule |
| POST | `/upload-transactions` | JSON (transaction batch) | Success/Failure | Upload new transactions |
| GET | `/get-graph-clusters` | None | JSON (clusters) | Get user graph clusters |
| POST | `/validate-ml-model` | JSON (model parameters) | Validation Results | Validate ML model |

---

## 🔍 RAG (Retrieval Augmented Generation) Flow
1. **Upload Compliance PDF** → Extract text → Store in MongoDB.
2. **During Recommendation Generation**:
   - Query compliance documents.
   - Filter out non-compliant recommendations.
3. **Non-compliant recommendations** will be automatically discarded.

---

## 🧠 LangGraph LLM Architecture

| Node | Function |
|:--|:--|
| Node 1 | Preprocessing Input (Transaction, Rule, Graph Data) |
| Node 2 | Compliance Validator (cross-check compliance docs) |
| Node 3 | Recommendation Generator (rules, graph, ML updates) |
| Node 4 | Report Generator (fraud detection performance) |

---

## 📈 Fraud/Anomaly Analysis

### Policy Engine
- Math-based comparison logic:
  - `equal`, `greater than`, `lower than`, `lower equal`
- **Velocity rule**:
  - Aggregate `count`, `sum`, `average` → compared to threshold.
- Output: **risk score** per transaction.

### Graph Service
- Analyze user relationship via field matches.
- Distance computation using **Manhattan** / **Euclidean** / **Cosine** metrics.
- Form user **clusters** based on proximity.

### Neural Network Engine
- Neural network classifier for fraud/non-fraud.
- Predicts fraud probability and scoring.

### Final Decision
- Combine risk scores from Policy + Graph + ML models.

---

## 📊 Statistics Report

- False Positive Rate
- False Negative Rate
- Fraud Rate
- Precision, Recall, F1-Score
- Risk Score Distribution
- Top Contributing Rules

---

## 🧰 Technology Stack

| Component | Technology |
|:--|:--|
| Programming Language | Python 3.10+ |
| API Server | FastAPI |
| LLM Framework | LangGraph + LangChain |
| Database | MongoDB |
| PDF Parsing | PyMuPDF / pdfminer |
| Graph Analysis | NetworkX |
| ML & Distance Metric | Scikit-learn / PyTorch |
| Deployment (Optional) | Docker |
| API Documentation | Swagger UI |

---

## 🛠 Next Steps Development
- Build **ERD Diagram** for all MongoDB collections.
- Create **Sequence Diagram** for transaction-fraud detection flow.
- Generate **OpenAPI Spec** for full API documentation.
- Setup **CI/CD pipeline** for automated deployment.
- Integrate **LLM Fine-Tuning** for optimal rule recommendations.

---

# 📌 Notes
- All features must comply with active **compliance regulations**.
- All recommendations must pass a compliance validation check before deployment.
