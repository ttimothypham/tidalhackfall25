from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import json
import ast

# Import Gemini helper functions
try:
    from gemini_helper import batch_analyze_recipes, generate_recipe_description, analyze_recipe_match
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI integration loaded")
except Exception as e:
    print(f"⚠️ Gemini AI not available: {e}")
    GEMINI_AVAILABLE = False

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
        print(f"✅ Successfully loaded data from {path}")
        print(f"   Total recipes: {len(recipes_df)}")
        break
    except Exception as e:
        print(f"❌ Could not load data from {path}: {e}")

if recipes_df is None:
    raise FileNotFoundError("Could not find or load the processed_data.csv file")


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Food Bank Recipe API',
        'status': 'running',
        'gemini_enabled': GEMINI_AVAILABLE,
        'endpoints': {
            'test': '/api/test (GET)',
            'recommend': '/api/recommend (POST)'
        }
    })


@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'API is working!',
        'recipes_loaded': len(recipes_df) if recipes_df is not None else 0,
        'gemini_enabled': GEMINI_AVAILABLE
    })


@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    try:
        # Get selected ingredients from frontend
        data = request.get_json()
        user_ingredients = data.get('selected_ingredients', [])
        use_ai = data.get('use_ai', True)  # Option to enable/disable AI
        
        print(f"\n🔍 Searching for recipes with: {user_ingredients}")
        print(f"   AI Enhancement: {'Enabled' if (use_ai and GEMINI_AVAILABLE) else 'Disabled'}")
        
        if not user_ingredients:
            return jsonify({'error': 'No ingredients provided'}), 400
        
        # Step 1: Filter recipes using pandas
        matches = []
        
        for idx, recipe in recipes_df.iterrows():
            try:
                # Parse ingredients_list if it's a string
                if isinstance(recipe['ingredients'], str):
                    try:
                        ingredients_list = ast.literal_eval(recipe['ingredients'])
                    except:
                        ingredients_list = recipe['ingredients'].split(',')
                else:
                    ingredients_list = recipe['ingredients']
                
                # Convert to list if it's not already
                if not isinstance(ingredients_list, list):
                    ingredients_list = [str(ingredients_list)]
                
                # Count matching ingredients
                match_count = 0
                for user_ing in user_ingredients:
                    for recipe_ing in ingredients_list:
                        if user_ing.lower() in str(recipe_ing).lower():
                            match_count += 1
                            break
                
                # Only include recipes with at least 2 matches
                if match_count >= 2:
                    matches.append({
                        'title': str(recipe['title']),
                        'ingredients_list': ingredients_list,
                        'directions': str(recipe.get('directions', 'No directions available')),
                        'basic_match_score': match_count
                    })
            
            except Exception as e:
                # Skip recipes that cause errors
                continue
        
        print(f"   Found {len(matches)} matching recipes")
        
        # Step 2: Sort and get top matches
        top_matches = sorted(matches, key=lambda x: x['basic_match_score'], reverse=True)[:10]
        
        # Step 3: Enhance with AI if available and enabled
        if use_ai and GEMINI_AVAILABLE and len(top_matches) > 0:
            print(f"   🤖 Enhancing top 5 recipes with Gemini AI...")
            try:
                # Use Gemini to analyze top 5 recipes
                enhanced_recipes = batch_analyze_recipes(user_ingredients, top_matches, top_n=5)
                
                # Format for frontend
                results = []
                for recipe in enhanced_recipes:
                    # Parse ingredients if needed
                    if isinstance(recipe['ingredients'], list):
                        ingredients_display = ', '.join(str(x) for x in recipe['ingredients'])
                    else:
                        ingredients_display = str(recipe['ingredients'])
                    
                    results.append({
                        'title': recipe['title'],
                        'ingredients': ingredients_display,
                        'directions': recipe['instructions'],
                        'match_score': recipe['match_score'],
                        'ai_description': recipe.get('description', ''),
                        'ai_explanation': recipe.get('explanation', ''),
                        'missing_ingredients': recipe.get('missing_ingredients', []),
                        'substitutions': recipe.get('substitutions', {}),
                        'ai_enhanced': True
                    })
                
                print(f"   ✅ AI enhancement complete!")
                
            except Exception as e:
                print(f"   ⚠️ AI enhancement failed: {e}, falling back to basic results")
                use_ai = False  # Fall back to basic results
        
        # If AI not available or disabled, return basic results
        if not use_ai or not GEMINI_AVAILABLE:
            results = []
            for match in top_matches[:5]:
                # Parse ingredients if needed
                if isinstance(match['ingredients_list'], list):
                    ingredients_display = ', '.join(str(x) for x in match['ingredients_list'])
                else:
                    ingredients_display = str(match['ingredients_list'])
                
                results.append({
                    'title': match['title'],
                    'ingredients': ingredients_display,
                    'directions': match['directions'],
                    'match_score': match['basic_match_score'],
                    'ai_enhanced': False
                })
        
        print(f"   Returning {len(results)} recipes")
        
        return jsonify({
            'recommendations': results,
            'total_found': len(matches),
            'ai_enhanced': use_ai and GEMINI_AVAILABLE
        })
    
    except Exception as e:
        print(f"❌ Error in get_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'details': 'Check server console for more info'
        }), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Food Bank Recipe API")
    print("="*50)
    print(f"📊 Recipes loaded: {len(recipes_df) if recipes_df is not None else 0}")
    print(f"🤖 Gemini AI: {'Enabled ✅' if GEMINI_AVAILABLE else 'Disabled ⚠️'}")
    print(f"🌐 Server running on: http://127.0.0.1:5000")
    print(f"🧪 Test endpoint: http://127.0.0.1:5000/api/test")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)