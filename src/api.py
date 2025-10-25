from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Try different paths for the data file
data_paths = [
    '../data/processed/processed_data.csv',
    'data/processed/processed_data.csv',
    os.path.join(os.path.dirname(__file__), '../data/processed/processed_data.csv')
]

recipes_df = None
for path in data_paths:
    try:
        recipes_df = pd.read_csv(path)
        print(f"Successfully loaded data from {path}")
        break
    except Exception as e:
        print(f"Could not load data from {path}: {e}")

if recipes_df is None:
    raise FileNotFoundError("Could not find or load the processed_data.csv file")

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    try:
        # Get selected ingredients from frontend
        user_ingredients = request.json['selected_ingredients']
        
        # Step 1: Filter recipes using pandas (fast)
        # Find recipes where user has most ingredients
        matches = []
        for idx, recipe in recipes_df.iterrows():
            try:
                ingredients_list = json.loads(recipe['ingredients_list'])
            except:
                ingredients_list = []
            
            match_count = sum(1 for ing in user_ingredients if any(ing.lower() in str(recipe_ing).lower() for recipe_ing in ingredients_list))
            
            if match_count >= 2:  # At least 2 matching ingredients
                matches.append({
                    'recipe': recipe,
                    'basic_match_score': match_count
                })
        
        # Step 2: Get top 10 matches
        top_matches = sorted(matches, key=lambda x: x['basic_match_score'], reverse=True)[:10]
        
        # Convert matches to JSON-friendly format
        results = []
        for match in top_matches[:5]:
            recipe = match['recipe']
            results.append({
                'title': recipe['title'],
                'ingredients': recipe['ingredients_list'],
                'directions': recipe['directions'],
                'match_score': match['basic_match_score']
            })
        
        return jsonify({
            'recommendations': results
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# Add a test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'API is working!'})

    if __name__ == '__main__':
        print("Starting Flask server...")
        app.run(debug=True, port=5000)
        description = generate_recipe_description(recipe)
            
        enhanced_results.append({
            'title': recipe['title'],
            'ingredients': recipe['ingredients_list'],
            'instructions': recipe['directions'],
            'ai_analysis': ai_analysis,
            'description': description,
            'match_score': match['basic_match_score']
        })
    
    return jsonify({'recipes': enhanced_results})


@app.route('/', methods=['POST'])
def home():
    return jsonify({
        'message': 'Food Bank Recipe API',
        'endpoints': {
            'test': '/api/test',
            'recommend': '/api/recommend (POST)'
        }
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
