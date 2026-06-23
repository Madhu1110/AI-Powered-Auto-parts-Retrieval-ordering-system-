"""
Evaluation Set for Conversational Assistant

This module contains test interactions covering:
1. Happy paths (standard queries)
2. Ambiguous queries (need clarification)
3. Out-of-stock scenarios
4. Out-of-scope requests
5. Edge cases (typos, variations)
"""

import json
from pathlib import Path


class EvaluationSet:
    """Test interactions and expected behavior"""
    
    TEST_CASES = [
        # ============================================================================
        # HAPPY PATHS - Standard, well-defined queries
        # ============================================================================
        {
            "id": "HP_001",
            "category": "HAPPY_PATH",
            "subcategory": "check_stock_specific",
            "query": "What's the price of the Honda Unicorn tyre?",
            "expected_action": "check_stock",
            "expected_tool_params": {
                "product_name": "Tubeless Tyre — Honda Unicorn"
            },
            "test_name": "Check stock for specific product",
            "description": "User asks for price of a product - should use check_stock"
        },
        {
            "id": "HP_002",
            "category": "HAPPY_PATH",
            "subcategory": "check_stock_general",
            "query": "Show me available tyres",
            "expected_action": "check_stock",
            "expected_tool_params": {
                "product_name": "tyre"
            },
            "test_name": "Search for product category",
            "description": "User searches by product type - retrieval should find tyres"
        },
        {
            "id": "HP_003",
            "category": "HAPPY_PATH",
            "subcategory": "find_parts_vehicle",
            "query": "What parts are available for Yamaha FZ?",
            "expected_action": "find_parts_by_vehicle",
            "expected_tool_params": {
                "vehicle": "Yamaha FZ"
            },
            "test_name": "List parts for vehicle",
            "description": "User asks for all parts compatible with a vehicle"
        },
        {
            "id": "HP_004",
            "category": "HAPPY_PATH",
            "subcategory": "create_order_simple",
            "query": "I want to buy a clutch plate set for Yamaha FZ",
            "expected_action": "create_order",
            "expected_tool_params": {
                "product_name": "Clutch Plate Set — Yamaha FZ",
                "quantity": 1
            },
            "test_name": "Create order with specific product",
            "description": "User explicitly states intent to purchase"
        },
        {
            "id": "HP_005",
            "category": "HAPPY_PATH",
            "subcategory": "create_order_quantity",
            "query": "Order 2 side mirrors for Honda Hornet 2.0",
            "expected_action": "create_order",
            "expected_tool_params": {
                "product_name": "Side Mirror Set — Honda Hornet 2.0",
                "quantity": 2
            },
            "test_name": "Create order with quantity",
            "description": "User specifies both product and quantity"
        },
        {
            "id": "HP_006",
            "category": "HAPPY_PATH",
            "subcategory": "product_availability",
            "query": "Is the horn for Yamaha R15 in stock?",
            "expected_action": "check_stock",
            "expected_tool_params": {
                "product_name": "Horn Set — Yamaha R15"
            },
            "test_name": "Check stock availability",
            "description": "User checks if product is available",
            "expected_response_contains": "stock"
        },
        {
            "id": "HP_007",
            "category": "HAPPY_PATH",
            "subcategory": "price_query",
            "query": "How much is the car seat cover for Kia Seltos?",
            "expected_action": "check_stock",
            "expected_tool_params": {
                "product_name": "Car Seat Cover Set — Kia Seltos"
            },
            "test_name": "Price inquiry",
            "description": "User asks for product price"
        },
        
        # ============================================================================
        # AMBIGUOUS QUERIES - Need clarification
        # ============================================================================
        {
            "id": "AMB_001",
            "category": "AMBIGUOUS",
            "subcategory": "missing_vehicle",
            "query": "I need brake pads",
            "expected_action": "needs_clarification",
            "clarification": "For which vehicle?",
            "test_name": "Product without vehicle context",
            "description": "User requests product without specifying vehicle - should ask for vehicle"
        },
        {
            "id": "AMB_002",
            "category": "AMBIGUOUS",
            "subcategory": "generic_search",
            "query": "Show me oil filters",
            "expected_action": "check_stock",
            "expected_tool_params": {
                "product_name": "oil filter"
            },
            "test_name": "Generic product search",
            "description": "User searches by product type without specific model",
            "notes": "RAG should surface all oil filters"
        },
        {
            "id": "AMB_003",
            "category": "AMBIGUOUS",
            "subcategory": "unclear_intent",
            "query": "Hornet mirrors",
            "expected_action": "could_be_check_stock",
            "possible_params": {
                "product_name": "Side Mirror Set — Honda Hornet 2.0"
            },
            "test_name": "Abbreviated query",
            "description": "User uses shorthand - should still match product"
        },
        {
            "id": "AMB_004",
            "category": "AMBIGUOUS",
            "subcategory": "multiple_matches",
            "query": "clutch",
            "expected_action": "needs_product_selection",
            "test_name": "Ambiguous product query",
            "description": "Query could match multiple products"
        },
        
        # ============================================================================
        # OUT-OF-STOCK SCENARIOS
        # ============================================================================
        {
            "id": "OOS_001",
            "category": "OUT_OF_STOCK",
            "subcategory": "order_unavailable",
            "query": "I want to order the Horn Set for Yamaha R15",
            "expected_action": "create_order",
            "expected_result": "out_of_stock_error",
            "test_name": "Order for out-of-stock product",
            "description": "User tries to order product with 0 stock (current: 0 units)",
            "expected_response_contains": "Insufficient stock"
        },
        {
            "id": "OOS_002",
            "category": "OUT_OF_STOCK",
            "subcategory": "quantity_exceeds_stock",
            "query": "I need 1000 tyres for Honda Unicorn",
            "expected_action": "create_order",
            "expected_result": "insufficient_quantity",
            "test_name": "Quantity exceeds available stock",
            "description": "User requests quantity greater than available",
            "expected_response_contains": "only"
        },
        
        # ============================================================================
        # OUT-OF-SCOPE REQUESTS
        # ============================================================================
        {
            "id": "OOS_001",
            "category": "OUT_OF_SCOPE",
            "subcategory": "product_not_in_catalog",
            "query": "Do you have airplane parts?",
            "expected_action": "check_stock",
            "expected_result": "product_not_found",
            "test_name": "Product category not in catalog",
            "description": "User asks for product outside catalog scope",
            "expected_response_contains": "not found"
        },
        {
            "id": "OOS_002",
            "category": "OUT_OF_SCOPE",
            "subcategory": "non_product_query",
            "query": "What's the capital of India?",
            "expected_action": "cannot_help",
            "test_name": "General knowledge question",
            "description": "User asks unrelated question",
            "expected_response_contains": "automotive|parts|catalog"
        },
        {
            "id": "OOS_003",
            "category": "OUT_OF_SCOPE",
            "subcategory": "vehicle_not_supported",
            "query": "What parts do you have for a Ferrari?",
            "expected_action": "find_parts_by_vehicle",
            "expected_result": "no_results",
            "test_name": "Vehicle not in catalog",
            "description": "User queries for vehicle with no compatible parts",
            "expected_response_contains": "No parts found|not available"
        },
        {
            "id": "OOS_004",
            "category": "OUT_OF_SCOPE",
            "subcategory": "installation_advice",
            "query": "How do I install a clutch plate set?",
            "expected_action": "cannot_help",
            "test_name": "Installation/technical advice",
            "description": "User asks for technical support outside catalog scope"
        },
        
        # ============================================================================
        # EDGE CASES - Typos, Variations, Boundary Conditions
        # ============================================================================
        {
            "id": "EDGE_001",
            "category": "EDGE_CASE",
            "subcategory": "typo_tyre_tires",
            "query": "Show me tire options for Honda Unicorn",
            "expected_action": "check_stock",
            "test_name": "Common spelling variation (tire vs tyre)",
            "description": "Query normalization should handle 'tire' → 'tyre'"
        },
        {
            "id": "EDGE_002",
            "category": "EDGE_CASE",
            "subcategory": "case_insensitive",
            "query": "HONDA UNICORN TUBELESS TYRE",
            "expected_action": "check_stock",
            "test_name": "All caps input",
            "description": "Should match case-insensitively"
        },
        {
            "id": "EDGE_003",
            "category": "EDGE_CASE",
            "subcategory": "partial_product_name",
            "query": "Clutch plates",
            "expected_action": "check_stock",
            "test_name": "Partial product name",
            "description": "Should match 'Clutch Plate Set — Yamaha FZ'"
        },
        {
            "id": "EDGE_004",
            "category": "EDGE_CASE",
            "subcategory": "empty_query",
            "query": "",
            "expected_action": "clarification",
            "test_name": "Empty query",
            "description": "User provides empty input"
        },
        {
            "id": "EDGE_005",
            "category": "EDGE_CASE",
            "subcategory": "special_characters",
            "query": "Car Seat Cover — Kia Seltos",
            "expected_action": "check_stock",
            "test_name": "Special characters in query",
            "description": "Should handle em-dashes and special chars"
        },
        {
            "id": "EDGE_006",
            "category": "EDGE_CASE",
            "subcategory": "whitespace_handling",
            "query": "  clutch   plate   yamaha  ",
            "expected_action": "check_stock",
            "test_name": "Extra whitespace",
            "description": "Should normalize whitespace"
        },
        {
            "id": "EDGE_007",
            "category": "EDGE_CASE",
            "subcategory": "numbers_in_query",
            "query": "Honda Hornet 2.0 mirrors",
            "expected_action": "check_stock",
            "test_name": "Model numbers in query",
            "description": "Should handle version numbers (2.0, R15, etc.)"
        },
        
        # ============================================================================
        # MULTI-TURN SCENARIOS
        # ============================================================================
        {
            "id": "MULTI_001",
            "category": "MULTI_TURN",
            "subcategory": "clarification_flow",
            "turns": [
                {
                    "user": "I need brake pads",
                    "expected_response_type": "clarification",
                    "expected_contains": "vehicle"
                },
                {
                    "user": "For my Honda Unicorn",
                    "expected_response_type": "error_or_listing",
                    "description": "No brake pads in catalog, should handle gracefully"
                }
            ],
            "test_name": "Multi-turn clarification",
            "description": "User provides additional context in second turn"
        },
        {
            "id": "MULTI_002",
            "category": "MULTI_TURN",
            "subcategory": "browse_then_buy",
            "turns": [
                {
                    "user": "What parts fit Yamaha FZ?",
                    "expected_response_type": "parts_list"
                },
                {
                    "user": "Order the clutch plate set",
                    "expected_response_type": "order_confirmation",
                    "description": "User references product from previous response"
                }
            ],
            "test_name": "Browse then purchase",
            "description": "User browses parts, then decides to order"
        },
        
        # ============================================================================
        # GROUNDING & ACCURACY
        # ============================================================================
        {
            "id": "GROUND_001",
            "category": "GROUNDING",
            "subcategory": "price_accuracy",
            "query": "What's the price of Clutch Plate Set for Yamaha FZ?",
            "expected_action": "check_stock",
            "expected_price": 2725,
            "test_name": "Exact price verification",
            "description": "Verify price is returned from catalog, not hallucinated"
        },
        {
            "id": "GROUND_002",
            "category": "GROUNDING",
            "subcategory": "stock_accuracy",
            "query": "How many Tubeless Tyres for Honda Unicorn are in stock?",
            "expected_action": "check_stock",
            "expected_stock": 324,
            "test_name": "Exact stock verification",
            "description": "Verify stock count is from catalog"
        },
        {
            "id": "GROUND_003",
            "category": "GROUNDING",
            "subcategory": "no_invention",
            "query": "Do you have iOS app for tracking orders?",
            "expected_action": "clarification_or_error",
            "test_name": "No information hallucination",
            "description": "Should not invent features not in catalog"
        },
    ]

    @classmethod
    def get_all_tests(cls):
        """Return all test cases"""
        return cls.TEST_CASES

    @classmethod
    def get_tests_by_category(cls, category):
        """Get tests by category"""
        return [t for t in cls.TEST_CASES if t.get("category") == category]

    @classmethod
    def get_happy_paths(cls):
        """Get all happy path tests"""
        return cls.get_tests_by_category("HAPPY_PATH")

    @classmethod
    def get_ambiguous(cls):
        """Get all ambiguous query tests"""
        return cls.get_tests_by_category("AMBIGUOUS")

    @classmethod
    def get_edge_cases(cls):
        """Get all edge case tests"""
        return cls.get_tests_by_category("EDGE_CASE")

    @classmethod
    def get_out_of_scope(cls):
        """Get all out-of-scope tests"""
        return cls.get_tests_by_category("OUT_OF_SCOPE")


