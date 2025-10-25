from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import joblib
import numpy as np
import re
from fractions import Fraction
from utils import load_data
from typing import Dict

def train_model(df, output_model_path='model.pkl'):
    """Train a TF-IDF model on cleaned recipes for ingredient matching."""
    df['ingredient_string'] = df['NER'].apply(lambda x: ' '.join(eval(x) if isinstance(x, str) else x))
    vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
    ingredient_vectors = vectorizer.fit_transform(df['ingredient_string'])
    joblib.dump({
        'vectorizer': vectorizer,
        'vectors': ingredient_vectors,
        'recipes': df
    }, output_model_path)
    print(f"Model saved to {output_model_path}")
    return vectorizer, ingredient_vectors, df

def is_cheap_mass_producible(recipe):
    """Check if recipe is a soup, stew, or casserole."""
    preferred_types = ['soup', 'stew', 'casserole']
    return recipe['recipe_type'] in preferred_types

def has_high_end_ingredients(ingredients):
    """Check for high-end ingredients to exclude."""
    high_end_keywords = [
        'steak', 'lobster', 'shrimp', 'salmon', 'tuna', 'crab', 'oyster', 'caviar',
        'truffle', 'foie gras', 'saffron', 'filet mignon', 'veal', 'lamb', 'duck'
    ]
    return any(keyword in ' '.join(ingredients).lower() for keyword in high_end_keywords)

def scale_quantities(quantities: Dict[str, str], original_servings: int, target_servings: int) -> Dict[str, str]:
    """Scale ingredient quantities based on servings."""
    if original_servings < 2:  # Ensure valid servings
        original_servings = 2
    scale_factor = target_servings / original_servings
    scaled_quantities = {}
    for ingr, qty in quantities.items():
        try:
            match = re.match(r'(\d+\.?\d*/?\d*)\s*(c\.|cup|tsp\.|tbsp\.|oz\.|pound|lb\.|teaspoon|tablespoon)?', qty)
            if match:
                num, unit = match.groups()
                num_value = float(Fraction(num.replace('/', '.')))
                scaled_num = num_value * scale_factor
                scaled_qty = f"{scaled_num:.2f} {unit or ''}".strip()
                scaled_quantities[ingr] = scaled_qty
            else:
                scaled_quantities[ingr] = qty
        except:
            scaled_quantities[ingr] = qty
    return scaled_quantities

def suggest_recipe(input_ingredients, target_servings=10, model_path='model.pkl', top_n=3):
    """Suggest a recipe, prioritizing soups/stews/casseroles, scaling quantities."""
    input_cleaned = [re.sub(r'[^a-zA-Z\s]', '', ingr.lower().strip()) for ingr in input_ingredients]
    input_string = ' '.join(input_cleaned)
    
    model_data = joblib.load(model_path)
    vectorizer = model_data['vectorizer']
    ingredient_vectors = model_data['vectors']
    recipes = model_data['recipes']
    
    input_vector = vectorizer.transform([input_string])
    similarities = cosine_similarity(input_vector, ingredient_vectors)
    
    recipe_indices = np.argsort(similarities[0])[::-1]
    selected_recipes = []
    for idx in recipe_indices:
        recipe = recipes.iloc[idx]
        ingredients = eval(recipe['NER']) if isinstance(recipe['NER'], str) else recipe['NER']
        if not has_high_end_ingredients(ingredients):
            score = similarities[0][idx]
            boosted_score = score * 1.5 if is_cheap_mass_producible(recipe) else score
            selected_recipes.append((idx, boosted_score))
        if len(selected_recipes) >= top_n:
            break
    
    if not selected_recipes:
        return None
    
    best_idx, _ = max(selected_recipes, key=lambda x: x[1])
    recipe = recipes.iloc[best_idx]
    quantities = eval(recipe['ingredient_quantities']) if isinstance(recipe['ingredient_quantities'], str) else recipe['ingredient_quantities']
    scaled_quantities = scale_quantities(quantities, recipe['servings'], target_servings)
    
    return {
        'name': recipe['title'],
        'ingredients': eval(recipe['NER']) if isinstance(recipe['NER'], str) else recipe['NER'],
        'scaled_quantities': scaled_quantities,
        'directions': recipe['instructions'],
        'serves': target_servings,
        'original_servings': recipe['servings'],
        'recipe_type': recipe['recipe_type'],
        'high_protein': recipe['high_protein'],
        'confidence': float(similarities[0][best_idx])
    }

def suggest_recipe_from_inventory(inventory_id, target_servings=10, model_path='model.pkl', inventory_path='data/mock_inventories.csv'):
    """Suggest a recipe based on inventory ID, scaling quantities."""
    inventory_df = load_data(inventory_path)
    try:
        input_ingredients = eval(inventory_df[inventory_df['inventory_id'] == inventory_id]['ingredients'].iloc[0])
        return suggest_recipe(input_ingredients, target_servings, model_path)
    except IndexError:
        print(f"Inventory ID {inventory_id} not found")
        return None