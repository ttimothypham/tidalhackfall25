from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import joblib
import numpy as np
import re

def train_model(df, output_model_path='model.pkl'):
    """Train a TF-IDF model on cleaned recipes for ingredient matching."""
    # Convert stringified ingredient lists to strings for TF-IDF
    df['ingredient_string'] = df['ingredients'].apply(lambda x: ' '.join(eval(x) if isinstance(x, str) else x))
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
    ingredient_vectors = vectorizer.fit_transform(df['ingredient_string'])
    
    # Save model, vectorizer, and recipes
    joblib.dump({
        'vectorizer': vectorizer,
        'vectors': ingredient_vectors,
        'recipes': df
    }, output_model_path)
    print(f"Model saved to {output_model_path}")
    return vectorizer, ingredient_vectors, df

def suggest_recipe(input_ingredients, model_path='model.pkl'):
    """Suggest a recipe based on input ingredients."""
    # Clean input ingredients
    input_cleaned = [re.sub(r'[^a-zA-Z\s]', '', ingr.lower().strip()) for ingr in input_ingredients]
    input_string = ' '.join(input_cleaned)
    
    # Load model
    model_data = joblib.load(model_path)
    vectorizer = model_data['vectorizer']
    ingredient_vectors = model_data['vectors']
    recipes = model_data['recipes']
    
    # Transform input to TF-IDF
    input_vector = vectorizer.transform([input_string])
    
    # Compute cosine similarity
    similarities = cosine_similarity(input_vector, ingredient_vectors)
    best_match_idx = np.argmax(similarities)
    
    # Get best recipe
    recipe = recipes.iloc[best_match_idx]
    return {
        'name': recipe['title'],
        'ingredients': eval(recipe['ingredients']) if isinstance(recipe['ingredients'], str) else recipe['ingredients'],
        'directions': recipe['instructions'],
        'serves': 10,  # Placeholder (food bank estimate)
        'recipe_type': recipe['recipe_type'],
        'high_protein': recipe['high_protein'],
        'confidence': float(similarities[0][best_match_idx])
    }

def suggest_recipe_from_inventory(inventory_id, model_path='model.pkl', inventory_path='data/mock_inventories.csv'):
    """Suggest a recipe based on inventory ID."""
    inventory_df = pd.read_csv(inventory_path)
    try:
        input_ingredients = eval(inventory_df[inventory_df['inventory_id'] == inventory_id]['ingredients'].iloc[0])
        return suggest_recipe(input_ingredients, model_path)
    except IndexError:
        print(f"Inventory ID {inventory_id} not found")
        return None