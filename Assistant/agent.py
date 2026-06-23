from fastapi import params
import ollama
import json
import re
from pathlib import Path
from rag import retrieve
from tools import check_stock, create_order, find_parts_by_vehicle
from vision import identify_part_from_image, get_product_image, format_response_with_image

def is_off_topic(query):
    off_topic_keywords = [
        "weather", "movie", "cricket", "politics", "news",
        "music", "game", "chatgpt", "ai model", "who are you"
    ]

    query_lower = query.lower()
    return any(word in query_lower for word in off_topic_keywords)


# Keywords to identify products vs vehicles
PRODUCT_KEYWORDS = {
    'tyre', 'tire', 'brake', 'pad', 'oil', 'filter', 'mirror', 'horn', 'seat',
    'clutch', 'chain', 'cover', 'light', 'lamp', 'battery', 'cable', 'screw',
    'bolt', 'plug', 'switch', 'belt', 'pipe', 'hose', 'valve', 'seal'
}

VEHICLE_KEYWORDS = {
    'honda', 'yamaha', 'bajaj', 'hero', 'tvs', 'royal', 'enfield',
    'ktm', 'bmw', 'harley', 'suzuki', 'kawasaki', 'ducati', 'jawa',
    'activa', 'unicorn', 'fz', 'hornet', 'r15', 'dominar', 'avenger',
    'bullet', 'sportsbike', 'cruiser', 'scooter', 'bike', 'motorcycle'
}


def format_response(result):
    """
    Format response for display with optional image attachment.
    
    Returns:
        dict: {
            'text': str (the formatted response text),
            'image': None or {'path': str, 'url': str},
            'has_image': bool
        }
    """
    response_obj = {
        'text': '',
        'image': None,
        'has_image': False
    }
    
    if result is None:
        response_obj['text'] = "No results found."
        return response_obj
    
    product_name = None
    
    if isinstance(result, dict):
        if "error" in result:
            response_obj['text'] = f"❌ {result['error']}"
            return response_obj
        
        # Order confirmation
        if result.get("type") == "order_confirmation":
            product_name = result.get('product_name')
            response_obj['text'] = f"""✅ ORDER CONFIRMED!
   Order ID: {result['order_id']}
   Product: {result['product_name']}
   Quantity: {result['quantity']}
   Unit Price: ₹{result['unit_price']}
   Total Price: ₹{result['total_price']}
   Status: {result['status']}"""
        
        # Parts list
        elif result.get("type") == "parts_list":
            if isinstance(result["result"], list) and len(result["result"]) > 0:
                text = "Available parts for this vehicle:\n"
                for i, part in enumerate(result["result"][:10], 1):
                    text += f"{i}. {part}\n"
                response_obj['text'] = text
            else:
                response_obj['text'] = "No parts found for this vehicle."
            return response_obj
        
        # Product info (stock check)
        elif "name" in result:
            product_name = result.get('name')
            price = f"₹{result.get('price_inr', 'N/A')}"
            stock = result.get('stock', 'N/A')
            response_obj['text'] = f"✓ {result['name']}\n   Price: {price}\n   Stock: {stock} units"
    
    elif isinstance(result, list) and len(result) > 0:
        text = "Available products:\n"
        for i, p in enumerate(result[:5], 1):
            price = f"₹{p.get('price_inr', 'N/A')}"
            stock = p.get('stock', 'N/A')
            text += f"{i}. {p['name']} | {price} | Stock: {stock}\n"
            # Get first product's image
            if i == 1:
                product_name = p['name']
        response_obj['text'] = text
    
    elif isinstance(result, str):
        response_obj['text'] = result
        return response_obj
    
    else:
        response_obj['text'] = str(result)
        return response_obj
    
    # Try to attach image for product responses
    if product_name:
        image_info = get_product_image(product_name)
        if image_info['has_image']:
            response_obj['image'] = {
                'path': image_info['image_path'],
                'url': image_info['image_url']
            }
            response_obj['has_image'] = True
    
    return response_obj


