import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import logging
import time

@dataclass
class RecipeType:
    """Classification information for a recipe"""
    is_savory: bool
    is_sweet: bool
    meal_category: str  # 'main_dish', 'soup', 'stew', 'side_dish', 'dessert', etc.
    confidence_score: float  # 0.0 to 1.0


@dataclass
class Recipe:
    """Core recipe data model"""
    id: str
    title: str
    ingredients: List[str]
    instructions: str
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    category: Optional[str] = None
    recipe_type: Optional[RecipeType] = None
    nutrition_info: Optional[Dict[str, Any]] = None


@dataclass
class FilterStats:
    """Statistics for allergen filtering operations"""
    total_recipes: int
    filtered_recipes: int
    retained_recipes: int
    allergen_breakdown: Dict[str, int]
    processing_time: float


@dataclass
class ClassificationStats:
    """Statistics for recipe classification operations"""
    total_recipes: int
    savory_recipes: int
    sweet_recipes: int
    unclassified_recipes: int
    meal_category_breakdown: Dict[str, int]


@dataclass
class ProcessingResult:
    """Complete processing results"""
    processed_recipes: List[Recipe]
    filter_stats: FilterStats
    classification_stats: ClassificationStats
    success: bool
    error_message: Optional[str] = None


class RecipeClassifier:
    """Classifies recipes as savory/sweet and determines meal categories"""
    
    def __init__(self):
        self.sweet_keywords = [
            'sugar', 'honey', 'syrup', 'chocolate', 'vanilla', 'cinnamon', 'cake', 'cookie',
            'dessert', 'frosting', 'icing', 'candy', 'caramel', 'marshmallow', 'pie crust',
            'powdered sugar', 'brown sugar', 'maple syrup', 'cocoa', 'sweet', 'baking powder',
            'confectioner', 'molasses', 'jam', 'jelly', 'fruit preserve', 'custard', 'pudding'
        ]
        
        self.savory_keywords = [
            'salt', 'pepper', 'garlic', 'onion', 'herbs', 'spices', 'broth', 'stock',
            'meat', 'chicken', 'beef', 'pork', 'vegetables', 'beans', 'lentils',
            'soup', 'stew', 'casserole', 'sauce', 'savory', 'main dish', 'oregano',
            'thyme', 'rosemary', 'basil', 'paprika', 'cumin', 'chili', 'vinegar'
        ]
        
        self.meal_categories = {
            'main_dish': ['main', 'entree', 'dinner', 'lunch', 'casserole', 'pasta', 'rice'],
            'soup': ['soup', 'broth', 'bisque', 'chowder', 'gazpacho'],
            'stew': ['stew', 'curry', 'chili', 'ragout', 'goulash'],
            'side_dish': ['side', 'vegetable', 'salad', 'bread', 'roll'],
            'dessert': ['dessert', 'cake', 'pie', 'cookie', 'sweet', 'pudding', 'ice cream']
        }
    
    def classify_recipe_type(self, recipe: Recipe) -> RecipeType:
        """Classify a recipe as savory/sweet and determine meal category"""
        # Combine title and ingredients for analysis
        text_to_analyze = f"{recipe.title.lower()} {' '.join(recipe.ingredients).lower()}"
        
        # Count sweet and savory indicators
        sweet_score = sum(1 for keyword in self.sweet_keywords if keyword in text_to_analyze)
        savory_score = sum(1 for keyword in self.savory_keywords if keyword in text_to_analyze)
        
        # Determine if recipe is sweet or savory
        is_sweet = sweet_score > savory_score
        is_savory = savory_score > sweet_score or (sweet_score == 0 and savory_score == 0)
        
        # Calculate confidence score
        total_indicators = sweet_score + savory_score
        if total_indicators == 0:
            confidence_score = 0.5  # Neutral confidence for unclassified
        else:
            max_score = max(sweet_score, savory_score)
            confidence_score = max_score / total_indicators
        
        # Determine meal category
        meal_category = self._determine_meal_category(text_to_analyze)
        
        return RecipeType(
            is_savory=is_savory,
            is_sweet=is_sweet,
            meal_category=meal_category,
            confidence_score=confidence_score
        )
    
    def _determine_meal_category(self, text: str) -> str:
        """Determine the meal category based on keywords"""
        category_scores = {}
        
        for category, keywords in self.meal_categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return 'unclassified'
        
        # Return category with highest score
        return max(category_scores, key=category_scores.get)
    
    def is_meal_appropriate(self, recipe: Recipe) -> bool:
        """Check if recipe is appropriate for food bank meals (savory, not dessert)"""
        recipe_type = self.classify_recipe_type(recipe)
        return recipe_type.is_savory and recipe_type.meal_category != 'dessert'
    
    def filter_savory_recipes(self, recipes: List[Recipe]) -> Tuple[List[Recipe], ClassificationStats]:
        """Filter recipes to keep only savory, meal-appropriate ones"""
        savory_recipes = []
        sweet_count = 0
        savory_count = 0
        unclassified_count = 0
        meal_category_breakdown = {}
        
        for recipe in recipes:
            recipe_type = self.classify_recipe_type(recipe)
            recipe.recipe_type = recipe_type  # Store classification in recipe
            
            # Count classifications
            if recipe_type.is_sweet:
                sweet_count += 1
            elif recipe_type.is_savory:
                savory_count += 1
            else:
                unclassified_count += 1
            
            # Count meal categories
            category = recipe_type.meal_category
            meal_category_breakdown[category] = meal_category_breakdown.get(category, 0) + 1
            
            # Keep only meal-appropriate recipes
            if self.is_meal_appropriate(recipe):
                savory_recipes.append(recipe)
        
        stats = ClassificationStats(
            total_recipes=len(recipes),
            savory_recipes=savory_count,
            sweet_recipes=sweet_count,
            unclassified_recipes=unclassified_count,
            meal_category_breakdown=meal_category_breakdown
        )
        
        return savory_recipes, stats


