import pytest
import pandas as pd
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.model import suggest_recipe, suggest_recipe_from_inventory
from src.utils import extract_unique_ingredients, validate_processed_data, estimate_servings, classify_recipe_type

def test_processed_data():
    df = pd.read_csv(os.path.join(project_root, 'data', 'processed', 'processed_data.csv'))
    assert set(df.columns) == {'title', 'ingredients', 'directions', 'n_ings', 'NER', 'structured_ingredients', 'structured_directions', 'total_time_minutes', 'cooking_temp_f', 'tier'}
    assert (df['tier'] == 1).all(), "Non-tier 1 recipes found"
    assert not any(df['NER'].str.contains('milk|peanuts|sugar', case=False, na=False)), "Allergens found"
    for idx, row in df.iterrows():
        structured_ings = eval(row['structured_ingredients']) if isinstance(row['structured_ingredients'], str) else row['structured_ingredients']
        servings = estimate_servings(structured_ings)
        assert servings >= 2, f"Invalid servings for {row['title']}: {servings}"

def test_unique_ingredients():
    ingredients = extract_unique_ingredients(os.path.join(project_root, 'data', 'processed', 'processed_data.csv'))
    assert len(ingredients) > 0, "No ingredients extracted"
    assert all(isinstance(ingr, str) and ingr == ingr.lower() for ingr in ingredients), "Non-lowercase ingredients"
    assert not any(ingr in ['milk', 'peanuts', 'sugar'] for ingr in ingredients), "Allergens found"

def test_suggest_recipe():
    recipe = suggest_recipe(['potatoes', 'beans'], target_servings=10)
    assert recipe is not None, "No recipe returned"
    assert recipe['recipe_type'] in ['soup', 'stew', 'casserole', 'unknown'], "Non-savory recipe"
    assert recipe['serves'] == 10, "Incorrect target servings"
    assert recipe['original_servings'] >= 2, "Invalid original servings"
    assert not any(ingr in ['milk', 'peanuts', 'sugar', 'steak'] for ingr in recipe['ingredients']), "Allergens or high-end ingredients"
    assert recipe['confidence'] > 0, "Invalid confidence score"

def test_suggest_recipe_from_inventory():
    recipe = suggest_recipe_from_inventory(1, target_servings=20, inventory_path=os.path.join(project_root, 'data', 'mock_inventories.csv'))
    assert recipe is not None, "No inventory recipe returned"
    assert recipe['serves'] == 20, "Incorrect target servings"
    assert recipe['scaled_quantities'], "Missing scaled quantities"

def test_validate_processed_data():
    validate_processed_data(os.path.join(project_root, 'data', 'processed', 'processed_data.csv'))
    df = pd.read_csv(os.path.join(project_root, 'data', 'processed', 'processed_data.csv'))
    for idx, row in df.iterrows():
        structured_ings = eval(row['structured_ingredients']) if isinstance(row['structured_ingredients'], str) else row['structured_ingredients']
        assert estimate_servings(structured_ings) >= 2, f"Invalid servings for {row['title']}"