def prepare_agent_response(response_obj):
    """
    Converts format_response output to a final response string with image metadata.
    Handles both old string responses and new dict responses.
    
    Args:
        response_obj: dict or str - output from format_response() or simple string
    
    Returns:
        str or dict - formatted for display/API
    """
    if isinstance(response_obj, dict) and 'text' in response_obj:
        # New format with potential images
        if response_obj.get('has_image') and response_obj.get('image'):
            # Return structured response with image
            return {
                'message': response_obj['text'],
                'image': response_obj['image'],
                'has_image': True
            }
        else:
            # Just text, no image
            return response_obj['text']
    
    # Fallback for strings or other formats
    return response_obj


def normalize_query(query):
    """Normalize user query for better matching."""
    query = query.lower().strip()
    query = query.replace("avtiva", "activa")
    query = query.replace("tyres", "tyre")
    return query


def detect_intent(query_text):
    """
    Quick detection of whether query mentions products or vehicles.
    Returns: ('product', name) | ('vehicle', name) | ('unclear', None)
    """
    query_lower = query_text.lower()
    
    # Check for product keywords
    for keyword in PRODUCT_KEYWORDS:
        if keyword in query_lower:
            return ('product', keyword)
    
    # Check for vehicle keywords
    for keyword in VEHICLE_KEYWORDS:
        if keyword in query_lower:
            return ('vehicle', keyword)
    
    return ('unclear', None)


def detect_purchase_intent(query_text):
    """
    Client-side detection of purchase intent (HIGHEST PRIORITY).
    Returns True if user clearly wants to buy/order.
    """
    query_lower = query_text.lower()
    purchase_keywords = ['buy', 'order', 'purchase', 'want to buy', 'want to order', 
                        'i need to buy', 'i need to order', 'place an order', 'make an order',
                        'give me', 'send me', 'deliver', 'book']
    
    for keyword in purchase_keywords:
        if keyword in query_lower:
            return True
    
    return False


def detect_vehicle_search(query_text):
    """
    Client-side detection of vehicle parts search.
    Returns vehicle name if found, None otherwise.
    """
    query_lower = query_text.lower()
    
    # Check for "parts for" or "parts compatible with" patterns
    if 'parts' in query_lower and ('for' in query_lower or 'compatible' in query_lower or 'fit' in query_lower):
        # Extract vehicle name if it's a known vehicle
        for keyword in VEHICLE_KEYWORDS:
            if keyword in query_lower:
                return keyword
    
    return None


