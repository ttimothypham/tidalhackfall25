import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.utils import validate_processed_data, ProcessingLogger

def main():
    logger = ProcessingLogger()
    logger.log_info("Starting validation of processed_data.csv")
    
    # Validate processed_data.csv
    processed_data_path = os.path.join(project_root, 'data', 'processed', 'processed_data.csv')
    validate_processed_data(processed_data_path)
    
    # Generate and print error report
    error_report = logger.generate_error_report()
    print("\nValidation Report:")
    print(f"Errors: {len(error_report.errors)}")
    for error in error_report.errors:
        print(f"- {error['type']}: {error['details']} (Recipe: {error['recipe_title']})")
    print(f"Warnings: {len(error_report.warnings)}")
    for warning in error_report.warnings:
        print(f"- {warning['type']}: {warning['details']}")
    print(f"Info: {len(error_report.info)}")
    for info in error_report.info:
        print(f"- {info}")

if __name__ == "__main__":
    main()