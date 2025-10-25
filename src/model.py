from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import pandas as pd
import joblib
import numpy as np
import re
from fractions import Fraction
import os
from src.utils import load_data, estimate_servings, classify_recipe_type, parse_ingredient_quantities

def train_model(df, output_model_path=os.path.join('model.pkl')):
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

def is_cheap_mass_producible(recipe_type: str) -> bool:
    return recipe_type in ['soup', 'stew', 'casserole']

def has_high_end_ingredients(ingredients: List[str]) -> bool:
    high_end_keywords = [
        'steak', 'lobster', 'shrimp', 'salmon', 'tuna', 'crab', 'oyster', 'caviar',
        'truffle', 'foie gras', 'saffron', 'filet mignon', 'veal', 'lamb', 'duck'
    ]
    return any(keyword in ' '.join(ingredients).lower() for keyword in high_end_keywords)

def scale_quantities(quantities: Dict[str, str], original_servings: int, target_servings: int) -> Dict[str, str]:
    if original_servings < 2:
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

def suggest_recipe(input_ingredients: List[str], target_servings: int = 10, model_path: str = os.path.join('model.pkl'), top_n: int = 3):
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
        recipe_type = classify_recipe_type(recipe['title'], eval(recipe['directions']) if isinstance(recipe['directions'], str) else recipe['directions'])
        if not has_high_end_ingredients(ingredients) and not any(allergen in ' '.join(ingredients).lower() for allergen in ['milk', 'peanuts', 'sugar']):
            score = similarities[0][idx]
            boosted_score = score * 1.5 if is_cheap_mass_producible(recipe_type) else score
            selected_recipes.append((idx, boosted_score))
        if len(selected_recipes) >= top_n:
            break
    
    if not selected_recipes:
        return None
    
    best_idx, _ = max(selected_recipes, key=lambda x: x[1])
    recipe = recipes.iloc[best_idx]
    structured_ings = eval(recipe['structured_ingredients']) if isinstance(recipe['structured_ingredients'], str) else recipe['structured_ingredients']
    quantities = parse_ingredient_quantities(structured_ings)
    servings = estimate_servings(structured_ings)
    scaled_quantities = scale_quantities(quantities, servings, target_servings)
    
    return {
        'name': recipe['title'],
        'ingredients': eval(recipe['NER']) if isinstance(recipe['NER'], str) else recipe['NER'],
        'scaled_quantities': scaled_quantities,
        'directions': eval(recipe['directions']) if isinstance(recipe['directions'], str) else recipe['directions'],
        'serves': target_servings,
        'original_servings': servings,
        'recipe_type': classify_recipe_type(recipe['title'], eval(recipe['directions']) if isinstance(recipe['directions'], str) else recipe['directions']),
        'total_time_minutes': recipe['total_time_minutes'],
        'cooking_temp_f': recipe['cooking_temp_f'],
        'confidence': float(similarities[0][best_idx])
    }

def suggest_recipe_from_inventory(inventory_id: int, target_servings: int = 10, model_path: str = os.path.join('model.pkl'), inventory_path: str = os.path.join('data', 'mock_inventories.csv')):
    inventory_df = load_data(inventory_path, tier=None)
    try:
        input_ingredients = eval(inventory_df[inventory_df['inventory_id'] == inventory_id]['ingredients'].iloc[0])
        return suggest_recipe(input_ingredients, target_servings, model_path)
    except IndexError:
        print(f"Inventory ID {inventory_id} not found")
        return None