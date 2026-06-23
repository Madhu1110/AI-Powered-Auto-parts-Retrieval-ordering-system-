 Automotive Parts Assistant
An AI-powered assistant for automotive parts search, stock checking, ordering, and demand forecasting.
 Features
 RAG-based product retrieval
 LLM decision-making (Ollama - LLaMA 3)
 Tool calling:
ocheck_stock
ocreate_order
ofind_parts_by_vehicle
 Chat-style CLI interface
 Guardrails (off-topic protection)
 Clarification handling
 Demand Forecasting (Part B)

 Project Structure
root/
│
├── assistant/
│   ├── agent.py
│   ├── tools.py
│   ├── rag.py
│
├── data/
│   ├── catalogue.csv
│   ├── sales.csv
│
├── forecasting/
│   ├── forecast.py
│
├── DESIGN.md
├── README.md

 Setup
1. Install dependencies
pip install pandas numpy ollama

2. Install Ollama
Download from:
https://ollama.com
Then run:
ollama pull llama3

 Run Assistant
python assistant/agent.py
Example Queries
Product Query
Do you have brake pads?
Vehicle Query
Show parts for Meteor 350
Order Query
I want to buy oil filter

Guardrails
Rejects off-topic queries:
What is the weather?
→  Not supported

Clarification
Handles ambiguity:
show parts
→ asks clarification

 Forecasting (Part B)
Run:
python forecasting/forecast.py
Output:
Per-SKU performance
Baseline vs Model comparison
MAE & MAPE metrics

Model Performance
Baseline MAE: ~9.35

Model MAE: ~8.29

Improvement achieved 

 Evaluation
Tested across:
Guardrails
Ambiguity handling
Tool accuracy
Grounded responses

 Future Improvements
Vector search (FAISS)
UI (WhatsApp style)
Multimodal input (image → part detection)
Advanced forecasting
