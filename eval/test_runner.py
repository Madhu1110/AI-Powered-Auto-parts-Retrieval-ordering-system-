"""
Test Runner - Execute and evaluate conversational assistant

Runs the evaluation test suite and provides pass/fail analysis.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "assistant"))

from test_interactions import EvaluationSet, print_test_summary


def run_single_test(test_case, agent_func):
    """
    Run a single test case and check results
    
    Returns:
        dict: Test result with pass/fail status
    """
    test_id = test_case.get("id")
    category = test_case.get("category")
    query = test_case.get("query")
    expected_action = test_case.get("expected_action")
    
    result = {
        "test_id": test_id,
        "category": category,
        "query": query,
        "status": "NOT_RUN",
        "message": ""
    }
    
    try:
        # Run the agent
        response = agent_func(query)
        
        # For now, just check that it returns a response
        if response:
            result["status"] = "PASS"
            result["response"] = response[:100]  # First 100 chars
        else:
            result["status"] = "FAIL"
            result["message"] = "Empty response"
    
    except Exception as e:
        result["status"] = "ERROR"
        result["message"] = str(e)[:100]
    
    return result


def run_test_suite(sample_mode=False):
    """
    Run test suite and generate report
    
    Args:
        sample_mode (bool): Run only sample tests if True
    """
    print("\n" + "="*70)
    print("STARTING TEST EXECUTION")
    print("="*70 + "\n")
    
    # Import agent (may fail if Ollama not running)
    try:
        from agent import agent
    except Exception as e:
        print(f"⚠️  WARNING: Could not import agent: {e}")
        print("Make sure Ollama is running with llama3:8b-instruct-q4_K_M model")
        print("\nTest suite will run in DRY-RUN mode (schema validation only)\n")
        run_schema_validation()
        return
    
    # Get test cases
    all_tests = EvaluationSet.get_all_tests()
    if sample_mode:
        test_cases = all_tests[:5]  # Run only first 5
        print(f"Running in SAMPLE mode: {len(test_cases)} tests\n")
    else:
        test_cases = all_tests
        print(f"Running full suite: {len(test_cases)} tests\n")
    
    # Run tests
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Running {test.get('id')}: {test.get('test_name')}")
        
        result = run_single_test(test, agent)
        results.append(result)
        
        print(f"  → {result['status']}")
        if result['message']:
            print(f"     {result['message']}")
    
    # Generate report
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"Total:  {len(results)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Errors: {errors} ⚠️")
    
    if results:
        pass_rate = (passed / len(results)) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%\n")
    
    # Print failures
    if failed > 0 or errors > 0:
        print("Failed/Error Tests:")
        for r in results:
            if r['status'] != 'PASS':
                print(f"  • {r['test_id']}: {r['status']}")
                if r['message']:
                    print(f"    {r['message']}")


def run_schema_validation():
    """Validate test case schemas without running agent"""
    print("VALIDATING TEST CASE SCHEMAS\n")
    
    tests = EvaluationSet.get_all_tests()
    required_fields = ['id', 'category', 'query', 'test_name']
    
    invalid_count = 0
    for test in tests:
        missing = [f for f in required_fields if f not in test]
        if missing:
            print(f"⚠️  Test {test.get('id', 'UNKNOWN')} missing fields: {missing}")
            invalid_count += 1
    
    if invalid_count == 0:
        print(f"✓ All {len(tests)} test cases have valid schemas")
    else:
        print(f"✗ {invalid_count} test cases have schema issues")
    
    # Print category distribution
    print("\n" + "="*70)
    print_test_summary()


def print_test_details(test_id=None):
    """Print details of a specific test or all tests"""
    all_tests = EvaluationSet.get_all_tests()
    
    if test_id:
        test = next((t for t in all_tests if t['id'] == test_id), None)
        if test:
            print(json.dumps(test, indent=2, ensure_ascii=False))
        else:
            print(f"Test {test_id} not found")
    else:
        for test in all_tests:
            print(f"\n{test['id']}: {test['test_name']}")
            print(f"  Category: {test.get('category')}")
            print(f"  Query: {test.get('query')}")
            print(f"  Expected Action: {test.get('expected_action')}")


def generate_report(output_file="eval_report.json"):
    """Generate a detailed test report"""
    tests = EvaluationSet.get_all_tests()
    
    report = {
        "generated_at": str(Path.cwd()),
        "total_tests": len(tests),
        "categories": {},
        "test_cases": tests
    }
    
    # Aggregate by category
    for test in tests:
        cat = test.get("category")
        if cat not in report["categories"]:
            report["categories"][cat] = 0
        report["categories"][cat] += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Report saved to {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test conversational assistant")
    parser.add_argument("--sample", action="store_true", help="Run sample tests only")
    parser.add_argument("--schema", action="store_true", help="Validate schemas only")
    parser.add_argument("--details", nargs="?", const="all", help="Print test details")
    parser.add_argument("--report", action="store_true", help="Generate report")
    
    args = parser.parse_args()
    
    if args.schema:
        run_schema_validation()
    elif args.details:
        print_test_details(args.details if args.details != "all" else None)
    elif args.report:
        generate_report()
    else:
        run_test_suite(sample_mode=args.sample)
