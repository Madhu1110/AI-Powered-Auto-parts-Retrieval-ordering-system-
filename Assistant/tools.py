import json
from pathlib import Path
from datetime import datetime
import uuid

# Get the path to data directory
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / 'data' / 'products.json'

# Load product data
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Could not find products.json at {DATA_FILE}")

# In-memory order storage (in production, use database)
orders = []


def find_product(product_name):
    """
    Find a product by name (case-insensitive, partial matching).
    
    Args:
        product_name (str): Name or partial name of product
    
    Returns:
        dict or list: Single product, list of matches, or None
    """
    if not product_name:
        return None
    
    product_name_lower = product_name.lower().strip()
    
    # Exact matches (highest priority)
    exact_matches = [
        p for p in products 
        if p['name'].lower() == product_name_lower
    ]
    if exact_matches:
        return exact_matches
    
    # Substring matches (medium priority)
    substring_matches = [
        p for p in products 
        if product_name_lower in p['name'].lower()
    ]
    if substring_matches:
        return substring_matches
    
    # Word-level matches (lower priority)
    query_words = set(product_name_lower.split())
    word_matches = []
    
    for p in products:
        product_words = set(p['name'].lower().split())
        if query_words & product_words:  # If any word matches
            word_matches.append(p)
    
    return word_matches if word_matches else None


def check_stock(product_name):
    """
    Check stock availability for a product.
    
    Args:
        product_name (str): Name of product to check
    
    Returns:
        dict: Product details with price and stock info
    """
    if not product_name:
        return {"error": "Product name is required"}
    
    matches = find_product(product_name)
    
    if not matches:
        return {"error": f"Product '{product_name}' not found in catalog"}
    
    if isinstance(matches, list):
        if len(matches) == 1:
            return matches[0]  # Return single product
        else:
            # Multiple matches - return first 5
            return matches[:5]
    
    return matches


def create_order(product_name, quantity=1):
    """
    Create an order for a product.
    
    Args:
        product_name (str): Name of product to order
        quantity (int): Quantity to order (default: 1)
    
    Returns:
        dict: Order confirmation with order ID and details
    """
    if not product_name or quantity < 1:
        return {
            "error": "Invalid product name or quantity",
            "type": "error"
        }
    
    # Find the product
    matches = find_product(product_name)
    
    if not matches:
        return {
            "error": f"Product '{product_name}' not found in catalog",
            "type": "error"
        }
    
    # If multiple matches, pick first one
    product = matches[0] if isinstance(matches, list) else matches
    
    # Check stock
    if product['stock'] < quantity:
        return {
            "error": f"Insufficient stock. Available: {product['stock']} units, Requested: {quantity}",
            "type": "error",
            "available_stock": product['stock']
        }
    
    # Create order
    order_id = str(uuid.uuid4())[:8].upper()
    order = {
        "order_id": order_id,
        "timestamp": datetime.now().isoformat(),
        "product_sku": product['sku'],
        "product_name": product['name'],
        "quantity": quantity,
        "unit_price": product['price_inr'],
        "total_price": product['price_inr'] * quantity,
        "status": "confirmed",
        "type": "order_confirmation"
    }
    
    orders.append(order)
    
    return order


def find_parts_by_vehicle(vehicle_name):
    """
    Find all parts compatible with a specific vehicle.
    
    Args:
        vehicle_name (str): Vehicle make/model (e.g., 'Honda Unicorn')
    
    Returns:
        list: List of compatible product names
    """
    if not vehicle_name:
        return []
    
    vehicle_lower = vehicle_name.lower().strip()
    
    # Exact vehicle matches
    matches = [
        p['name']
        for p in products
        if vehicle_lower in p['vehicle_fitment'].lower()
    ]
    
    if matches:
        return matches
    
    # Partial word matches
    vehicle_words = set(vehicle_lower.split())
    partial_matches = []
    
    for p in products:
        fitment_words = set(p['vehicle_fitment'].lower().split())
        if vehicle_words & fitment_words:  # Any word overlap
            partial_matches.append(p['name'])
    
    return partial_matches if partial_matches else []


def get_order_history():
    """Get all orders created so far."""
    return orders


def get_catalog_summary():
    """Get summary statistics about the catalog."""
    return {
        "total_products": len(products),
        "categories": list(set(p['category'] for p in products)),
        "brands": list(set(p['brand'] for p in products)),
        "total_stock": sum(p['stock'] for p in products),
        "total_orders": len(orders)
    }