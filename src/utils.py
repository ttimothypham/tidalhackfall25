from typing import Optional, List, Dict
from dataclasses import dataclass
import pandas as pd
import re
import logging
import os

@dataclass
class Recipe:
    title: str
    ingredients: List[str]
    instructions: List[str]
    servings: int
    recipe_type: str
    structured_ingredients: List[Dict]
    total_time_minutes: Optional[float]
    cooking_temp_f: Optional[float]
    tier: int

@dataclass
class RecipeType:
    is_savory: bool
    meal_category: str
    confidence_score: float

@dataclass
class FilterStats:
    total_recipes: int
    filtered_recipes: int
    retained_recipes: int
    allergen_breakdown: Dict[str, int]
    processing_time: float

@dataclass
class ClassificationStats:
    total_recipes: int
    savory_recipes: int
    unclassified_recipes: int
    meal_category_breakdown: Dict[str, int]

@dataclass
class ErrorReport:
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    info: List[str]

class ProcessingLogger:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, error_type: str, details: str, recipe_title: Optional[str] = None):
        self.errors.append({'type': error_type, 'details': details, 'recipe_title': recipe_title})
        logging.error(f"{error_type}: {details} (Recipe: {recipe_title})")

    def log_warning(self, warning_type: str, details: str):
        self.warnings.append({'type': warning_type, 'details': details})
        logging.warning(f"{warning_type}: {details}")

    def log_info(self, message: str):
        self.info.append(message)
        logging.info(message)

    def generate_error_report(self) -> ErrorReport:
        return ErrorReport(errors=self.errors, warnings=self.warnings, info=self.info)

def load_data(path: str, tier: int = 1) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        df = df[df['tier'] == tier].reset_index(drop=True)
        if df.empty:
            logger = ProcessingLogger()
            logger.log_error("Data Load Error", f"No tier {tier} recipes found in {path}")
        return df
    except Exception as e:
        logger = ProcessingLogger()
        logger.log_error("File I/O Error", f"Failed to load {path}: {e}")
        return None

def validate_recipe(recipe: Recipe) -> Optional[List[str]]:
    errors = []
    if not recipe.title:
        errors.append("Missing title")
    if not recipe.ingredients or len(recipe.ingredients) == 0:
        errors.append("No ingredients")
    if not recipe.instructions or all(not step for step in recipe.instructions):
        errors.append("No valid instructions")
    if recipe.servings < 2:
        errors.append(f"Invalid servings: {recipe.servings} (must be >= 2)")
    if any(allergen in ' '.join(recipe.ingredients).lower() for allergen in ['milk', 'peanuts', 'sugar']):
        errors.append("Allergens detected")
    return errors if errors else None

def parse_ingredient_quantities(ingredient_list: List[Dict]) -> Dict[str, str]:
    quantities = {}
    for ingr in ingredient_list:
        name = ingr['ingredient'].strip().lower()
        qty = ingr.get('raw_amount', 'unknown')
        unit = ingr.get('unit', '')
        quantities[name] = f"{qty} {unit}".strip() if qty != 'unknown' else 'unknown'
    return quantities

def estimate_servings(structured_ingredients: List[Dict]) -> int:
    total_units = 0
    measurable_quantities = 0
    for ingr in structured_ingredients:
        try:
            qty = ingr.get('raw_amount')
            unit = ingr.get('unit', '')
            if not qty or qty == 'unknown':
                continue
            num = float(re.sub(r'[^0-9/]', '', qty).replace('/', '.')) if '/' in qty else float(qty)
            if unit and ('cup' in unit or 'c.' in unit):
                total_units += num
                measurable_quantities += 1
            elif unit and ('tablespoon' in unit or 'tbsp.' in unit):
                total_units += num / 16
                measurable_quantities += 1
            elif unit and ('teaspoon' in unit or 'tsp.' in unit):
                total_units += num / 48
                measurable_quantities += 1
            elif unit and ('pound' in unit or 'lb.' in unit):
                total_units += num * 2
                measurable_quantities += 1
            elif unit and 'oz.' in unit:
                total_units += num / 8
                measurable_quantities += 1
        except:
            continue
    
    if measurable_quantities > 0:
        servings = max(2, int(total_units * 2))
    else:
        num_ingredients = len(structured_ingredients)
        servings = max(2, min(4, num_ingredients))
        logger = ProcessingLogger()
        logger.log_warning("Serving estimation", f"Using fallback for servings: {servings} (based on {num_ingredients} ingredients)")
    
    return servings

def classify_recipe_type(title: str, directions: List[str]) -> str:
    text = (title + ' ' + ' '.join(directions)).lower()
    if any(keyword in text for keyword in ['soup', 'stew']):
        return 'soup' if 'soup' in text else 'stew'
    elif 'casserole' in text or 'bake' in text:
        return 'casserole'
    return 'unknown'

def extract_unique_ingredients(input_path: str = os.path.join('data', 'processed', 'processed_data.csv'), 
                              output_path: str = os.path.join('data', 'processed', 'unique_ingredients.csv')) -> List[str]:
    df = load_data(input_path)
    if df is None:
        return []
    
    unique_ingredients = set()
    for ner in df['NER']:
        try:
            ingr_list = eval(ner) if isinstance(ner, str) else ner
            unique_ingredients.update(ingr.strip().lower() for ingr in ingr_list if ingr and not any(allergen in ingr.lower() for allergen in ['milk', 'peanuts', 'sugar']))
        except Exception as e:
            logger = ProcessingLogger()
            logger.log_error("Parsing error", f"Failed to parse NER: {e}")
    
    unique_ingredients = sorted(list(unique_ingredients))
    pd.DataFrame(unique_ingredients, columns=['ingredient']).to_csv(output_path, index=False)
    logger = ProcessingLogger()
    logger.log_info(f"Saved {len(unique_ingredients)} unique ingredients to {output_path}")
    
    return unique_ingredients

def validate_processed_data(input_path: str = os.path.join('data', 'processed', 'processed_data.csv')) -> None:
    df = load_data(input_path)
    if df is None:
        return
    
    for idx, row in df.iterrows():
        try:
            structured_ings = eval(row['structured_ingredients']) if isinstance(row['structured_ingredients'], str) else row['structured_ingredients']
            ner = eval(row['NER']) if isinstance(row['NER'], str) else row['NER']
            directions = eval(row['directions']) if isinstance(row['directions'], str) else row['directions']
            
            recipe = Recipe(
                title=row['title'],
                ingredients=ner,
                instructions=directions,
                servings=estimate_servings(structured_ings),
                recipe_type=classify_recipe_type(row['title'], directions),
                structured_ingredients=structured_ings,
                total_time_minutes=row['total_time_minutes'],
                cooking_temp_f=row['cooking_temp_f'],
                tier=row['tier']
            )
            errors = validate_recipe(recipe)
            if errors:
                logger = ProcessingLogger()
                logger.log_error("Validation error", f"Recipe {row['title']}: {errors}")
        except Exception as e:
            logger = ProcessingLogger()
            logger.log_error("Validation error", f"Failed to validate recipe {idx}: {e}")
    
    logger = ProcessingLogger()
    logger.log_info(f"Validated {len(df)} tier 1 recipes")