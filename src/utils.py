from typing import Optional, List, Dict
from dataclasses import dataclass
import pandas as pd
import re
import logging

# Data models shared across modules
@dataclass
class Recipe:
    id: str
    title: str
    ingredients: List[str]
    instructions: str
    prep_time: Optional[int]
    cook_time: Optional[int]
    servings: int  # Non-optional
    category: Optional[str]
    recipe_type: Optional['RecipeType']
    nutrition_info: Optional[Dict[str, bool]]

@dataclass
class RecipeType:
    is_savory: bool
    is_sweet: bool
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
    sweet_recipes: int
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

    def log_error(self, error_type: str, details: str, recipe_id: Optional[str] = None):
        self.errors.append({'type': error_type, 'details': details, 'recipe_id': recipe_id})
        logging.error(f"{error_type}: {details} (Recipe ID: {recipe_id})")

    def log_warning(self, warning_type: str, details: str):
        self.warnings.append({'type': warning_type, 'details': details})
        logging.warning(f"{warning_type}: {details}")

    def log_info(self, message: str):
        self.info.append(message)
        logging.info(message)

    def generate_error_report(self) -> ErrorReport:
        return ErrorReport(errors=self.errors, warnings=self.warnings, info=self.info)

def load_data(path: str) -> pd.DataFrame:
    """Load CSV with error handling."""
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger = ProcessingLogger()
        logger.log_error("File I/O Error", f"Failed to load {path}: {e}")
        return None

def validate_recipe(recipe: Recipe) -> Optional[List[str]]:
    """Validate recipe data integrity."""
    errors = []
    if not recipe.title:
        errors.append("Missing title")
    if not recipe.ingredients or len(recipe.ingredients) == 0:
        errors.append("No ingredients")
    if not recipe.instructions:
        errors.append("No instructions")
    if recipe.servings < 2:
        errors.append(f"Invalid servings: {recipe.servings} (must be >= 2)")
    return errors if errors else None

def parse_ingredient_quantities(ingredient_list: List[str]) -> Dict[str, str]:
    """Parse quantities from ingredients (e.g., '1 c. brown sugar' -> {brown sugar: 1 cup})."""
    try:
        quantities = {}
        for ingr in ingredient_list:
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
                total_units += num * 2  # 1 pound ~ 2 cups
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
        num_ingredients = len(ingredients)
        servings = max(2, min(4, num_ingredients))  # Fallback: 2-4 servings
        logger = ProcessingLogger()
        logger.log_warning("Serving estimation", f"Using fallback for servings: {servings} (based on {num_ingredients} ingredients)")
    
    return servings

def extract_unique_ingredients(input_path: str = "data/processed/processed_data.csv", output_path: str = "data/processed/unique_ingredients.csv") -> List[str]:
    """Extract unique ingredients from NER column in processed_data.csv."""
    df = load_data(input_path)
    if df is None:
        return []
    
    unique_ingredients = set()
    for ner in df['NER']:
        try:
            ingr_list = eval(ner) if isinstance(ner, str) else ner
            unique_ingredients.update(ingr.strip().lower() for ingr in ingr_list)
        except Exception as e:
            logger = ProcessingLogger()
            logger.log_error("Parsing error", f"Failed to parse NER: {e}")
    
    unique_ingredients = sorted(list(unique_ingredients))
    pd.DataFrame(unique_ingredients, columns=['ingredient']).to_csv(output_path, index=False)
    logger = ProcessingLogger()
    logger.log_info(f"Saved {len(unique_ingredients)} unique ingredients to {output_path}")
    
    return unique_ingredients

def validate_processed_data(input_path: str = "data/processed/processed_data.csv") -> None:
    """Validate processed_data.csv and fix servings if needed."""
    df = load_data(input_path)
    if df is None:
        return
    
    for idx, row in df.iterrows():
        try:
            servings = row['servings']
            if not isinstance(servings, int) or servings < 2:
                ner_ingredients = eval(row['NER']) if isinstance(row['NER'], str) else row['NER']
                quantities = eval(row['ingredient_quantities']) if isinstance(row['ingredient_quantities'], str) else row['ingredient_quantities']
                df.at[idx, 'servings'] = estimate_servings(quantities, ner_ingredients)
                logger = ProcessingLogger()
                logger.log_warning("Serving fix", f"Fixed servings for recipe {idx}: {df.at[idx, 'servings']}")
        except Exception as e:
            logger = ProcessingLogger()
            logger.log_error("Validation error", f"Failed to validate recipe {idx}: {e}")
    
    df.to_csv(input_path, index=False)
    logger = ProcessingLogger()
    logger.log_info(f"Validated and saved {len(df)} recipes to {input_path}")