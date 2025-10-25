import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.model import train_model
from src.utils import load_data, validate_processed_data, ProcessingLogger

def main():
    logger = ProcessingLogger()
    processed_data_path = os.path.join(project_root, 'data', 'processed', 'processed_data.csv')
    
    # Validate data
    logger.log_info("Validating processed_data.csv before training")
    validate_processed_data(processed_data_path)
    
    # Check for errors
    error_report = logger.generate_error_report()
    if error_report.errors:
        print("Validation failed with errors:")
        for error in error_report.errors:
            print(f"- {error['type']}: {error['details']} (Recipe: {error['recipe_title']})")
        exit(1)
    
    # Load and train
    df = load_data(processed_data_path)
    if df is None:
        print("Failed to load data")
        exit(1)
    
    vectorizer, ingredient_vectors, recipes_df = train_model(df, output_model_path=os.path.join(project_root, 'models', 'model.pkl'))
    print("Model training completed")

if __name__ == "__main__":
    main()