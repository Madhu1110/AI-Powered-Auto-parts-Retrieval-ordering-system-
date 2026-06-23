Automotive Parts Assistant
1. System Overview
This project implements an AI-powered automotive parts assistant capable of:
Retrieving relevant products using RAG
Selecting appropriate tools (function calling)
Handling conversational queries
Providing grounded responses (no hallucination)
Forecasting demand (Part B)

2. Architecture
Pipeline:
User Query
→ Guardrails
→ Intent Detection
→ Clarification (if needed)
→ Retrieval (RAG)
→ LLM Decision
→ Tool Execution
→ Response

3. Retrieval (RAG)
Approach:
Implemented keyword-based + structured filtering retrieval
Avoided full prompt stuffing (as required)
Why not embeddings?
Dataset is structured (SKU, product name, vehicle)
Deterministic matching gives:
oFaster performance
oBetter grounding
oLower hallucination risk
Retrieval Strategy:
Product queries → fuzzy/keyword match
Vehicle queries → exact vehicle filtering

4. Tools (Function Calling)
Implemented Tools:
1. check_stock(product_name)
Returns:
oproduct
oprice (price_inr mapped)
ostock
2. create_order(product_name, quantity)
Returns structured output
Validates product existence
3. find_parts_by_vehicle(vehicle)
Returns list of compatible parts

5. Decision Logic
LLM selects action using strict rules:
Product mentioned → check_stock
Buying intent → create_order
Vehicle query → find_parts_by_vehicle

6. Guardrails
Implemented client-side guardrails:
Rejects off-topic queries
Prevents LLM hallucination
Reduces latency
Example: “Tell me a joke” → Rejected

7. Clarification Handling
Ambiguous queries are intercepted:
Example: “show parts” → asks clarification

8. Grounding
All outputs:
Come strictly from dataset
No fabricated price/stock

9. Conversation Handling
Maintains chat-style interaction
Supports multi-turn queries
Context tracked via conversation history

10. Evaluation
Metrics:
Tool accuracy
Response correctness
Grounding validity
Test Coverage:
Guardrails
Ambiguous queries
Product queries
Vehicle queries
Order flows

11. Demand Forecasting (Part B)
Approach:
Per-SKU time series forecasting
Train/Test split (no leakage)
4-week prediction horizon
Models:
Baseline: Last value
Model: Moving Average
Metrics:
MAPE
MAE
Result:
Model improves MAE over baseline

12. Failure Modes
Typos in vehicle names
Ambiguous product queries
Sparse SKU data
Improvements:
Add fuzzy matching
Add embeddings
Add typo correction

13. Future Enhancements
Vector search (FAISS)
WhatsApp UI
Image-based part detection
Advanced forecasting (ARIMA / ML)

Conclusion
The system meets all assignment requirements:
RAG implemented
Tool calling functional
Grounded responses
Evaluation included
Forecasting implemented
