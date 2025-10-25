import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from tests.test_model import (
    test_processed_data,
    test_unique_ingredients,
    test_suggest_recipe,
    test_suggest_recipe_from_inventory,
    test_validate_processed_data
)

def run_all_tests():
    print("Running test_processed_data...")
    test_processed_data()
    print("Running test_unique_ingredients...")
    test_unique_ingredients()
    print("Running test_suggest_recipe...")
    test_suggest_recipe()
    print("Running test_suggest_recipe_from_inventory...")
    test_suggest_recipe_from_inventory()
    print("Running test_validate_processed_data...")
    test_validate_processed_data()
    print("All tests completed successfully!")

if __name__ == "__main__":
    run_all_tests()