def agent(query):
    """Main agent function - handles multi-turn conversation."""
    
    normalized_query = normalize_query(query)
    
    # 🚫 GUARDRAIL: off-topic detection
    if is_off_topic(query):
        return "⚠️ I can only help with automotive parts, stock, and orders."
    
    intent_type, keyword = detect_intent(normalized_query)

    # ✅ STEP : Clarification Fallback (🔥 YOUR BLOCK GOES HERE)
    if intent_type == 'product' and 'parts' in normalized_query:
        return "❓ Do you want to see tyre products, or parts for a specific vehicle?"

    # 🎯 STEP 1: Client-side high-confidence detection
    # This catches obvious cases without needing LLM
    
    # Detect PURCHASE INTENT (highest priority)
    if detect_purchase_intent(normalized_query):
        print(f"[CLIENT-SIDE] Detected purchase intent: {normalized_query}")
        
        # Use RAG to find the best matching product
        context = retrieve(normalized_query)
        
        # Extract quantity if mentioned (default 1)
        quantity = 1
        import re
        match = re.search(r'\d+', normalized_query)
        if match:
            quantity = int(match.group())
        
        # STRICT extraction prompt - JSON format only
        extract_prompt = f"""Extract product name ONLY. Return JSON with single field.

Query: {normalized_query}

Products Available:
{context}

Rules:
- Return ONLY valid JSON: {{"product": "EXACT product name"}}
- Match product type from query (tyre, filter, mirror, etc.)
- Use exact name from list above
- If no match: {{"product": null}}

RESPOND WITH VALID JSON ONLY - NO EXPLANATION."""
        
        try:
            extract_response = ollama.chat(
                model='llama3:8b-instruct-q4_K_M',
                messages=[{"role": "user", "content": extract_prompt}],
                format="json",  # Force JSON format
                options={"temperature": 0.0, "num_predict": 100}
            )
            
            response_text = extract_response['message']['content'].strip()
            print(f"[CLIENT-SIDE] Raw extraction response: {response_text}")
            
            # Parse JSON response
            try:
                extract_json = json.loads(response_text)
                product_name = extract_json.get("product")
                
                if product_name and product_name.lower() not in ['null', 'none', '']:
                    print(f"[CLIENT-SIDE] Extracted product: {product_name}")
                    result = create_order(product_name, quantity)
                    return prepare_agent_response(format_response(result))
                else:
                    print(f"[CLIENT-SIDE] No valid product extracted, using LLM decision")
            except json.JSONDecodeError:
                print(f"[CLIENT-SIDE] Invalid JSON response, using LLM decision")
        
        except Exception as e:
            print(f"[CLIENT-SIDE] Extraction error: {e}, using LLM decision")
    
    # 🔍 STEP 2: Retrieve relevant context (RAG)
    context = retrieve(normalized_query)

    # 🤖 STEP 3: Create decision prompt for LLM
    
    # Detect intent to provide hints
    intent_type, keyword = detect_intent(normalized_query)
    intent_hint = ""
    if intent_type == 'product':
        intent_hint = f"\n⚠️  Query contains PRODUCT keyword: '{keyword}'"
    elif intent_type == 'vehicle':
        intent_hint = f"\n⚠️  Query contains VEHICLE keyword: '{keyword}'"
    
    decision_prompt = f"""You are a product assistant for an automotive parts catalog.

Available Products:
{context}

User Query: {normalized_query}{intent_hint}

Action options:
1. check_stock: Returns product details, price, and availability
2. create_order: Places an order for a product
3. find_parts_by_vehicle: Finds parts compatible with a specific vehicle

PRODUCT keywords (not vehicles): tyre, tire, brake, pad, oil, filter, mirror, horn, seat, clutch, chain, cover, light, battery, cable, switch, belt, pipe, hose, valve, seal

VEHICLE keywords: Honda, Yamaha, Bajaj, Hero, TVS, Royal Enfield, KTM, BMW, Activa, Unicorn, FZ, Hornet, R15, Dominar, Avenger, Bullet, scooter, bike, motorcycle

DECISION RULES (in priority order):

1. PURCHASE INTENT (HIGHEST PRIORITY):
   If user says: "buy", "order", "purchase", "want to order", "I need to buy"
   → Use create_order (even if product not explicitly named)

2. PRODUCT SEARCH (when product keyword is in query):
   If query contains PRODUCT keyword (e.g., "show parts for tyre")
   AND NO clear VEHICLE name is mentioned
   → Ask clarification: "Do you want to see tyre products, or parts for a specific vehicle?"
   → Set needs_clarification: true

3. VEHICLE COMPATIBILITY (when vehicle is mentioned):
   If user asks: "what parts", "parts for", "what fits"
   AND mentions a VEHICLE (e.g., Honda Unicorn, Yamaha FZ)
   → Use find_parts_by_vehicle with the vehicle name

4. PRODUCT INQUIRY (DEFAULT):
   If user asks about: availability, price, stock, details, "show me"
   AND it's clearly about a product
   → Use check_stock

Respond in JSON only:
{{
    "action": "check_stock | create_order | find_parts_by_vehicle",
    "parameters": {{
        "product_name": "exact name from catalog or null",
        "quantity": integer >= 1 or null,
        "vehicle": "vehicle model or null"
    }},
    "needs_clarification": false,
    "clarification_question": "question if ambiguous"
}}"""

    # 🤖 Step 4: Get LLM decision
    try:
        decision = ollama.chat(
            model='llama3:8b-instruct-q4_K_M',
            messages=[{"role": "user", "content": decision_prompt}],
            format="json",
            options={
                "temperature": 0.1,
                "num_predict": 200
            }
        )

        decision_text = decision['message']['content']
        print("\n[DEBUG] LLM Decision:", decision_text)

        # Extract JSON from response
        start = decision_text.find("{")
        end = decision_text.rfind("}") + 1

        if start == -1 or end <= start:
            return "Error: Could not parse LLM response. Please rephrase your query."

        json_str = decision_text[start:end]
        decision_json = json.loads(json_str)

        # Check if clarification needed
        if decision_json.get("needs_clarification"):
            return f"🤔 {decision_json.get('clarification_question', 'Could you provide more details?')}"

        action = decision_json.get("action", "").strip().lower()
        params = decision_json.get("parameters", {})

        # ✅ Clarification fallback (AFTER parsing)
        if action == "check_stock" and params.get("product_name") in ["", None, "unknown"]:
            return "❓ Which product are you looking for?"

        if action == "find_parts_by_vehicle" and params.get("vehicle") in ["", None]:
            return "❓ Please specify the vehicle (e.g., Activa 6G, Meteor 350)."

        if action == "create_order" and not params.get("product_name"):
            return "❓ What product would you like to order?"

        # Execute the chosen action
        if action == "check_stock":
            product_name = params.get("product_name")
            if not product_name:
                return "Please specify a product name (e.g., 'Tubeless Tyre', 'Oil Filter')."
            result = check_stock(product_name)

            if isinstance(result, dict) and "error" in result:
                return "❌ That product is not available in our catalog."

            return prepare_agent_response(format_response(result))

        elif action == "create_order":
            product_name = params.get("product_name")
            quantity = params.get("quantity", 1)
            if not product_name:
                return "Please specify which product you'd like to order."
            result = create_order(product_name, quantity)
            return prepare_agent_response(format_response(result))

        elif action == "find_parts_by_vehicle":
            vehicle = params.get("vehicle")
            if not vehicle:
                return "Please specify a vehicle model (e.g., 'Honda Unicorn', 'Yamaha FZ')."
            result = find_parts_by_vehicle(vehicle)
            return prepare_agent_response(format_response({"result": result, "type": "parts_list"}))

        else:
            return "I couldn't determine what you're asking. Try: 'Show me brake pads' or 'What parts fit Honda Unicorn?'"

    except json.JSONDecodeError as e:
        return f"Sorry, I had trouble understanding that. Please try again."
    except Exception as e:
        return f"An error occurred: {str(e)[:100]}"
    
    


if __name__ == "__main__":
    print("🚗 Welcome to Automotive Parts Assistant!")
    print("--------------------------------------")
    print("Type 'exit' or 'quit' to end.\n")
    
    conversation_history = []
    
    while True:
        user_query = input("🧑 You: ").strip()
        
        if user_query.lower() in ["exit", "quit"]:
            print("🤖 Assistant: Goodbye! 👋")
            break
        
        if not user_query:
            continue
        

        # 🔥 Image input support
        if user_query.startswith("image:"):
            image_path = user_query.replace("image:", "").strip()

            part = identify_part_from_image(image_path)
            print(f"\nDetected Part: {part}")

            response = check_stock(part)
            print(f"\nAssistant: {response}\n")
            continue


        conversation_history.append({"role": "user", "content": user_query})
        
        response = agent(user_query)
        print(f"🤖 Assistant:\n{response}\n")
        
        conversation_history.append({"role": "assistant", "content": response})