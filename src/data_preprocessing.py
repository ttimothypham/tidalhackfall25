from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import pandas as pd
import re
import time
from src.model import RecipeClassifier, AllergenFilter
from src.utils import ProcessingLogger, Recipe, RecipeType, FilterStats, ClassificationStats, validate_recipe

@dataclass
class ProcessingResult:
    processed_recipes: List[Recipe]
    filter_stats: FilterStats
    classification_stats: ClassificationStats

@dataclass
class ProcessingReport:
    total_recipes: int
    processed_recipes: int
    processing_time: float
    filter_stats: FilterStats
    classification_stats: ClassificationStats

def parse_ingredient_quantities(ingredient_list: str) -> Dict[str, str]:
    """Parse quantities from ingredients (e.g., '1 c. brown sugar' -> {brown sugar: 1 cup})."""
    try:
        ingredients = eval(ingredient_list) if isinstance(ingredient_list, str) else ingredient_list
        quantities = {}
        for ingr in ingredients:
            match = re.match(r'(\d+\s*/?\s*\d*\s*(?:c\.|cup|tsp\.|tbsp\.|oz\.|pound|lb\.|teaspoon|tablespoon)?)\s*(.*)', ingr)
            if match:
                quantity, name = match.groups()
                quantities[name.strip().lower()] = quantity.strip()
            else:
                quantities[ingr.strip().lower()] = "unknown"
        return quantities
    except:
        return {}

def estimate_servings(quantities: Dict[str, str], ingredients: List[str]) -> int:
    """Estimate servings based on ingredient quantities, with fallback."""
    total_units = 0
    measurable_quantities = 0
    for quantity in quantities.values():
        try:
            if 'cup' in quantity or 'c.' in quantity:
                num = float(re.findall(r'(\d+\.?\d*/?\d*)\s*(?:c\.|cup)', quantity)[0].replace('/', '.'))
                total_units += num
                measurable_quantities += 1
            elif 'tablespoon' in quantity or 'tbsp.' in quantity:
                num = float(re.findall(r'(\d+\.?\d*/?\d*)\s*(?:tbsp\.|tablespoon)', quantity)[0].replace('/', '.'))
                total_units += num / 16
                measurable_quantities += 1
            elif 'teaspoon' in quantity or 'tsp.' in quantity:
                num = float(re.findall(r'(\d+\.?\d*/?\d*)\s*(?:tsp\.|teaspoon)', quantity)[0].replace('/', '.'))
                total_units += num / 48
                measurable_quantities += 1
            elif 'pound' in quantity or 'lb.' in quantity:
                num = float(re.findall(r'(\d+\.?\d*/?\d*)\s*(?:pound|lb\.)', quantity)[0].replace('/', '.'))
                total_units += num * 2  # Assume 1 pound ~ 2 cups
                measurable_quantities += 1
            elif 'oz.' in quantity:
                num = float(re.findall(r'(\d+\.?\d*/?\d*)\s*oz\.', quantity)[0].replace('/', '.'))
                total_units += num / 8  # 1 oz ~ 1/8 cup
                measurable_quantities += 1
        except:
            continue
    
    if measurable_quantities > 0:
        servings = max(2, int(total_units * 2))  # ~1 cup = 2 servings
    else:
        # Fallback: Estimate based on number of ingredients
        num_ingredients = len(ingredients)
        servings = max(2, min(4, num_ingredients))  # 2-4 servings based on ingredient count
        logger = ProcessingLogger()
        logger.log_warning("Serving estimation", f"Using fallback for servings: {servings} (based on {num_ingredients} ingredients)")
    
    return servings

class DataProcessor:
    def __init__(self, input_path: str = "data/raw/full_dataset.csv", output_path: str = "data/processed/processed_data.csv"):
        self.input_path = input_path
        self.output_path = output_path
        self.logger = ProcessingLogger()
        self.classifier = RecipeClassifier()
        self.allergen_filter = AllergenFilter()
        self.start_time = None

    def process_dataset(self) -> ProcessingResult:
        """Process RecipeNLG CSV, including non-optional servings."""
        self.start_time = time.time()
        
        df = pd.read_csv(self.input_path, usecols=['title', 'ingredients', 'directions', 'NER'])
        self.logger.log_info(f"Loaded {len(df)} recipes from {self.input_path}")
        
        recipes = []
        for idx, row in df.iterrows():
            try:
                ingredient_quantities = parse_ingredient_quantities(row['ingredients'])
                ner_ingredients = eval(row['NER']) if isinstance(row['NER'], str) else row['NER']
                servings = estimate_servings(ingredient_quantities, ner_ingredients)
                recipe = Recipe(
                    id=str(idx),
                    title=row['title'],
                    ingredients=ner_ingredients,
                    instructions=' '.join(eval(row['directions']) if isinstance(row['directions'], str) else row['directions']),
                    prep_time=None,
                    cook_time=None,
                    servings=servings,
                    category=None,
                    recipe_type=None,
                    nutrition_info=None
                )
                if not validate_recipe(recipe):
                    recipe.nutrition_info = {'ingredient_quantities': ingredient_quantities}
                    recipes.append(recipe)
                else:
                    self.logger.log_error("Validation error", f"Invalid recipe {idx}", str(idx))
            except Exception as e:
                self.logger.log_error("Parsing error", f"Failed to parse recipe {idx}: {e}", str(idx))

        recipes, classification_stats = self.classifier.filter_savory_recipes(recipes)
        self.logger.log_info(f"Classified {classification_stats.savory_recipes} savory recipes")

        recipes, filter_stats = self.allergen_filter.filter_recipes(recipes)
        self.logger.log_info(f"Retained {filter_stats.retained_recipes} allergen-free recipes")

        output_df = pd.DataFrame([
            {
                'id': r.id,
                'title': r.title,
                'NER': r.ingredients,
                'instructions': r.instructions,
                'recipe_type': r.recipe_type.meal_category if r.recipe_type else 'unknown',
                'high_protein': r.nutrition_info.get('high_protein', False) if r.nutrition_info else False,
                'servings': r.servings,
                'ingredient_quantities': r.nutrition_info.get('ingredient_quantities', {}) if r.nutrition_info else {}
            } for r in recipes
        ])
        output_df.to_csv(self.output_path, index=False)
        self.logger.log_info(f"Saved {len(recipes)} recipes to {self.output_path}")

        return ProcessingResult(
            processed_recipes=recipes,
            filter_stats=filter_stats,
            classification_stats=classification_stats
        )

    def generate_report(self) -> ProcessingReport:
        """Generate processing report."""
        result = self.process_dataset()
        return ProcessingReport(
            total_recipes=result.classification_stats.total_recipes,
            processed_recipes=len(result.processed_recipes),
            processing_time=time.time() - self.start_time,
            filter_stats=result.filter_stats,
            classification_stats=result.classification_stats
        )

if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_dataset()