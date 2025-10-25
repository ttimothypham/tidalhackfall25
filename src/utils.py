from typing import Optional, List, Dict
from dataclasses import dataclass
import pandas as pd
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
    servings: Optional[int]
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
    return errors if errors else None

def extract_unique_ingredients(input_path: str = "data/processed/processed_data.csv", output_path: str = "data/processed/unique_ingredients.csv") -> List[str]:
    """Extract unique ingredients from processed_data.csv and save to CSV."""
    df = load_data(input_path)
    if df is None:
        return []
    
    unique_ingredients = set()
    for ingredients in df['ingredients']:
        try:
            ingr_list = eval(ingredients) if isinstance(ingredients, str) else ingredients
            unique_ingredients.update(ingr.strip().lower() for ingr in ingr_list)
        except Exception as e:
            logger = ProcessingLogger()
            logger.log_error("Parsing error", f"Failed to parse ingredients: {e}")
    
    unique_ingredients = sorted(list(unique_ingredients))
    pd.DataFrame(unique_ingredients, columns=['ingredient']).to_csv(output_path, index=False)
    logger = ProcessingLogger()
    logger.log_info(f"Saved {len(unique_ingredients)} unique ingredients to {output_path}")
    
    return unique_ingredients