class AllergenFilter:
    """Filters recipes containing the seven major allergens"""
    
    def __init__(self):
        self.allergen_keywords = {
            'peanuts': [
                'peanut', 'peanuts', 'groundnut', 'arachis oil', 'peanut oil',
                'peanut butter', 'peanut flour', 'goober', 'monkey nut'
            ],
            'tree_nuts': [
                'almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut',
                'macadamia', 'brazil nut', 'pine nut', 'chestnut', 'beechnut',
                'hickory nut', 'almond oil', 'walnut oil', 'nut butter', 'marzipan',
                'praline', 'nougat', 'gianduja', 'nut meal', 'nut flour'
            ],
            'milk': [
                'milk', 'dairy', 'cheese', 'butter', 'cream', 'yogurt', 'whey',
                'casein', 'lactose', 'buttermilk', 'sour cream', 'heavy cream',
                'half and half', 'condensed milk', 'evaporated milk', 'powdered milk',
                'milk powder', 'cottage cheese', 'ricotta', 'mozzarella', 'cheddar',
                'parmesan', 'swiss cheese', 'cream cheese', 'ice cream', 'sherbet',
                'custard', 'pudding', 'ghee', 'clarified butter'
            ],
            'eggs': [
                'egg', 'eggs', 'albumin', 'mayonnaise', 'meringue', 'egg white',
                'egg yolk', 'whole egg', 'egg powder', 'dried egg', 'egg substitute',
                'lecithin', 'lysozyme', 'ovalbumin', 'ovomucin', 'vitellin'
            ],
            'fish': [
                'fish', 'salmon', 'tuna', 'cod', 'anchovy', 'sardine', 'mackerel',
                'halibut', 'flounder', 'sole', 'bass', 'trout', 'catfish', 'tilapia',
                'fish sauce', 'fish oil', 'worcestershire sauce', 'caesar dressing',
                'fish stock', 'dashi', 'surimi', 'caviar', 'roe'
            ],
            'shellfish': [
                'shrimp', 'crab', 'lobster', 'clam', 'oyster', 'mussel', 'scallop',
                'crawfish', 'crayfish', 'prawns', 'langostino', 'barnacle',
                'sea urchin', 'abalone', 'cockle', 'periwinkle', 'whelk',
                'shellfish extract', 'crab extract', 'lobster extract'
            ],
            'soybeans': [
                'soy', 'soya', 'tofu', 'tempeh', 'miso', 'edamame', 'soy sauce',
                'soybean', 'soy protein', 'soy flour', 'soy milk', 'soy oil',
                'textured soy protein', 'hydrolyzed soy protein', 'soy lecithin',
                'tamari', 'shoyu', 'natto', 'yuba', 'soy cheese', 'soy yogurt'
            ],
            'wheat': [
                'wheat', 'flour', 'bread', 'pasta', 'gluten', 'semolina', 'bulgur',
                'couscous', 'wheat flour', 'whole wheat', 'wheat bran', 'wheat germ',
                'durum', 'spelt', 'kamut', 'farro', 'einkorn', 'emmer', 'triticale',
                'seitan', 'vital wheat gluten', 'wheat starch', 'wheat protein',
                'graham flour', 'self-rising flour', 'all-purpose flour',
                'bread flour', 'cake flour', 'pastry flour', 'cracker', 'cookie',
                'biscuit', 'muffin', 'pancake', 'waffle', 'cereal', 'oats', 'barley', 'rye'
            ]
        }
    
    def contains_allergens(self, ingredients: List[str]) -> Tuple[bool, List[str]]:
        """Check if ingredients contain any allergens and return which ones"""
        found_allergens = []
        
        # Convert all ingredients to lowercase for case-insensitive matching
        ingredients_text = ' '.join(ingredients).lower()
        
        for allergen_type, keywords in self.allergen_keywords.items():
            for keyword in keywords:
                if keyword in ingredients_text:
                    found_allergens.append(allergen_type)
                    break  # Found this allergen type, move to next
        
        return len(found_allergens) > 0, found_allergens
    
    def filter_recipes(self, recipes: List[Recipe]) -> Tuple[List[Recipe], FilterStats]:
        """Filter out recipes containing any allergens"""
        start_time = time.time()
        safe_recipes = []
        allergen_breakdown = {allergen: 0 for allergen in self.allergen_keywords.keys()}
        total_filtered = 0
        
        for recipe in recipes:
            has_allergens, found_allergens = self.contains_allergens(recipe.ingredients)
            
            if has_allergens:
                total_filtered += 1
                # Count each allergen type found
                for allergen in found_allergens:
                    allergen_breakdown[allergen] += 1
            else:
                safe_recipes.append(recipe)
        
        processing_time = time.time() - start_time
        
        stats = FilterStats(
            total_recipes=len(recipes),
            filtered_recipes=total_filtered,
            retained_recipes=len(safe_recipes),
            allergen_breakdown=allergen_breakdown,
            processing_time=processing_time
        )
        
        return safe_recipes, stats