def export_tests_to_json(output_file="eval_tests.json"):
    """Export test cases to JSON for easy reference"""
    tests = EvaluationSet.get_all_tests()
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tests, f, indent=2, ensure_ascii=False)
    print(f"✓ Exported {len(tests)} test cases to {output_file}")


def print_test_summary():
    """Print summary of test coverage"""
    tests = EvaluationSet.get_all_tests()
    
    print("\n" + "="*70)
    print("EVALUATION SET SUMMARY")
    print("="*70)
    
    categories = {}
    for test in tests:
        cat = test.get("category", "UNKNOWN")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)
    
    total_tests = len(tests)
    print(f"\nTotal Test Cases: {total_tests}\n")
    
    for category in sorted(categories.keys()):
        count = len(categories[category])
        percentage = (count / total_tests) * 100
        print(f"  {category:15s} : {count:2d} tests ({percentage:5.1f}%)")
    
    print("\n" + "="*70)
    print("\nTest Categories:")
    print("  • HAPPY_PATH     : Standard well-defined queries")
    print("  • AMBIGUOUS      : Queries requiring clarification")
    print("  • OUT_OF_STOCK   : Inventory constraint scenarios")
    print("  • OUT_OF_SCOPE   : Requests outside catalog")
    print("  • EDGE_CASE      : Typos, special chars, boundary cases")
    print("  • MULTI_TURN     : Multi-turn conversation flows")
    print("  • GROUNDING      : Data accuracy verification")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Print summary
    print_test_summary()
    
    # Export to JSON
    export_tests_to_json()
    
    # Print sample test cases
    print("\nSample Happy Path Tests:")
    for test in EvaluationSet.get_happy_paths()[:2]:
        print(f"\n  ID: {test['id']}")
        print(f"  Query: {test['query']}")
        print(f"  Action: {test['expected_action']}")
